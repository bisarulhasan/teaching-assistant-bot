"""Central configuration loaded from prompts.yaml and environment."""

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

# Load prompt config
CONFIG_PATH = Path(__file__).parent / "prompts.yaml"

with open(CONFIG_PATH) as f:
    PROMPT_CONFIG = yaml.safe_load(f)

# Retrieval settings
# Vector store backend: "weaviate" (local, default) or "qdrant" (hosted, 24/7).
VECTOR_DB = os.getenv("VECTOR_DB", "weaviate")

RETRIEVAL_TOP_K = 10          # Initial retrieval count
RERANK_TOP_K = 5              # After reranking, keep top 5
CHUNK_SIZE = 650              # Target tokens per chunk
CHUNK_OVERLAP = 100           # Token overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-small"
# Generation model. Default: a strong open model hosted on OpenRouter (24/7, no
# local RAM/GPU). Override with LLM_MODEL env: "qwen2.5:7b" for local Ollama, or
# another OpenRouter id like "meta-llama/llama-3.3-70b-instruct".
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen-2.5-72b-instruct")

# Evaluation thresholds (Phase 3)
FAITHFULNESS_THRESHOLD = 0.8
ANSWER_RELEVANCY_THRESHOLD = 0.75
CONTEXT_PRECISION_THRESHOLD = 0.5 # Change it to 0.7 if better model is used for evaluation


def get_system_prompt(prompt_key: str) -> str:
    """Retrieve a system prompt by key from the YAML config."""
    return PROMPT_CONFIG["system_prompts"][prompt_key]["template"]


def get_query_template(template_key: str) -> str:
    """Retrieve a query template by key from the YAML config."""
    return PROMPT_CONFIG["query_templates"][template_key]["template"]