from typing import List, Dict, Any, Tuple
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import json
import hashlib

# ------- Global: disable LLM, use local open-source embeddings (won't trigger OpenAI) -------
Settings.llm = None
Settings.embed_model = HuggingFaceEmbedding(model_name="intfloat/e5-small-v2")  # CPU OK

# ------- Data utilities -------
def load_rows_from_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def partition_rows_by_source(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]],
                                                                   List[Dict[str, Any]],
                                                                   List[Dict[str, Any]]]:
    docs_rows, forums_rows, blogs_rows = [], [], []
    for r in rows:
        src = (r.get("source") or "").lower()
        if src == "docs":
            docs_rows.append(r)
        elif src == "forums":
            forums_rows.append(r)
        elif src == "blogs":
            blogs_rows.append(r)
        else:
            # Unknown source defaults to docs to avoid data loss
            rr = dict(r)
            rr["source"] = "docs"
            docs_rows.append(rr)
    return docs_rows, forums_rows, blogs_rows

def to_documents(rows: List[Dict[str, Any]]) -> List[Document]:
    docs = []
    for r in rows:
        meta = {"source": r.get("source", "docs")}
        if r.get("meta"):
            meta.update(r["meta"])
        # ---- Generate/fallback chunk id (stable & traceable) ----
        cid = r.get("id") or meta.get("id")
        if not cid:
            cid = hashlib.md5(r["text"].encode("utf-8")).hexdigest()[:10]
        meta["id"] = cid
        docs.append(Document(text=r["text"], metadata=meta))
    return docs

# ------- Retriever construction (vector-only) -------
def build_vector_retriever(rows: List[Dict[str, Any]], top_k: int = 30):
    docs = to_documents(rows)
    index = VectorStoreIndex.from_documents(docs, embed_model=Settings.embed_model)
    return index.as_retriever(similarity_top_k=top_k)

# ------- Lightweight weighting at recall stage (docs > forums > blogs, adjustable) -------
SOURCE_WEIGHT = {"docs": 1.0, "forums": 0.88, "blogs": 0.75}
FORUM_PRIOR   = 0.05  # Forum prior; set to 0 if undesired

def apply_source_bias(nodes: List[NodeWithScore]) -> List[NodeWithScore]:
    for n in nodes:
        src = (n.node.metadata or {}).get("source", "")
        base = n.score or 0.0
        w = SOURCE_WEIGHT.get(src, 1.0)
        bonus = FORUM_PRIOR if src == "forums" else 0.0
        n.score = base * w + bonus
    return sorted(nodes, key=lambda x: x.score or 0.0, reverse=True)

class BiasedRetriever:
    """Apply source weighting on top of the base vector retriever; only a light bias at the recall stage."""
    def __init__(self, base_retriever):
        self.base = base_retriever
    def retrieve(self, query: str) -> List[NodeWithScore]:
        return apply_source_bias(self.base.retrieve(query))
