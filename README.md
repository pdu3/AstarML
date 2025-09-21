# AstarML
Project: AstraML Multi-Source RAG

A small, production-minded RAG system that:

Ingests three sources (docs / forums / blogs)

Applies source-specific chunking

Retrieves with per-source vector search and RRF fusion

Optionally reranks with a cross-encoder

Builds a lightweight GraphRAG layer to detect & explain contradictions

Logs sources and scores for each response

0) Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# if you’ll use OpenAI:
export OPENAI_API_KEY=sk-xxxxx
```
1) Prepare data → chunks
```kotlin
project_root/
  data/
    docs/*.md
    forums/*.md
    blogs/*.md
```
2) Query (fusion only)
```bash
python main.py fusion \
  --chunks artifacts/chunks.jsonl \
  --q "how should I tune batch size and retries for AstraML on CPU-only setups?" \
  --per-source-topk 30 \
```
3) Add reranking (+GraphRAG)
```bash
python main.py fusion \
  --chunks artifacts/chunks.jsonl \
  --q "what timeout and retry policy should I use behind corporate proxies?" \
  --per-source-topk 30 \
  --rerank --rerank-topn 12 \
  --graph --graph-topn 12 \
```
Flags you’ll care about

--per-source-topk: how many candidates per source feed into fusion (RRF).

--rerank-topn: how many fused results are re-scored by the cross-encoder.

--graph-topn: how many final results build the contradiction graph.

--log-txt: append a one-line structured log per query (sources, scores, flags).


Report

Requirement 1 — Create/source three data types

We used data/docs, data/forums, data/blogs.

Docs: long-form technical docs (MD)

Forums: short Q/A or troubleshooting threads (MD)

Blogs: narrative posts and tips (MD)

Chunking strategy

Docs: semantic-aware sliding window; larger chunks (~1200–1800 chars), small overlap (~150) to keep context.

Forums: per-post or per-accepted-answer with light normalization; chunk size smaller (~600–900 chars), overlap ≈ 0。

Blogs: paragraph-based with title carry-over; chunk size（~900–1200 chars），overlap 100。
All chunks include metadata: source, id (path#chunk_idx), created_at (if available).

Requirement 2 — Implement chunking per source

Implemented in src/pipelines/chunk_runner.py. It outputs a single chunks.jsonl, each row:
```json
{"text": "...", "metadata": {"source":"docs","id":"data/docs/retries.md#c0","created_at":"2024-05-01"}}
```
Requirement 3 — Retrieval with fusion across sources

Embeddings: intfloat/e5-small-v2 via HuggingFaceEmbedding.

Per-source retrievers: one vector retriever per source (docs/forums/blogs); 

Fusion: QueryFusionRetriever with query rewriting (--num-queries) and either RRF (--mode rrf) or relative-score fusion (--mode relative). Implemented in src/fusion/query_fusion.py.

Scoring adjustments: post-fusion rescoring applies configurable source weights (docs > forums > blogs) and forum priors (accepted, upvotes). Final score = fusion_score * w(source) + prior.

Output: top-K candidates (--k) with metadata (source, accepted, upvotes) for later reranking and logging.

Requirement 4 — Reranking

Model: Cross-Encoder cross-encoder/ms-marco-MiniLM-L-6-v2.

Process: Re-score the top-N candidates from the fusion stage (--rerank-topn).

Final ranking: Results are sorted by Cross-Encoder score in descending order

Requirement 5 — Handle contradictions

We implement a lightweight GraphRAG:

Extraction: For each top-N chunk, we LLM-extract claims = [{"key","val","sent"}] in JSON-only format;

Key clustering: open_canon.cluster_keys merges synonym keys (e.g., retention_days, artifact retention, retain artifacts) without an allowlist;

Edges: Evidence → Claim (supports, weight = evidence_weight(meta, base_score)), Claim ↔ Claim (contradicts if same canonical key but different values);

Decision: consensus = supports - λ * supports(opposing claims); print top claims per key with support & contradict evidence.

This flags batch_size 32 vs 64, concurrency 2 vs 1, artifact_retention_days 30 vs 60, etc., and shows where each side comes from.

Requirement 6 — Logging

Each query appends a line to logs/responses.txt:
```ini
[2025-09-20T01:23:45Z] q='...' sources=['docs','blogs'] topk=12 \
chunks=docs:data/docs/retries.md#c0:0.301 | blogs:data/blogs/post_09.md#c0:0.287 \
flags={rerank:True, graph:True, per_source_topk:30}
```
