"""Hybrid retrieval combining BM25 + vector search with Reciprocal Rank Fusion."""

import weaviate
from src.retrieval.vector_retriever import vector_search
from src.retrieval.bm25_retriever import BM25Retriever


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion (RRF).
    
    RRF score = sum(1 / (k + rank_i)) across all lists.
    This is the same fusion method used by Weaviate and Elasticsearch.
    
    Args:
        result_lists: List of ranked result lists to fuse.
        k: RRF constant (default 60, standard value from the original paper).
        
    Returns:
        Fused and re-sorted list of results.
    """
    fused_scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}
    
    for results in result_lists:
        for rank, doc in enumerate(results):
            # Use chunk_id as unique key, fallback to content hash
            doc_key = doc["metadata"].get("chunk_id") or str(hash(doc["content"]))
            
            if doc_key not in fused_scores:
                fused_scores[doc_key] = 0.0
                doc_map[doc_key] = doc
            
            fused_scores[doc_key] += 1.0 / (k + rank + 1)
    
    # Sort by fused score (descending)
    sorted_keys = sorted(fused_scores, key=fused_scores.get, reverse=True)
    
    results = []
    for key in sorted_keys:
        doc = doc_map[key].copy()
        doc["score"] = fused_scores[key]
        results.append(doc)
    
    return results


def hybrid_search(
    query: str,
    client: weaviate.WeaviateClient,
    bm25_retriever: BM25Retriever,
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    """
    Perform hybrid search combining BM25 and vector retrieval.

    Args:
        query: The search query.
        client: Weaviate client for vector search.
        bm25_retriever: Initialized BM25Retriever instance.
        top_k: Number of final results after fusion.
        filters: Optional {year, subject, course} to scope retrieval.

    Returns:
        Fused and ranked list of results.
    """
    # Get results from both retrievers
    vector_results = vector_search(query, client, top_k=top_k, filters=filters)
    bm25_results = bm25_retriever.search(query, top_k=top_k, filters=filters)
    
    print(f"Vector results: {len(vector_results)}, BM25 results: {len(bm25_results)}")
    
    # Fuse with RRF
    fused = reciprocal_rank_fusion([vector_results, bm25_results])
    
    return fused[:top_k]