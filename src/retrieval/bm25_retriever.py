"""BM25 keyword-based retrieval for hybrid search."""

import json
from pathlib import Path
from rank_bm25 import BM25Okapi
import weaviate

COLLECTION_NAME = "TeachingAssistantChunks"


class BM25Retriever:
    """BM25 keyword retriever that works alongside vector search."""
    
    def __init__(self, client):
        """Load all chunks (from Weaviate or Qdrant) and build the BM25 index."""
        from src.config.settings import VECTOR_DB

        if VECTOR_DB == "qdrant":
            from src.retrieval.qdrant_store import scroll_all
            self.documents = scroll_all(client)
        else:
            collection = client.collections.get(COLLECTION_NAME)
            self.documents = [
                {
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
                }
                for obj in collection.iterator()
            ]

        self.tokenized_corpus = [d["content"].lower().split() for d in self.documents]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"BM25 index built with {len(self.documents)} documents")
    
    @staticmethod
    def _matches(metadata: dict, filters: dict | None) -> bool:
        """True if the chunk metadata satisfies all {year, subject, course} filters."""
        if not filters:
            return True
        for prop in ("year", "subject", "course"):
            val = filters.get(prop)
            if val not in (None, "", 0) and metadata.get(prop) != val:
                return False
        return True

    def search(self, query: str, top_k: int = 10, filters: dict | None = None) -> list[dict]:
        """
        Search using BM25 keyword matching.

        Args:
            query: The search query.
            top_k: Number of top results to return.
            filters: Optional {year, subject, course} to scope retrieval.

        Returns:
            List of dicts with 'content', 'metadata', and 'score' keys.
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Rank all docs, then keep the top_k that are non-zero and pass the filter
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked:
            if scores[idx] <= 0:
                break  # remaining are all zero
            if not self._matches(self.documents[idx]["metadata"], filters):
                continue
            results.append({
                "content": self.documents[idx]["content"],
                "metadata": self.documents[idx]["metadata"],
                "score": float(scores[idx]),
            })
            if len(results) >= top_k:
                break

        return results