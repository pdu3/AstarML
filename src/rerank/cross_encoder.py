# src/rerank/cross_encoder.py
from typing import Optional

# Compatible import path across versions
# try:
from llama_index.core.postprocessor import SentenceTransformerRerank
# except Exception:
#     from llama_index.postprocessor import SentenceTransformerRerank

def build_reranker(
    model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    top_n: int = 10,
) -> SentenceTransformerRerank:
    """
    Cross-encoder pairwise reranker: re-score fused candidates and keep the top_n.
    """
    return SentenceTransformerRerank(
        model=model,
        top_n=top_n,
        keep_retrieval_score=True,
    )

