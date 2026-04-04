"""Main RAG pipeline — ties ingestion, retrieval, and generation together."""

from src.ingestion.loader import load_all_pdfs
from src.ingestion.chunker import chunk_documents
from src.ingestion.embedder import get_weaviate_client, create_collection, embed_and_store
from src.retrieval.vector_retriever import vector_search
from src.generation.generator import generate_answer


def ingest(data_dir: str = "data/raw", fresh: bool = False):
    """Run the full ingestion pipeline."""
    print("=" * 60)
    print("INGESTION PIPELINE")
    print("=" * 60)
    
    # Step 1: Load PDFs
    documents = load_all_pdfs(data_dir)
    
    # Step 2: Chunk documents
    chunks = chunk_documents(documents)
    
    # Step 3: Embed and store in Weaviate
    client = get_weaviate_client()
    try:
        create_collection(client, delete_existing=fresh)
        embed_and_store(chunks, client)
    finally:
        client.close()
    
    print("Ingestion complete!")
    return chunks


def query(question: str, top_k: int = 5) -> dict:
    """Run a single query through the RAG pipeline."""
    client = get_weaviate_client()
    try:
        # Retrieve relevant chunks
        retrieved = vector_search(question, client, top_k=top_k)
        
        # Generate answer
        result = generate_answer(question, retrieved)
        
        return result
    finally:
        client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        # Run: python -m src.pipeline ingest
        fresh = "--fresh" in sys.argv
        ingest(fresh=fresh)
    else:
        # Run: python -m src.pipeline "What is photosynthesis?"
        question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is this textbook about?"
        result = query(question)
        
        print("\n" + "=" * 60)
        print("ANSWER:")
        print("=" * 60)
        print(result["answer"])
        print("\nSOURCES:")
        for src in result["sources"]:
            print(f"  - {src['file']}, Page {src['page']}")