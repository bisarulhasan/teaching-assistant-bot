"""Main RAG pipeline — ties ingestion, retrieval, reranking, and generation together."""

from src.ingestion.loader import load_all_pdfs
from src.ingestion.chunker import chunk_documents
from src.ingestion.embedder import get_weaviate_client, create_collection, embed_and_store
from src.retrieval.vector_retriever import vector_search
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_retriever import hybrid_search
from src.retrieval.reranker import rerank_chunks
from src.generation.generator import generate_answer
from src.generation.citation_checker import verify_answer_against_context
from src.config.settings import RETRIEVAL_TOP_K, RERANK_TOP_K


def ingest(data_dir: str = "data/raw", fresh: bool = False):
    """Run the full ingestion pipeline."""
    print("=" * 60)
    print("INGESTION PIPELINE")
    print("=" * 60)
    
    documents = load_all_pdfs(data_dir)
    chunks = chunk_documents(documents)
    
    client = get_weaviate_client()
    try:
        create_collection(client, delete_existing=fresh)
        embed_and_store(chunks, client)
    finally:
        client.close()
    
    print("Ingestion complete!")
    return chunks


def query(
    question: str,
    use_hybrid: bool = True,
    verify: bool = True,
    filters: dict | None = None,
    client=None,
    bm25=None,
) -> dict:
    """
    Run a query through the full RAG pipeline.

    Pipeline: Hybrid Retrieval → Reranking → Generation → Citation Verification

    Args:
        filters: Optional {year, subject, course} to scope retrieval to a
            student's textbooks.
        client, bm25: Optionally inject a pre-initialized Weaviate client and
            BM25 index (the API does this once at startup). When omitted, they
            are created for this call and the client is closed afterwards.
    """
    own_client = client is None
    if own_client:
        client = get_weaviate_client()
    try:
        # Step 1: Retrieve candidates
        if use_hybrid:
            if bm25 is None:
                bm25 = BM25Retriever(client)
            candidates = hybrid_search(
                question, client, bm25, top_k=RETRIEVAL_TOP_K, filters=filters
            )
        else:
            candidates = vector_search(
                question, client, top_k=RETRIEVAL_TOP_K, filters=filters
            )

        print(f"\nRetrieved {len(candidates)} candidates")

        # Step 2: Rerank with cross-encoder
        reranked = rerank_chunks(question, candidates, top_k=RERANK_TOP_K)

        # Step 3: Generate answer
        result = generate_answer(
            question, reranked, prompt_key="rag_answer_with_reranking"
        )

        # Step 4: Citation enforcement
        if verify and result["answer"]:
            verification = verify_answer_against_context(
                question, result["answer"], reranked
            )
            result["verification"] = verification

            if not verification["is_supported"]:
                result["answer"] = (
                    "I don't have enough information in the course materials to "
                    "answer this question confidently. The retrieved materials "
                    "don't sufficiently support a complete answer. "
                    "Please ask your teacher for clarification."
                )
                result["citation_enforced"] = True

        return result
    finally:
        if own_client:
            client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        fresh = "--fresh" in sys.argv
        ingest(fresh=fresh)
    else:
        question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is this textbook about?"
        result = query(question)
        
        print("\n" + "=" * 60)
        print("ANSWER:")
        print("=" * 60)
        print(result["answer"])
        print("\nSOURCES:")
        for src in result["sources"]:
            print(f"  - {src['file']}, Page {src['page']}")
        if "verification" in result:
            v = result["verification"]
            print(f"\nVERIFICATION: supported={v['is_supported']}, confidence={v['confidence']}")