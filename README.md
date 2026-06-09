# Noor — Teaching Assistant Bot 🎓

A production-grade, **deployed 24/7** RAG (Retrieval-Augmented Generation) assistant that answers students' questions **only from their own school textbooks**, with exact chapter/section/page citations and automated quality gates.

**▶ Live demo:** https://wgs-noor.vercel.app — students pick their year/subject/course and ask away.

Built for Western Grammar School across **6 textbooks, 4 subjects, Years 7–12** (Mathematics Standard & Advanced, Commerce, Investigating Science, PDHPE Stage 4 & 5).

## Architecture

```
                         Vercel (Next.js "Noor" UI)
                                   │  https
                                   ▼
                          Render (FastAPI backend)
        ┌──────────────────────────┼───────────────────────────┐
        ▼                          ▼                            ▼
  Qdrant Cloud              Cohere Rerank v3.5            OpenRouter
 (dense + payload          (cross-encoder)            (qwen-2.5-72b
  filtering) + in-                                     generation)
  memory BM25
```

Per request: **hybrid retrieval** (BM25 + dense, fused with Reciprocal Rank Fusion) → **Cohere cross-encoder reranking** → **OpenRouter generation** → **citation verification** (declines if ungrounded).

Ingestion: `pdftotext` extraction → publisher-aware cleaning → token-aware chunking → **FastEmbed (ONNX MiniLM)** embeddings → Qdrant, tagged with year/subject/course + chapter/section for filtered retrieval and citations.

## Key Features

- **Hybrid retrieval** — BM25 + dense vector search fused with **Reciprocal Rank Fusion**, then **Cohere v3.5 cross-encoder** reranking.
- **Per-student scoping** — every chunk carries year/subject/course metadata; retrieval is filtered so a Year 11 Standard student never sees Year 12 Science content (isolation verified).
- **Citation enforcement** — a second-pass grounding check declines to answer when the textbook doesn't support it, instead of hallucinating.
- **Heterogeneous ingestion** — 6 books from 3 publishers (different layouts, multi-year books, no-course subjects, per-chapter folders), with publisher-aware boilerplate cleaning.
- **Dual evaluation** — a **RAGAS** pipeline (configurable judge) **and** a fast deterministic harness (page-hit, citation precision, fact coverage).
- **CI/CD** — feature → develop → main gitflow with GitHub Actions running the test suite on every PR.
- **Hosted 24/7** — Vercel + Render + Qdrant Cloud + OpenRouter; no always-on laptop required.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js (App Router) + Tailwind v4 + KaTeX, on **Vercel** |
| Backend | FastAPI + Uvicorn, on **Render** |
| Vector store | **Qdrant Cloud** (dense + payload-indexed filtering) |
| Keyword search | `rank-bm25` (in-memory, built from Qdrant at startup) |
| Embeddings | **FastEmbed** ONNX `all-MiniLM-L6-v2` (384-dim, no PyTorch) |
| Reranking | **Cohere Rerank v3.5** (cross-encoder) |
| Generation | **OpenRouter** (`qwen/qwen-2.5-72b-instruct` by default; configurable) |
| Orchestration | LangChain |
| Evaluation | RAGAS + a custom deterministic harness |
| CI/CD | GitHub Actions |

> The vector store is abstracted behind a `VECTOR_DB` switch (`qdrant` | `weaviate`) and generation behind a model factory (OpenRouter / Ollama / Anthropic), so the same code runs hosted **or** fully local.

## Evaluation Results

On a 13-question golden set spanning all 6 books (judge = `gpt-4o-mini` via OpenRouter, scoring the deployed model):

| Metric | Score | Threshold |
|--------|-------|-----------|
| RAGAS Faithfulness | **0.94** | 0.80 ✅ |
| RAGAS Context Precision | **0.98** | 0.50 ✅ |
| RAGAS Answer Relevancy | **0.85** | 0.75 ✅ |
| Retrieval page-hit (harness) | **1.00** | — |
| Answer fact-coverage (harness) | **1.00** | — |

## Deployment (24/7)

Frontend on Vercel, backend on Render, data in Qdrant Cloud, generation via OpenRouter — see **[`DEPLOY.md`](DEPLOY.md)**. Backend env vars: `VECTOR_DB=qdrant`, `LLM_MODEL`, `QDRANT_URL`, `QDRANT_API_KEY`, `OPENROUTER_API_KEY`, `COHERE_API_KEY`, `FRONTEND_ORIGIN`. Render config lives in [`render.yaml`](render.yaml); slim runtime deps in [`requirements-deploy.txt`](requirements-deploy.txt).

## Local Development

```bash
git clone https://github.com/bisarulhasan/teaching-assistant-bot.git
cd teaching-assistant-bot
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # add COHERE_API_KEY, OPENROUTER_API_KEY, (QDRANT_URL/KEY for cloud)

# Ingest the books into Qdrant (cloud, or in-memory if QDRANT_URL unset)
VECTOR_DB=qdrant python -m src.ingestion.qdrant_ingest

# Run the API
VECTOR_DB=qdrant uvicorn src.api.main:app --reload

# Evaluate
pytest tests/ -v
python -m src.evaluation.harness --retrieval-only        # fast, no LLM
RAGAS_JUDGE=openrouter python -m src.evaluation.evaluate  # full RAGAS
```

Frontend: see [`frontend/README.md`](frontend/README.md).

## Adding more books

Drop PDFs into `data/raw/` named `"<year> <Subject> <Course> textbook.pdf"` (multi-year `7:8`, multi-word subjects, and per-chapter folders are all supported), then re-run the ingest. The picker and filtering update automatically from the corpus.

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `src/ingestion/` | PDF loading, cleaning, chunking, FastEmbed embeddings, Qdrant/Weaviate ingest |
| `src/retrieval/` | BM25, dense search, RRF fusion, Cohere reranking, Qdrant store |
| `src/generation/` | Answer generation, model factory (OpenRouter/Ollama/Anthropic), citation verification |
| `src/api/` | FastAPI server (`/ask`, `/catalog`, `/health`) |
| `src/evaluation/` | RAGAS pipeline + deterministic harness |
| `src/config/` | Version-controlled prompts (YAML) and settings |
| `frontend/` | Next.js "Noor" UI |
| `data/eval/` | Golden evaluation dataset |
| `tests/` | Unit tests (run in CI) |

## License

MIT
