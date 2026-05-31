"""Vector-based semantic retrieval from Weaviate."""

from functools import lru_cache

import weaviate
from weaviate.classes.query import Filter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "TeachingAssistantChunks"


@lru_cache(maxsize=1)
def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Load the embedding model once and reuse it (loading is ~seconds)."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "mps"},
    )


def build_filter(filters: dict | None):
    """Build a Weaviate filter from {year, subject, course} (any subset)."""
    if not filters:
        return None
    conditions = []
    for prop in ("year", "subject", "course"):
        val = filters.get(prop)
        if val not in (None, "", 0):
            conditions.append(Filter.by_property(prop).equal(val))
    if not conditions:
        return None
    return Filter.all_of(conditions) if len(conditions) > 1 else conditions[0]


def vector_search(
    query: str,
    client: weaviate.WeaviateClient,
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    """
    Perform vector similarity search against Weaviate.

    Args:
        query: The user's question.
        client: Connected Weaviate client.
        top_k: Number of results to return.
        filters: Optional {year, subject, course} to scope retrieval.

    Returns:
        List of dicts with 'content', 'metadata', and 'score' keys.
    """
    query_vector = get_embeddings_model().embed_query(query)

    collection = client.collections.get(COLLECTION_NAME)

    results = collection.query.near_vector(
        near_vector=query_vector,
        limit=top_k,
        filters=build_filter(filters),
        return_metadata=weaviate.classes.query.MetadataQuery(distance=True),
    )
    
    retrieved = []
    for obj in results.objects:
        retrieved.append({
            "content": obj.properties["content"],
            "metadata": {
                "source_file": obj.properties.get("source_file", ""),
                "page": obj.properties.get("page", 0),
                "chunk_id": obj.properties.get("chunk_id", ""),
                "year": obj.properties.get("year", 0),
                "subject": obj.properties.get("subject", ""),
                "course": obj.properties.get("course", ""),
                "chapter": obj.properties.get("chapter", 0),
                "chapter_title": obj.properties.get("chapter_title", ""),
                "section": obj.properties.get("section", ""),
            },
            "score": 1 - (obj.metadata.distance or 0),  # Convert distance to similarity
        })
    
    return retrieved