# Teaching Assistant Bot 🎓

A production-grade RAG (Retrieval-Augmented Generation) system that answers student questions from course materials with verifiable citations and automated quality assurance.

## Architecture

PDF Documents → Chunking (500-800 tokens) → HuggingFace Embeddings → Weaviate Vector Store
↓
Student Question → Hybrid Retrieval (BM25 + Vector) → Cohere Reranking → LLM Generation
↓
Citation Verification → Answer

## Key Features

- **Hybrid Retrieval**: BM25 keyword search + vector semantic search with Reciprocal Rank Fusion
- **Cross-Encoder Reranking**: Cohere Rerank v3.5 for precision relevance scoring
- **Citation Enforcement**: Answers are verified against source material; unsupported claims are declined
- **CI-Gated Evaluation**: RAGAS evaluation runs on every PR; quality regression fails the build
- **Version-Controlled Prompts**: All system prompts stored in `prompts.yaml` with Git history
- **Fully Local Pipeline**: Runs entirely on open-source models — no paid API dependencies

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Orchestration | LangChain |
| Vector Store | Weaviate |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (local) |
| Reranking | Cohere Rerank v3.5 |
| Generation | Google Gemma 4 via Ollama (local) |
| Evaluation LLM | Qwen 2.5:7b via Ollama (local) |
| Evaluation Framework | RAGAS |
| CI/CD | GitHub Actions |

## Evaluation Results

| Metric | Score | Threshold | Status |
|--------|-------|-----------|--------|
| Faithfulness | 0.8482 | 0.80 | ✅ |
| Answer Relevancy | 0.7551 | 0.75 | ✅ |
| Context Precision | 0.8326 | 0.50 | ✅ |

## Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop
- Ollama

### Setup
```bash
# Clone and install
git clone https://github.com/bisarulhasan/teaching-assistant-bot.git
cd teaching-assistant-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Pull local models
ollama pull gemma4
ollama pull qwen2.5:7b

# Start Weaviate
docker compose up -d

# Configure API keys
cp .env.example .env  # Then add your Cohere API key
```

### Usage
```bash
# Ingest documents
python -m src.pipeline ingest --fresh

# Ask a question
python -m src.pipeline "What is the main topic of chapter 1?"

# Run evaluation
python -m src.evaluation.evaluate

# Run tests
pytest tests/ -v
```

## Project Structure

src/
├── ingestion/      # PDF loading, token-aware chunking, embedding
├── retrieval/      # BM25, vector search, hybrid RRF fusion, Cohere reranking
├── generation/     # LLM answer generation, citation verification
├── config/         # Version-controlled prompts (YAML) and settings
├── evaluation/     # RAGAS evaluation pipeline
└── api/            # FastAPI endpoint (chatbot interface — coming soon)

## How It Works

1. **Ingestion**: PDFs are loaded, split into 500-800 token chunks with 100-token overlap, embedded using HuggingFace sentence-transformers, and stored in Weaviate.

2. **Retrieval**: User queries hit both a BM25 keyword index and vector similarity search. Results are fused using Reciprocal Rank Fusion (RRF), then reranked by Cohere's cross-encoder which evaluates each query-chunk pair jointly.

3. **Generation**: The top-5 reranked chunks are passed to Gemma 4 with a citation-enforcing system prompt. The model must cite sources for every claim.

4. **Verification**: A separate LLM call verifies whether the generated answer is actually supported by the retrieved context. If not, the system declines to answer rather than hallucinating.

5. **Evaluation**: RAGAS measures faithfulness, answer relevancy, and context precision against a curated golden dataset. CI runs this on every PR.

## License

MIT