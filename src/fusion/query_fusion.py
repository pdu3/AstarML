from typing import List
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

def build_fusion_engine(retrievers: List, per_source_top_k: int = 10, reranker=None):
    # Pure fusion, no sub-query generation → no LLM involved
    fusion = QueryFusionRetriever(
        retrievers=retrievers,
        similarity_top_k=per_source_top_k,  # Take top-K from each retriever before fusion
        num_queries=1,                      # Key: =1 so it won't trigger an LLM
        mode="relative_score",              # RRF; can switch to "relative_score"/"dist_based"
        use_async=False,
        verbose=True,
    )
    # engine = RetrieverQueryEngine.from_args(fusion)
    # return engine
    if reranker is None:
        return RetrieverQueryEngine.from_args(fusion)
    else:
        # Attach the cross-encoder as a node postprocessor
        return RetrieverQueryEngine.from_args(
            fusion,
            node_postprocessors=[reranker],
        )
