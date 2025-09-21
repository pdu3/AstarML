# eval_quick.py  —— no latency version
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]  # project_root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json, math
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.fusion.utils import load_rows_from_jsonl, partition_rows_by_source
from src.fusion.build_retrievers import build_all_retrievers
from src.fusion.query_fusion import build_fusion_engine


def hits1(ranked_ids, gold):
    return 1.0 if ranked_ids and ranked_ids[0] in gold else 0.0

def recall_at5(ranked_ids, gold):
    top5 = set(ranked_ids[:5])
    return 1.0 if top5 & gold else 0.0

def run_once(chunks_path, q, per_source_topk, use_rerank, rerank_topn=12):
    from llama_index.core.query_engine import RetrieverQueryEngine  # ← 新增

    # 初始化（与 main.py 一致）
    Settings.llm = None
    Settings.embed_model = HuggingFaceEmbedding(model_name="intfloat/e5-small-v2")

    rows = load_rows_from_jsonl(chunks_path)
    d, f, b = partition_rows_by_source(rows)
    retrievers = build_all_retrievers(d, f, b, top_k=30)  # vec-topk 固定30

    reranker = None
    if use_rerank:
        from src.rerank.cross_encoder import build_reranker
        reranker = build_reranker(top_n=rerank_topn)

    base_engine = build_fusion_engine(
        retrievers, per_source_top_k=per_source_topk, reranker=reranker
    )

    engine = RetrieverQueryEngine.from_args(
        base_engine._retriever,
        node_postprocessors=list(base_engine._node_postprocessors or []),
        response_mode="no_text",
    )

    resp = engine.query(q)
    ranked_ids = [(sn.metadata or {}).get("id") for sn in resp.source_nodes]
    return ranked_ids

def evaluate(chunks_path, queries_path, configs):
    qs = [json.loads(l) for l in Path(queries_path).read_text(encoding="utf-8").splitlines()]
    rows = []
    for cfg in configs:
        h1, r5 = [], []
        for ex in qs:
            ranked = run_once(
                chunks_path,
                ex["q"],
                cfg["per_source_topk"],
                cfg["rerank"],
                cfg.get("rerank_topn", 12),
            )
            gold = set(ex["relevant_ids"])
            h1.append(hits1(ranked, gold))
            r5.append(recall_at5(ranked, gold))
        rows.append({
            "name": cfg["name"],
            "per_source_topk": cfg["per_source_topk"],
            "rerank": cfg["rerank"],
            "rerank_topn": cfg.get("rerank_topn", 12),
            "Hits@1": sum(h1) / len(h1),
            "Recall@5": sum(r5) / len(r5),
        })
    return rows

if __name__ == "__main__":
    cfgs = [
        {"name": "A_base_k20",     "per_source_topk": 20, "rerank": False},
        {"name": "A_base_k30",     "per_source_topk": 30, "rerank": False},
        {"name": "B_ce_k20_t12",   "per_source_topk": 20, "rerank": True,  "rerank_topn": 12},
        {"name": "B_ce_k30_t12",   "per_source_topk": 30, "rerank": True,  "rerank_topn": 12},
    ]
    out = evaluate("artifacts/chunks.jsonl", "eval/queries.jsonl", cfgs)
    print("\n=== Quick Eval (Hits@1 / Recall@5) ===")
    for r in out:
        print(f"{r['name']:>12} | topk={r['per_source_topk']:>2} "
              f"| rerank={'Y' if r['rerank'] else 'N'} "
              f"| Hits@1={r['Hits@1']:.2f} | R@5={r['Recall@5']:.2f}")
