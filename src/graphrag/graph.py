from __future__ import annotations
from typing import List, Dict, Any, Tuple, DefaultDict
from collections import defaultdict
import networkx as nx
# from .extract import extract_claims
from .scorer import evidence_weight
from .open_canon import cluster_keys  # ← added
from .extract_llm_open import extract_claims_llm_open as extract_claims

def _cid(meta: Dict[str, Any]) -> str:
    return f"{(meta.get('source') or 'src')}::{(meta.get('id') or 'chunk')}"

def _claim_node(key: str, val: str) -> str:
    return f"claim::{key}={val}"

class ClaimGraph:
    def __init__(self):
        self.G = nx.DiGraph()

    def build_from_nodes(self, nodes: List[Any], *, cluster_threshold: float = 0.62):
        """For Top-N: extract claims → cluster synonymous keys → add to graph → link contradiction edges."""
        collected = []  # (raw_key, val, sent, meta, base_score)
        for n in nodes:
            meta = (n.metadata or {})
            text = getattr(n, "text", None) or getattr(getattr(n, "node", None), "text", "") or ""
            base = n.score or 0.0
            for c in (extract_claims(text) or []):
                collected.append((c["key"], c["val"], c["sent"], meta, base))
        if not collected:
            return

        # Vocabulary-free clustering: merge synonymous keys to the same representative key.
        raw_keys = [k for k, _, _, _, _ in collected]
        clusters = cluster_keys(raw_keys, threshold=cluster_threshold)
        rep_map = {}
        for _, ks in clusters.items():
            rep = min(ks, key=len)  # representative name: the shortest one
            for k in ks:
                rep_map[k] = rep

        # Insert into graph (using representative keys)
        for raw_k, val, sent, meta, base in collected:
            key = rep_map.get(raw_k, raw_k)
            evid_id = _cid(meta)
            if not self.G.has_node(evid_id):
                self.G.add_node(evid_id, type="evidence", **meta)
            c_id = _claim_node(key, val)
            if not self.G.has_node(c_id):
                self.G.add_node(c_id, type="claim", key=key, val=val)
            w = evidence_weight(meta, base)
            self.G.add_edge(evid_id, c_id, type="supports", weight=float(w), sent=sent)

        self.add_contradictions()

    def add_evidence(self, node_text: str, meta: Dict[str, Any], base_score: float):
        """Extract claims from one evidence (chunk) and link edges."""
        evid_id = _cid(meta)
        self.G.add_node(evid_id, type="evidence", **meta)

        claims = extract_claims(node_text)
        for c in claims:
            c_id = _claim_node(c["key"], c["val"])
            if not self.G.has_node(c_id):
                self.G.add_node(c_id, type="claim", key=c["key"], val=c["val"])
            w = evidence_weight(meta, base_score)
            self.G.add_edge(evid_id, c_id, type="supports", weight=float(w), sent=c["sent"])

    def add_contradictions(self):
        """For the same key with different values, link pairwise 'contradicts' edges."""
        by_key: DefaultDict[str, List[Tuple[str, str]]] = defaultdict(list)
        for n, d in self.G.nodes(data=True):
            if d.get("type") == "claim":
                by_key[d["key"]].append((n, d["val"]))
        for key, items in by_key.items():
            # val -> nodes
            val2nodes: DefaultDict[str, List[str]] = defaultdict(list)
            for nid, val in items:
                val2nodes[val].append(nid)
            vals = list(val2nodes.keys())
            if len(vals) <= 1:
                continue
            for i in range(len(vals)):
                for j in range(i + 1, len(vals)):
                    a, b = vals[i], vals[j]
                    for na in val2nodes[a]:
                        for nb in val2nodes[b]:
                            self.G.add_edge(na, nb, type="contradicts")
                            self.G.add_edge(nb, na, type="contradicts")

    def build_from_nodes(self, nodes: List[Any]):
        """nodes: a list of LlamaIndex NodeWithScore."""
        for n in nodes:
            meta = (n.metadata or {})
            text = getattr(n, "text", None) or getattr(getattr(n, "node", None), "text", "") or ""
            base = n.score or 0.0
            self.add_evidence(text, meta, base)
        self.add_contradictions()

    # ---- Adjudication & reporting ----
    def consensus_score(self, claim_id: str, lam: float = 0.7) -> float:
        """Sum of support-edge weights minus lam * (sum of support weights on the contradictory side)."""
        supp = sum(d["weight"] for _, _, d in self.G.in_edges(claim_id, data=True) if d.get("type") == "supports")
        contra = 0.0
        for _, other, d in self.G.out_edges(claim_id, data=True):
            if d.get("type") != "contradicts":
                continue
            contra += sum(dd["weight"] for _, _, dd in self.G.in_edges(other, data=True) if dd.get("type") == "supports")
        return supp - lam * contra

    def decide_by_key(self, key: str, top_k: int = 2, lam: float = 0.7):
        """Return Top-K claims (by consensus score) for this key, with brief support/contradiction summaries."""
        claims = [(n, d) for n, d in self.G.nodes(data=True) if d.get("type") == "claim" and d.get("key") == key]
        scored = [(nid, self.consensus_score(nid, lam)) for nid, _ in claims]
        scored.sort(key=lambda x: x[1], reverse=True)
        out = []
        for nid, sc in scored[:top_k]:
            d = self.G.nodes[nid]
            supports = [(e, self.G.edges[e, nid]["weight"]) for e, _, ed in self.G.in_edges(nid, data=True) if ed["type"] == "supports"]
            supports.sort(key=lambda x: x[1], reverse=True)
            # Take the top few supporting evidences
            sup_brief = [{"evidence": e, "weight": w, "source": self.G.nodes[e].get("source"), "id": self.G.nodes[e].get("id")} for e, w in supports[:5]]

            # Contradictions: find contradictory claims, then take each one's strongest supporting evidence
            contra_brief = []
            for _, other, ed in self.G.out_edges(nid, data=True):
                if ed["type"] != "contradicts": continue
                supp2 = [(e, self.G.edges[e, other]["weight"]) for e, _, dd in self.G.in_edges(other, data=True) if dd["type"] == "supports"]
                supp2.sort(key=lambda x: x[1], reverse=True)
                if supp2:
                    e, w = supp2[0]
                    contra_brief.append({"claim": other, "evidence": e, "weight": w, "source": self.G.nodes[e].get("source"), "id": self.G.nodes[e].get("id")})
            out.append({"claim_id": nid, "key": d["key"], "val": d["val"], "consensus": sc, "supports": sup_brief, "contradicts": contra_brief})
        return out
