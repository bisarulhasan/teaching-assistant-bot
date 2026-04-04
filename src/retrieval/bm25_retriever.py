"""BM25 keyword-based retrieval for hybrid search."""

import json
from pathlib import Path
from rank_bm25 import BM25Okapi
import weaviate

COLLECTION_NAME = "TeachingAssistantChunks"


class BM25Retriever:
    """BM25 keyword retriever that works alongside vector search."""
    
    def __init__(self, client: weaviate.WeaviateClient):
        """Load all chunks from Weaviate and build BM25 index."""
        collection = client.collections.get(COLLECTION_NAME)
        
        self.documents = []
        self.tokenized_corpus = []
        
        # Fetch all documents from Weaviate
        for obj in collection.iterator():
            doc = {
                "content": obj.properties["content"],
                "metadata": {
                    "source_file": obj.properties.get("source_file", ""),
                    "page": obj.properties.get("page", 0),
                    "chunk_id": obj.properties.get("chunk_id", ""),
                },
            }
            self.documents.append(doc)
            # Simple whitespace tokenization for BM25
            self.tokenized_corpus.append(doc["content"].lower().split())
        
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"BM25 index built with {len(self.documents)} documents")
    
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Search using BM25 keyword matching.
        
        Args:
            query: The search query.
            top_k: Number of top results to return.
            
        Returns:
            List of dicts with 'content', 'metadata', and 'score' keys.
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append({
                    "content": self.documents[idx]["content"],
                    "metadata": self.documents[idx]["metadata"],
                    "score": float(scores[idx]),
                })
        
        return results