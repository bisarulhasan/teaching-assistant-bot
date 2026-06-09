"""Embeddings via FastEmbed (ONNX all-MiniLM-L6-v2).

Same model/dimension (384) as before, but ONNX instead of PyTorch — far lighter,
so it runs on small hosts (Render free tier) without GPU. Used for both ingestion
and query embedding so the vectors are consistent.
"""

from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL_NAME)


def embed_documents(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    return next(iter(_model().embed([text]))).tolist()
