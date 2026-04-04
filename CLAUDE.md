# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-grade RAG (Retrieval Augmented Generation) teaching assistant bot with hybrid retrieval, cross-encoder reranking, citation enforcement, and CI-gated evaluation pipeline.

## Tech Stack

- **Language:** Python
- **LLM:** Anthropic Claude (via `ANTHROPIC_API_KEY`)
- **Reranking:** Cohere cross-encoder (via `COHERE_API_KEY`)
- **Vector DB:** Weaviate (default: `http://localhost:8080` via `WEAVIATE_URL`)

## Repository Structure

```
src/
├── api/          # API endpoints
├── config/       # Configuration and environment management
├── evaluation/   # CI-gated evaluation pipeline and metrics
├── generation/   # LLM generation with citation enforcement
├── ingestion/    # Document ingestion pipeline
└── retrieval/    # Hybrid retrieval (vector + keyword) and reranking

data/
├── raw/          # Source documents (PDFs, etc.)
├── processed/    # Chunked and embedded documents
└── eval/         # Golden evaluation datasets

tests/            # Test suite
scripts/          # Utility scripts
```

## Architecture

The system follows a RAG pipeline:

1. **Ingestion** (`src/ingestion/`) — Load and chunk source documents from `data/raw/`, store embeddings in Weaviate, write processed artifacts to `data/processed/`
2. **Retrieval** (`src/retrieval/`) — Hybrid search (dense vector + sparse/BM25) against Weaviate, followed by Cohere cross-encoder reranking
3. **Generation** (`src/generation/`) — Prompt construction with retrieved context, Claude-based response generation with enforced citations
4. **Evaluation** (`src/evaluation/`) — Offline metrics against golden datasets in `data/eval/`; CI blocks on regression
5. **API** (`src/api/`) — Serves the pipeline as an HTTP service

## Environment

Copy `.env` and fill in credentials:
```
ANTHROPIC_API_KEY=...
COHERE_API_KEY=...
WEAVIATE_URL=http://localhost:8080
```

## Commands

> Commands will be added here as the project is built out. Expected patterns for a Python project:

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run a single test
pytest tests/path/to/test_file.py::test_name

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/
```
