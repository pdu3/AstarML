# main.py  —— unify to step 3 of "pure vector + simple RRF fusion"
import argparse
import sys
from pathlib import Path
from datetime import datetime
import os
# Make "src" importable
sys.path.append(str(Path(__file__).parent / "src"))

from src.pipelines.chunk_runner import run_chunk
from src.fusion.utils import (
    load_rows_from_jsonl,
    partition_rows_by_source,
)
from src.fusion.build_retrievers import build_all_retrievers
from src.fusion.query_fusion import build_fusion_engine
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor.types import BaseNodePostprocessor
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def run_graphrag_on_response(response_obj, topn: int = 10, query: str =""):
    """Pass the ask() response object in, run GraphRAG contradiction check on top-N results, and print."""
    from src.graphrag.graph import ClaimGraph
    G = ClaimGraph()

    top_nodes = (getattr(response_obj, "source_nodes", None) or [])[:topn]
    if not top_nodes:
        print("[GraphRAG] no nodes to build graph on")
        return

    G.build_from_nodes(top_nodes)
    q = (query or "").lower()
    # List the keys you care about (add/remove as needed)
    keys = []
    if any(k in q for k in ["concurrency", "parallel", "workers"]):
        keys.append("param.concurrency")
    if any(k in q for k in ["batch", "batch_size"]):
        keys.append("param.batch_size")
    if any(k in q for k in ["timeout", "latency"]):
        keys.append("param.timeout")
    if any(k in q for k in ["retry", "retries", "backoff"]):
        keys.append("param.retries")
    if any(k in q for k in ["patience", "early stopping"]):
        keys.append("param.early_stopping.patience")
    if any(k in q for k in ["scheduler", "cosine", "step"]):
        keys.append("param.lr_scheduler")
    if any(k in q for k in ["retention", "artifact"]):
        keys.append("param.artifact_retention_days")
    if any(k in q for k in ["granularity", "metrics"]):
        keys.append("param.metrics.granularity")
    keys = list(dict.fromkeys(keys))  # deduplicate
    if not keys:
        print("[GraphRAG] no relevant keys inferred from query; skip")
        return

    print("\n=== CONTRADICTION CHECK IF ANY (GraphRAG) ===")
    found_any = False
    for k in keys:
        decisions = G.decide_by_key(k, top_k=2, lam=0.7)
        if not decisions:
            continue
        found_any = True
        print(f"\nKey: {k}")
        for d in decisions:
            print(f"  - claim: {d['key']}={d['val']}  consensus={d['consensus']:.4f}")
            for s in d["supports"][:2]:
                print(f"      support: {s['source']}:{s['id']}  w={s['weight']:.3f}")
            for c in d["contradicts"][:2]:
                print(f"      contradict: {c['source']}:{c['id']}  w={c['weight']:.3f}  via {c['claim']}")
    if not found_any:
        print("[GraphRAG] no target keys found in top results")

def require_openai_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set. Run: export OPENAI_API_KEY=sk-xxxx")
    return key
