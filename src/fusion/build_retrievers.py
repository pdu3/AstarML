from typing import Dict, Any, List
from .utils import build_vector_retriever, BiasedRetriever

def build_all_retrievers(
    docs_rows: List[Dict[str, Any]],
    forums_rows: List[Dict[str, Any]],
    blogs_rows: List[Dict[str, Any]],
    top_k: int = 30,
):
    docs_vec   = build_vector_retriever(docs_rows,   top_k=top_k)
    forums_vec = build_vector_retriever(forums_rows, top_k=top_k)
    blogs_vec  = build_vector_retriever(blogs_rows,  top_k=top_k)

    retrievers = [
        BiasedRetriever(docs_vec),
        BiasedRetriever(forums_vec),
        BiasedRetriever(blogs_vec),
    ]
    return retrievers
