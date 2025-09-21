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