def ask(engine, query: str, *, graph: bool = False, graph_topn: int = 10, log_txt: str=None, flags:dict=None):
    # === Your original query & printing ===
    flags = flags or {}
    # resp = engine.query(query)
    try:
        resp = engine.query(query)
    except ValueError as e:
        if "available context size" in str(e):
            print("[WARN] answer synthesis overflow; falling back to no_text")
            from llama_index.core.query_engine import RetrieverQueryEngine
            retriever = engine._retriever
            post = list(engine._node_postprocessors or [])
            engine2 = RetrieverQueryEngine.from_args(
                retriever, node_postprocessors=post, response_mode="no_text"
            )
            resp = engine2.query(query)
        else:
            raise
    used_sources = []
    for sn in resp.source_nodes:
        src = (sn.metadata or {}).get("source")
        if src:
            used_sources.append(src)
    print("[LOG] Sources used:", sorted(set(used_sources)))

    print("\n=== ANSWER ===")
    print(resp.response)

    print("\n=== CITED CHUNKS (top few) ===")
    for i, sn in enumerate(resp.source_nodes[:10], 1):
        meta = sn.metadata or {}
        score = sn.score if sn.score is not None else 0.0
        print(f"[{i}] source={meta.get('source')} id={meta.get('id')} score={score:.4f}")

    # === Only do GraphRAG contradiction check when needed (based on resp) ===
    if graph:
        run_graphrag_on_response(resp, topn=graph_topn, query=query)
        # === Structured logging (persist to disk) ===

    if flags.get("log_txt"):  # We'll insert args.log_txt into flags at the call site
        used_sources = []
        chunks_strs = []
        for sn in resp.source_nodes:
            m = sn.metadata or {}
            used_sources.append(m.get("source"))
            chunks_strs.append(f"{m.get('source')}:{m.get('id')}:{float(sn.score or 0.0):.4f}")

        line = (
            f"[{datetime.utcnow().isoformat()}Z] "
            f"q={query!r} "
            f"sources={sorted(set(s for s in used_sources if s))} "
            f"topk={len(resp.source_nodes)} "
            f"chunks={' | '.join(chunks_strs)} "
            f"flags={{rerank:{bool(flags.get('rerank'))}, graph:{bool(flags.get('graph'))}, "
            f"per_source_topk:{flags.get('per_source_topk')}}}"
        )
        write_text_log(log_txt, line)
    return resp  # Keep this if callers want to further use resp; harmless to retain

