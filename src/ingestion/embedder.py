"""Embed chunks and store in Weaviate vector database."""

import os
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "TeachingAssistantChunks"


def get_weaviate_client() -> weaviate.WeaviateClient:
    """Connect to local Weaviate instance."""
    client = weaviate.connect_to_local()
    print(f"Weaviate connected: {client.is_ready()}")
    return client


def create_collection(client: weaviate.WeaviateClient, delete_existing: bool = False):
    """Create or recreate the Weaviate collection for storing chunks."""
    if delete_existing and client.collections.exists(COLLECTION_NAME):
        client.collections.delete(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    
    if not client.collections.exists(COLLECTION_NAME):
        client.collections.create(
            name=COLLECTION_NAME,
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source_file", data_type=DataType.TEXT),
                Property(name="page", data_type=DataType.INT),
                Property(name="chunk_id", data_type=DataType.TEXT),
                Property(name="token_count", data_type=DataType.INT),
            ],
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


def embed_and_store(chunks: list, client: weaviate.WeaviateClient):
    """
    Generate OpenAI embeddings for each chunk and store in Weaviate.
    
    Uses batch imports for efficiency.
    """
    embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "mps"},  # Uses your M1 GPU
    )
    collection = client.collections.get(COLLECTION_NAME)
    
    # Batch embed all chunks
    texts = [chunk.page_content for chunk in chunks]
    print(f"Generating embeddings for {len(texts)} chunks...")
    vectors = embeddings_model.embed_documents(texts)
    
    # Batch insert into Weaviate
    print("Storing in Weaviate...")
    with collection.batch.dynamic() as batch:
        for chunk, vector in zip(chunks, vectors):
            batch.add_object(
                properties={
                    "content": chunk.page_content,
                    "source_file": chunk.metadata.get("source_file", "unknown"),
                    "page": chunk.metadata.get("page", 0),
                    "chunk_id": chunk.metadata.get("chunk_id", ""),
                    "token_count": chunk.metadata.get("token_count", 0),
                },
                vector=vector,
            )
    
    # Verify
    count = collection.aggregate.over_all(total_count=True).total_count
    print(f"Stored {count} chunks in Weaviate")