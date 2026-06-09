"""Select the chat model implementation based on configured LLM model name.

Routing by LLM_MODEL shape:
  - "vendor/model" (e.g. "qwen/qwen-2.5-72b-instruct")  -> OpenRouter (hosted)
  - "claude..."                                          -> Anthropic
  - anything else (e.g. "qwen2.5:7b")                    -> local Ollama
"""

import os
from typing import Any

from src.config.settings import LLM_MODEL

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:  # pragma: no cover
    ChatAnthropic = None

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover
    ChatOllama = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    ChatOpenAI = None


def get_chat_llm(**kwargs: Any):
    """Return a configured chat model instance for the current LLM_MODEL."""
    model = LLM_MODEL
    normalized = model.lower()

    # OpenRouter models are namespaced "vendor/model"
    if "/" in model:
        if ChatOpenAI is None:
            raise ImportError("langchain-openai is required for OpenRouter models.")
        return ChatOpenAI(
            model=model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            **kwargs,
        )

    if normalized.startswith("claude"):
        if ChatAnthropic is None:
            raise ImportError(
                "langchain_anthropic is required for Claude models. "
                "Install langchain-anthropic or choose an Ollama model."
            )
        return ChatAnthropic(model=model, **kwargs)

    if ChatOllama is None:
        raise ImportError(
            "langchain_ollama is required for Ollama models. "
            "Install langchain-ollama or choose a Claude model."
        )
    return ChatOllama(model=model, **kwargs)