def write_text_log(path: str, line: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")
    print(f"[LOG] text log written -> {path}")

class TopK(BaseNodePostprocessor):
    def __init__(self, k:int): self.k=k
    def postprocess_nodes(self, nodes, query_bundle=None): return nodes[:self.k]

class TruncateNodeText(BaseNodePostprocessor):
    def __init__(self, max_chars:int=1200): self.max_chars=max_chars
    def postprocess_nodes(self, nodes, query_bundle=None):
        for n in nodes:
            if getattr(n, "text", None):
                n.text = n.text[:self.max_chars]
            elif getattr(getattr(n, "node", None), "text", None):
                n.node.text = n.node.text[:self.max_chars]
        return nodes

def main():
    ap = argparse.ArgumentParser(prog="astraml")
    sp = ap.add_subparsers(dest="cmd", required=True)

    # --- chunk subcommand (unchanged) ---
    sp_chunk = sp.add_parser("chunk", help="Chunk docs/forums/blogs into JSONL")
    sp_chunk.add_argument("--data-root", default=".", help="Project root containing /data")
    sp_chunk.add_argument("--out", default="artifacts/chunks.jsonl", help="Output JSONL file")
    sp_chunk.add_argument("--sources", nargs="*", default=["docs","forums","blogs"],
                          choices=["docs","forums","blogs"], help="Which sources to include")

    # --- fusion subcommand (rewritten: pure vector + simple RRF fusion; no bm25/num_queries/mode) ---
    sp_fusion = sp.add_parser("fusion", help="Query with simple multi-source vector fusion (RRF), no OpenAI/BM25")
    sp_fusion.add_argument("--chunks", default="artifacts/chunks.jsonl")
    sp_fusion.add_argument("--q", required=True)
    sp_fusion.add_argument("--model", default="intfloat/e5-small-v2")  # CPU OK
    sp_fusion.add_argument("--vec-topk", type=int, default=30, help="Per-source vector retriever top_k")
    sp_fusion.add_argument("--per-source-topk", type=int, default=10, help="K taken from each retriever before fusion")
    sp_fusion.add_argument("--final-topk", type=int, default=10, help="Final fused top_k returned")

    sp_fusion.add_argument("--rerank", action="store_true", help="Enable cross-encoder reranking")
    sp_fusion.add_argument("--rerank-model", default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    sp_fusion.add_argument("--rerank-topn", type=int, default=10)

    sp_fusion.add_argument("--graph", action="store_true", help="Build a claim-evidence graph on top-N results")
    sp_fusion.add_argument("--graph-topn", type=int, default=10, help="How many results to use when building the graph")

    sp_fusion.add_argument("--log-txt", default=None,
                           help="Append a human-readable text log for each response")

    # Append these lines after sp_fusion params:
    sp_fusion.add_argument("--answer", action="store_true",
                           help="Generate a short natural-language answer with LLM")
    sp_fusion.add_argument("--llm-model", default="gpt-4o-mini",
                           help="OpenAI model when --answer is on")
    sp_fusion.add_argument("--answer-topk", type=int, default=12,
                           help="Max nodes passed to answer synthesizer")
    sp_fusion.add_argument("--answer-maxc", type=int, default=1200,
                           help="Char cap per node before answer synthesis")

    args = ap.parse_args()

    if args.cmd == "chunk":
        n = run_chunk(args.data_root, args.out, args.sources)
        print(f"Wrote {n} chunks -> {args.out}")

    if args.cmd == "fusion":
        # Disable LLM and enable local open-source embeddings (won't trigger OpenAI)
        Settings.llm = None
        Settings.embed_model = HuggingFaceEmbedding(model_name=args.model)

        # Read and split by source
        rows = load_rows_from_jsonl(args.chunks)
        docs_rows, forums_rows, blogs_rows = partition_rows_by_source(rows)

        # Build three-way "weighted vector retrievers" (vector-only; no BM25)
        retrievers = build_all_retrievers(
            docs_rows, forums_rows, blogs_rows, top_k=args.vec_topk
        )

        # Simple RRF fusion (we define it in src/fusion/query_fusion.py)
        # engine = build_fusion_engine(
        #     retrievers,
        #     per_source_top_k=args.per_source_topk,
        # )

        # Query + logging
        # ask(engine, args.q)

        reranker = None
        if args.rerank:
            from src.rerank.cross_encoder import build_reranker
            reranker = build_reranker(model=args.rerank_model, top_n=args.rerank_topn)

        # Build the engine: just pass the reranker in
        engine = build_fusion_engine(
            retrievers,
            per_source_top_k=args.per_source_topk,
            reranker=reranker,  # ← only takes effect when --rerank is enabled
        )
        if args.answer:
            require_openai_key()
            from llama_index.llms.openai import OpenAI
            Settings.llm = OpenAI(
                model=args.llm_model,
                temperature=0,
                max_tokens=512,  # limit output length
                context_window=1200000,  # large window to avoid context underflow
                api_key=os.getenv("OPEN_API_KEY")
            )

            # Rebuild the existing engine as "compact" (reuse its retriever and existing postprocessors)
            from llama_index.core.query_engine import RetrieverQueryEngine
            retriever = engine._retriever
            post = list(engine._node_postprocessors or [])
            # Two safeguards to prevent oversized context fed to the LLM
            post.append(TopK(args.answer_topk))
            post.append(TruncateNodeText(args.answer_maxc))
            engine = RetrieverQueryEngine.from_args(
                retriever, node_postprocessors=post, response_mode="compact"
            )

        flags = {
            "rerank": bool(getattr(args, "rerank", False)),
            "rerank_model": getattr(args, "rerank_model", None) if getattr(args, "rerank", False) else None,
            "rerank_topn": getattr(args, "rerank_topn", None) if getattr(args, "rerank", False) else None,
            "graph": bool(getattr(args, "graph", False)),
            "graph_topn": getattr(args, "graph_topn", None),
            "per_source_topk": getattr(args, "per_source_topk", None),
            "log_txt": getattr(args, "log_txt", None)
        }
        ask(engine, args.q, graph=args.graph, graph_topn=args.graph_topn, log_txt=getattr(args, "log_txt", None), flags=flags)

if __name__ == "__main__":
    main()
