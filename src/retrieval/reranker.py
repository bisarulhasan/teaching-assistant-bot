"""Cross-encoder reranking using Cohere Rerank API."""

import os
import cohere
from dotenv import load_dotenv

load_dotenv()


def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    model: str = "rerank-v3.5",
) -> list[dict]:
    """
    Rerank retrieved chunks using Cohere's cross-encoder reranker.
    
    The cross-encoder evaluates each (query, chunk) pair together,
    producing much more accurate relevance scores than bi-encoder similarity.
    
    Args:
        query: The original user query.
        chunks: List of retrieved chunks to rerank.
        top_k: Number of top results to keep after reranking.
        model: Cohere rerank model to use.
        
    Returns:
        Top-k reranked chunks sorted by relevance score.
    """
    if not chunks:
        return []
    
    co = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
    
    # Extract texts for reranking
    documents = [chunk["content"] for chunk in chunks]
    
    response = co.rerank(
        query=query,
        documents=documents,
        model=model,
        top_n=top_k,
    )
    
    # Map reranked results back to original chunk data
    reranked = []
    for result in response.results:
        chunk = chunks[result.index].copy()
        chunk["rerank_score"] = result.relevance_score
        chunk["original_rank"] = result.index
        reranked.append(chunk)
    
    print(f"Reranked {len(chunks)} → top {len(reranked)} chunks")
    for i, r in enumerate(reranked):
        print(f"  #{i+1}: score={r['rerank_score']:.4f} "
              f"(was rank #{r['original_rank']+1}) "
              f"chunk={r['metadata'].get('chunk_id', '?')}")
    
    return reranked