# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-grade RAG (Retrieval Augmented Generation) teaching assistant bot with hybrid retrieval, cross-encoder reranking, citation enforcement, and CI-gated evaluation pipeline.

## Tech Stack

- **Deployed 24/7:** Next.js frontend on **Vercel** (`frontend/`) → FastAPI backend on **Render** → Qdrant Cloud + Cohere + OpenRouter. See `DEPLOY.md` and `render.yaml`. Live: https://wgs-noor.vercel.app
- **Orchestration:** LangChain
- **Vector DB:** abstracted behind `VECTOR_DB` (`qdrant` for deploy | `weaviate` local default). Qdrant store: `src/retrieval/qdrant_store.py`; client via `get_vector_client()`.
- **Embeddings:** `VECTOR_DB=qdrant` → **FastEmbed** ONNX `all-MiniLM-L6-v2` (`src/ingestion/embeddings.py`, no PyTorch, 384-dim); Weaviate path → HuggingFace MiniLM (MPS).
- **Generation:** `LLM_MODEL` routed by `src/generation/llm_client.py`: `vendor/model` → **OpenRouter** (default `qwen/qwen-2.5-72b-instruct`), `claude*` → Anthropic, else Ollama.
- **Reranking:** Cohere Rerank v3.5 (`COHERE_API_KEY`), with retry/backoff for the trial rate limit.
- **BM25:** `rank-bm25`, built in-memory at startup from the active vector store.
- **Evaluation:** `ragas` (judge via `RAGAS_JUDGE`: openrouter/openai/anthropic/ollama) + a deterministic harness (`src/evaluation/harness.py`).
- **API:** FastAPI + Uvicorn — implemented in `src/api/main.py` (`/ask`, `/catalog`, `/health`).

## Environment

```
COHERE_API_KEY=...        # reranking
OPENROUTER_API_KEY=...    # generation + RAGAS_JUDGE=openrouter
VECTOR_DB=qdrant          # or "weaviate" for local
QDRANT_URL=...            # Qdrant Cloud endpoint (when VECTOR_DB=qdrant)
QDRANT_API_KEY=...
LLM_MODEL=qwen/qwen-2.5-72b-instruct   # OpenRouter id, or "qwen2.5:7b" for local Ollama
FRONTEND_ORIGIN=https://wgs-noor.vercel.app   # backend CORS
WEAVIATE_URL=http://localhost:8080            # only for VECTOR_DB=weaviate
```

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Start Weaviate
docker compose up -d

# Ingest documents
python -m src.pipeline ingest --fresh

# Query the pipeline
python -m src.pipeline "What is Newton's second law?"

# Run tests
pytest tests/

# Run a single test
pytest tests/path/to/test_file.py::test_name

# Lint / format
ruff check src/
ruff format src/
```

## Architecture

The pipeline is orchestrated through `src/pipeline.py` with two entry points: `ingest()` and `query()`.

### Ingestion (`src/ingestion/`)

1. `loader.py` — `PyPDFLoader` reads PDFs from `data/raw/`, adds `source_file` metadata per page
2. `chunker.py` — `RecursiveCharacterTextSplitter.from_tiktoken_encoder()` with GPT-4o tokenizer; **650 tokens** target, **100 token** overlap; adds `chunk_id` (sequential) and `token_count` metadata per chunk
3. `embedder.py` — batches all chunks, embeds with HuggingFace model, stores in Weaviate collection `TeachingAssistantChunks`; `fresh=True` deletes the collection before re-ingesting

### Retrieval (`src/retrieval/`)

Multi-stage pipeline: hybrid search → Cohere reranking

- `vector_retriever.py` — dense `near_vector` search in Weaviate (top 10 candidates, `RETRIEVAL_TOP_K=10`)
- `bm25_retriever.py` — loads **all chunks from Weaviate into memory** at init to build a `BM25Okapi` index; whitespace tokenization; filters zero-score results
- `hybrid_retriever.py` — fuses dense + BM25 results via **RRF (Reciprocal Rank Fusion)** with `k=60`; de-duplicates by `chunk_id`
- `reranker.py` — passes fused results to Cohere Rerank v3.5; returns top 5 (`RERANK_TOP_K=5`) with `rerank_score` and `original_rank`

### Generation (`src/generation/`)

- `generator.py` — formats top-5 chunks using `prompts.yaml` template (chunk N, source filename, page, content), feeds into the configured LLM; returns `{"answer", "sources", "context_used"}`
- `llm_client.py` — factory (`get_chat_llm()`) that routes to `ChatOllama` or `ChatAnthropic` based on `LLM_MODEL` prefix
- `citation_checker.py` — makes a **second LLM call** to verify the answer is grounded in context; parses `is_supported` (YES/NO) and `confidence` (HIGH/MEDIUM/LOW); if unsupported, replaces the answer with a fixed decline message directing the student to ask their teacher

### Config (`src/config/`)

- `settings.py` — hardcodes retrieval/chunking params; loads `prompts.yaml`; defines RAGAS thresholds: faithfulness ≥ 0.80, answer relevancy ≥ 0.75, context precision ≥ 0.50
- `prompts.yaml` — version-controlled system prompts: `rag_answer` (basic) and `rag_answer_with_reranking` (enhanced, allows partial answers with disclaimers)

### Evaluation (`src/evaluation/`)

- `evaluate.py` — runs 10 golden Q&A pairs from `data/eval/golden_dataset.json` through the full pipeline (with `verify=False`), scores with RAGAS metrics, writes `data/eval/eval_results.json`
- CI (`.github/workflows/eval.yml`) runs `pytest tests/` on PRs to `develop`/`main`; **full RAGAS evaluation is not in CI** (requires Ollama running locally)
- Current scores: faithfulness 0.848, answer relevancy 0.755, context precision 0.833 — all passing

### Key Behaviors

- **BM25 is memory-loaded**: `bm25_retriever.py` fetches the entire corpus from Weaviate on init; for large corpora this can be slow/memory-intensive
- **Citation enforcement is two-stage**: generator is prompted to cite, then checker verifies grounding with a separate LLM call
- **Unsupported answers are suppressed**: the pipeline replaces hallucinated/ungrounded answers with a standard decline message rather than returning them
- **Weaviate collection schema**: TEXT fields `content`, `source_file`, `chunk_id`; INT fields `page`, `token_count`; no built-in vectorizer (embeddings provided externally)