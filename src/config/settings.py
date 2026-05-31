"""Central configuration loaded from prompts.yaml and environment."""

from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

# Load prompt config
CONFIG_PATH = Path(__file__).parent / "prompts.yaml"

with open(CONFIG_PATH) as f:
    PROMPT_CONFIG = yaml.safe_load(f)

# Retrieval settings
RETRIEVAL_TOP_K = 10          # Initial retrieval count
RERANK_TOP_K = 5              # After reranking, keep top 5
CHUNK_SIZE = 650              # Target tokens per chunk
CHUNK_OVERLAP = 100           # Token overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "qwen2.5:7b"    # Local Ollama model for RAG generation (4.7GB; fits 16GB RAM)
# LLM_MODEL = "gemma4"      # 9.6GB — too large for 16GB RAM alongside Weaviate (crashes)
# LLM_MODEL = "claude-sonnet-4-6"  # Claude API via langchain-anthropic (requires ANTHROPIC_API_KEY)

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