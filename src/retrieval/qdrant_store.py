"""Qdrant vector store — hosted 24/7 replacement for local Weaviate.

Connects to Qdrant Cloud via QDRANT_URL / QDRANT_API_KEY, or an in-memory Qdrant
(":memory:") when those aren't set (used for local tests). Search results use the
same {content, metadata, score} shape the rest of the pipeline already expects.
"""

import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.ingestion.embeddings import EMBED_DIM

COLLECTION = "teaching_assistant_chunks"

_META_KEYS = (
    "source_file", "page", "chunk_id", "token_count",
    "year", "subject", "course", "chapter", "chapter_title", "section",
)


def get_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    if url:
        return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"), timeout=60)
    return QdrantClient(":memory:")  # local fallback for tests


def ensure_collection(client: QdrantClient, recreate: bool = False) -> None:
    if recreate and client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )


def upsert(client: QdrantClient, points: list[tuple[int, list[float], dict]]) -> None:
    """points: list of (id, vector, payload)."""
    client.upsert(
        COLLECTION,
        points=[PointStruct(id=i, vector=v, payload=p) for (i, v, p) in points],
    )


def _build_filter(filters: dict | None) -> Filter | None:
    if not filters:
        return None
    must = [
        FieldCondition(key=k, match=MatchValue(value=filters[k]))
        for k in ("year", "subject", "course")
        if filters.get(k) not in (None, "", 0)
    ]
    return Filter(must=must) if must else None


def vector_search(
    query_vector: list[float],
    client: QdrantClient,
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    hits = client.query_points(
        COLLECTION,
        query=query_vector,
        limit=top_k,
        query_filter=_build_filter(filters),
        with_payload=True,
    ).points
    return [
        {
            "content": h.payload.get("content", ""),
            "metadata": {k: h.payload.get(k) for k in _META_KEYS},
            "score": h.score,
        }
        for h in hits
    ]


def scroll_all(client: QdrantClient) -> list[dict]:
    """Every chunk's content + metadata (used to build the in-memory BM25 index)."""
    docs, offset = [], None
    while True:
        batch, offset = client.scroll(
            COLLECTION, limit=512, offset=offset, with_payload=True, with_vectors=False
        )
        for p in batch:
            docs.append(
                {
                    "content": p.payload.get("content", ""),
                    "metadata": {k: p.payload.get(k) for k in _META_KEYS},
                }
            )
        if offset is None:
            break
    return docs
