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
