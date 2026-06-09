"""Ingest the textbook corpus into Qdrant (FastEmbed embeddings).

Mirrors the Weaviate ingestion: load -> chunk -> embed -> upsert, storing a chunk
once per year it belongs to (so 7-8 / 9-10 PDHPE books serve both years).
"""

from src.ingestion.loader import load_all_pdfs
from src.ingestion.chunker import chunk_documents
from src.ingestion.embeddings import embed_documents
from src.retrieval.qdrant_store import ensure_collection, upsert


def ingest_to_qdrant(client, data_dir: str = "data/raw", recreate: bool = True, only: str | None = None) -> int:
    documents = load_all_pdfs(data_dir)
    if only:
        documents = [d for d in documents if only.lower() in d.metadata.get("source_file", "").lower()]
    chunks = chunk_documents(documents)

    ensure_collection(client, recreate=recreate)

    print(f"Embedding {len(chunks)} chunks with FastEmbed...")
    vectors = embed_documents([c.page_content for c in chunks])

    points, pid = [], 0
    for chunk, vector in zip(chunks, vectors):
        m = chunk.metadata
        base = {
            "content": chunk.page_content,
            "source_file": m.get("source_file", ""),
            "page": m.get("page", 0),
            "chunk_id": m.get("chunk_id", ""),
            "token_count": m.get("token_count", 0),
            "subject": m.get("subject", ""),
            "course": m.get("course", ""),
            "chapter": m.get("chapter", 0),
            "chapter_title": m.get("chapter_title", ""),
            "section": m.get("section", ""),
        }
        for year in (m.get("years") or [m.get("year", 0)]):
            points.append((pid, vector, {**base, "year": year}))
            pid += 1

    print(f"Upserting {len(points)} points to Qdrant...")
    for i in range(0, len(points), 256):
        upsert(client, points[i : i + 256])
    print(f"Stored {len(points)} points.")
    return len(points)


if __name__ == "__main__":
    from src.retrieval.qdrant_store import get_client

    client = get_client()
    total = ingest_to_qdrant(client, recreate=True)
    print(f"Ingestion complete — {total} points in Qdrant.")
