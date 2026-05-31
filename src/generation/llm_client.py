"""Select the chat model implementation based on configured LLM model name."""

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


def get_chat_llm(**kwargs: Any):
    """Return a configured chat model instance for the current LLM_MODEL."""
    normalized = LLM_MODEL.lower()

    if normalized.startswith("claude"):
        if ChatAnthropic is None:
            raise ImportError(
                "langchain_anthropic is required for Claude models. "
                "Install langchain-anthropic or choose an Ollama model."
            )
        return ChatAnthropic(model=LLM_MODEL, **kwargs)

    if ChatOllama is None:
        raise ImportError(
            "langchain_ollama is required for Ollama models. "
            "Install langchain-ollama or choose a Claude model."
        )
    return ChatOllama(model=LLM_MODEL, **kwargs)
