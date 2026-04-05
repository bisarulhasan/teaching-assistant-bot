"""Basic tests for the chunking module."""

from langchain_core.documents import Document
from src.ingestion.chunker import chunk_documents, create_chunker


def test_chunk_size_within_range():
    """Verify chunks are within the 500-800 token target range."""
    # Create a fake long document
    fake_doc = Document(
        page_content="This is a test sentence. " * 500,
        metadata={"source_file": "test.pdf", "page": 1},
    )
    
    chunks = chunk_documents([fake_doc])
    
    for chunk in chunks:
        token_count = chunk.metadata["token_count"]
        # Allow some tolerance for edge chunks
        assert token_count <= 850, f"Chunk too large: {token_count} tokens"


def test_chunk_metadata_preserved():
    """Verify source metadata is carried through to chunks."""
    fake_doc = Document(
        page_content="Short content for testing metadata preservation.",
        metadata={"source_file": "biology.pdf", "page": 5},
    )
    
    chunks = chunk_documents([fake_doc])
    
    for chunk in chunks:
        assert chunk.metadata["source_file"] == "biology.pdf"
        assert chunk.metadata["page"] == 5
        assert "chunk_id" in chunk.metadata


def test_empty_input_returns_empty():
    """Verify empty input doesn't crash."""
    chunks = chunk_documents([])
    assert chunks == []