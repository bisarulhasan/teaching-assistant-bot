"""Cross-encoder reranking using Cohere Rerank API."""

import os
import time
import cohere
from dotenv import load_dotenv

try:
    from cohere.errors import TooManyRequestsError
except Exception:  # pragma: no cover - import shape varies by version
    TooManyRequestsError = None

load_dotenv()


def _rerank_with_backoff(co, *, query, documents, model, top_n, max_retries: int = 5):
    """Call Cohere rerank, retrying with backoff on 429s.

    The free Cohere trial key allows only ~10 calls/minute, so a burst (eval
    runs, or many students at once) will rate-limit. Backing off lets the work
    finish instead of crashing — and keeps the live bot resilient.
    """
    for attempt in range(max_retries + 1):
        try:
            return co.rerank(query=query, documents=documents, model=model, top_n=top_n)
        except Exception as e:  # noqa: BLE001 - we re-raise non-rate-limit errors
            msg = str(e).lower()
            rate_limited = (
                (TooManyRequestsError is not None and isinstance(e, TooManyRequestsError))
                or "429" in msg
                or "too many requests" in msg
                or "trial key" in msg
            )
            if not rate_limited or attempt == max_retries:
                raise
            wait = 7 * (attempt + 1)  # 7s, 14s, ... clears the 10/min window
            print(f"Cohere rate limit — backing off {wait}s (retry {attempt + 1}/{max_retries})")
            time.sleep(wait)


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
    
    response = _rerank_with_backoff(
        co, query=query, documents=documents, model=model, top_n=top_k
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