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
                # Student-facing filters
                Property(name="year", data_type=DataType.INT),
                Property(name="subject", data_type=DataType.TEXT),
                Property(name="course", data_type=DataType.TEXT),
                # Citation context
                Property(name="chapter", data_type=DataType.INT),
                Property(name="chapter_title", data_type=DataType.TEXT),
                Property(name="section", data_type=DataType.TEXT),
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
    
    # Batch insert into Weaviate. A chunk is embedded once but stored once PER
    # year it belongs to (e.g. a 7–8 PDHPE book → one object for year 7 and one
    # for year 8, sharing the same vector). This keeps `year` a simple INT so the
    # retrieval filter / catalog / frontend need no changes.
    print("Storing in Weaviate...")
    with collection.batch.dynamic() as batch:
        for chunk, vector in zip(chunks, vectors):
            m = chunk.metadata
            years = m.get("years") or [m.get("year", 0)]
            for year in years:
                batch.add_object(
                    properties={
                        "content": chunk.page_content,
                        "source_file": m.get("source_file", "unknown"),
                        "page": m.get("page", 0),
                        "chunk_id": m.get("chunk_id", ""),
                        "token_count": m.get("token_count", 0),
                        "year": year,
                        "subject": m.get("subject", ""),
                        "course": m.get("course", ""),
                        "chapter": m.get("chapter", 0),
                        "chapter_title": m.get("chapter_title", ""),
                        "section": m.get("section", ""),
                    },
                    vector=vector,
                )
    
    # Verify
    count = collection.aggregate.over_all(total_count=True).total_count
    print(f"Stored {count} chunks in Weaviate")