# Teaching Assistant Bot 🎓

A production-grade RAG (Retrieval-Augmented Generation) system that answers student questions from course materials with verifiable citations and automated quality assurance.

## Architecture

```
PDF Documents → Chunking (500-800 tokens) → HuggingFace Embeddings → Weaviate Vector Store
                                                                            ↓
Student Question → Hybrid Retrieval (BM25 + Vector) → Cohere Reranking → LLM Generation
                                                                              ↓
                                                          Citation Verification → Answer
```

## Key Features

- **Hybrid Retrieval**: BM25 keyword search + vector semantic search with Reciprocal Rank Fusion
- **Cross-Encoder Reranking**: Cohere Rerank v3.5 for precision relevance scoring
- **Citation Enforcement**: Answers are verified against source material; unsupported claims are declined
- **CI-Gated Evaluation**: Unit tests run on every PR via GitHub Actions
- **Version-Controlled Prompts**: All system prompts stored in `prompts.yaml` with Git history
- **Fully Local Pipeline**: Runs entirely on open-source models — no paid API dependencies for generation

## Tech Stack

| Component | Technology | Details |
|-----------|-----------|---------|
| Orchestration | LangChain | Pipeline orchestration and document processing |
| Vector Store | Weaviate | Local Docker instance for vector storage |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | 22M params, ~80 MB, runs on CPU/MPS |
| Reranking | Cohere Rerank v3.5 | Cross-encoder API (free tier: 1000 calls/month) |
| Generation | Google Gemma 4 via Ollama | 8B params, ~5.5 GB, runs locally on Apple Silicon |
| Evaluation LLM | Qwen 2.5:7b via Ollama | 7B params, ~4.7 GB, fast structured output |
| Evaluation Framework | RAGAS | Faithfulness, relevancy, and precision metrics |
| CI/CD | GitHub Actions | Unit tests on every PR |

## Evaluation Results

| Metric | Score | Threshold | Status |
|--------|-------|-----------|--------|
| Faithfulness | 0.8482 | 0.80 | ✅ |
| Answer Relevancy | 0.7551 | 0.75 | ✅ |
| Context Precision | 0.8326 | 0.50 | ✅ |

## Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop (for Weaviate)
- Ollama (for local LLMs) — https://ollama.com
- A Cohere API key (free tier: https://dashboard.cohere.com/api-keys)
- **Minimum 8 GB RAM** (16 GB recommended for best model performance)

### Step 1: Clone and Install

```bash
git clone https://github.com/bisarulhasan/teaching-assistant-bot.git
cd teaching-assistant-bot
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Step 2: Pull Local Models

This project runs entirely on local open-source models via Ollama. Choose models based on your available RAM:

| Model | Role | Parameters | Download Size | RAM Needed | Minimum Hardware |
|-------|------|-----------|---------------|------------|-----------------|
| `gemma4` | RAG generation | 8B | ~5.5 GB | ~9.6 GB | 16 GB RAM |
| `gemma4:e4b` | RAG generation (lightweight) | 4B effective | ~3 GB | ~5 GB | 8 GB RAM |
| `qwen2.5:7b` | RAGAS evaluation | 7B | ~4.7 GB | ~8 GB | 16 GB RAM |
| `qwen2.5:3b` | RAGAS evaluation (lightweight) | 3B | ~2 GB | ~4 GB | 8 GB RAM |

**Recommended setup for 16GB RAM (e.g., MacBook Pro M1/M2/M3):**

```bash
ollama pull gemma4          # Best quality for answer generation
ollama pull qwen2.5:7b      # Fast structured output for evaluation
```

**For 8GB RAM machines:**

```bash
ollama pull gemma4:e4b      # Lighter generation model
ollama pull qwen2.5:3b      # Lighter evaluation model
```

Then update `src/config/settings.py` to match your chosen models.

### Step 3: Start Weaviate

```bash
docker compose up -d
```

### Step 4: Configure API Key

```bash
cp .env.example .env
```

Open `.env` and replace `your-cohere-key-here` with your actual Cohere API key.

### Step 5: Add Your PDF Textbook

The bot needs a PDF document as its knowledge base. Place it in the `data/raw/` folder and name it `textbook.pdf`:

```bash
cp ~/Downloads/your-textbook.pdf data/raw/textbook.pdf
```

**Need a free textbook?** Download any textbook from [OpenStax](https://openstax.org) — they offer free, peer-reviewed textbooks covering subjects like Physics, Biology, Chemistry, Psychology, Economics, and more. Download the PDF version, rename it to `textbook.pdf`, and place it in `data/raw/`. I Used Physics Book.

Any PDF will work — textbooks, handbooks, course notes, documentation. The system will chunk, embed, and index it automatically. For best results, use a document with 50+ pages of text content.

### Step 6: Ingest and Query

```bash
# Ingest your PDF(s) into the vector store
python -m src.pipeline ingest --fresh

# Ask a question
python -m src.pipeline "What is physics?"
```

### Step 7: Run Evaluation

```bash
# Run unit tests
pytest tests/ -v

# Run RAGAS evaluation (requires Ollama running)
python -m src.evaluation.evaluate
```

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `src/ingestion/` | PDF loading, token-aware chunking, embedding |
| `src/retrieval/` | BM25, vector search, hybrid RRF fusion, Cohere reranking |
| `src/generation/` | LLM answer generation, citation verification |
| `src/config/` | Version-controlled prompts (YAML) and settings |
| `src/evaluation/` | RAGAS evaluation pipeline |
| `src/api/` | FastAPI endpoint (chatbot interface — coming soon) |
| `data/raw/` | Source PDF documents (add your PDFs here) |
| `data/eval/` | Golden evaluation dataset |
| `tests/` | Unit tests |

## How It Works

1. **Ingestion**: PDFs are loaded, split into 500-800 token chunks with 100-token overlap, embedded using HuggingFace sentence-transformers, and stored in Weaviate.

2. **Retrieval**: User queries hit both a BM25 keyword index and vector similarity search. Results are fused using Reciprocal Rank Fusion (RRF), then reranked by Cohere's cross-encoder which evaluates each query-chunk pair jointly.

3. **Generation**: The top-5 reranked chunks are passed to Gemma 4 with a citation-enforcing system prompt. The model must cite sources for every claim.

4. **Verification**: A separate LLM call verifies whether the generated answer is actually supported by the retrieved context. If not, the system declines to answer rather than hallucinating.

5. **Evaluation**: RAGAS measures faithfulness, answer relevancy, and context precision against a curated golden dataset. CI runs unit tests on every PR.

## License

MIT
