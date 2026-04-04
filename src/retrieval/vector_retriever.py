"""Vector-based semantic retrieval from Weaviate."""

import weaviate
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "TeachingAssistantChunks"


def vector_search(
    query: str,
    client: weaviate.WeaviateClient,
    top_k: int = 10,
) -> list[dict]:
    """
    Perform vector similarity search against Weaviate.
    
    Args:
        query: The user's question.
        client: Connected Weaviate client.
        top_k: Number of results to return.
        
    Returns:
        List of dicts with 'content', 'metadata', and 'score' keys.
    """
    embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "mps"},
    )
    query_vector = embeddings_model.embed_query(query)
    
    collection = client.collections.get(COLLECTION_NAME)
    
    results = collection.query.near_vector(
        near_vector=query_vector,
        limit=top_k,
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
            },
            "score": 1 - (obj.metadata.distance or 0),  # Convert distance to similarity
        })
    
    return retrieved