# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-grade RAG (Retrieval Augmented Generation) teaching assistant bot with hybrid retrieval, cross-encoder reranking, citation enforcement, and CI-gated evaluation pipeline.

## Tech Stack

- **Orchestration:** LangChain (`langchain`, `langchain-community`, `langchain-openai`, `langchain-cohere`, `langchain-weaviate`)
- **LLM/Embeddings:** OpenAI (via `OPENAI_API_KEY` / `langchain-openai`)
- **Reranking:** Cohere cross-encoder (via `COHERE_API_KEY`)
- **Vector DB:** Weaviate (via `WEAVIATE_URL`, default `http://localhost:8080`)
- **BM25:** `rank-bm25` for sparse retrieval
- **Evaluation:** `ragas` + `datasets`
- **API:** FastAPI + Uvicorn

## Architecture

The system follows a RAG pipeline orchestrated through `src/pipeline.py`:

1. **Ingestion** (`src/ingestion/`) — `loader.py` reads PDFs from `data/raw/`, `chunker.py` splits them, `embedder.py` stores embeddings in Weaviate; processed artifacts go to `data/processed/`
2. **Retrieval** (`src/retrieval/`) — `vector_retriever.py` runs hybrid search (dense + BM25) against Weaviate, followed by Cohere cross-encoder reranking
3. **Generation** (`src/generation/`) — `generator.py` constructs prompts with retrieved context and enforces citations in responses
4. **Config** (`src/config/`) — `settings.py` loads env vars via pydantic-settings; `prompts.yaml` holds prompt templates
5. **Evaluation** (`src/evaluation/`) — Offline RAGAS metrics against golden datasets in `data/eval/`; CI blocks on regression
6. **API** (`src/api/`) — FastAPI service over the pipeline

## Environment

```
OPENAI_API_KEY=...
COHERE_API_KEY=...
WEAVIATE_URL=http://localhost:8080
```

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Start Weaviate
docker compose up -d

# Run pipeline
python -m src.pipeline ingest --fresh

# Run tests
pytest tests/

# Run a single test
pytest tests/path/to/test_file.py::test_name

# Lint / format
ruff check src/
ruff format src/
```
