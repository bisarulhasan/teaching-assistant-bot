"""Chunk documents into overlapping pieces of 500-800 tokens."""

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_chunker(
    chunk_size: int = 650,       # Target ~650 tokens (middle of 500-800 range)
    chunk_overlap: int = 100,    # ~100 tokens overlap
    model_name: str = "gpt-4o"  # Tokenizer model for accurate token counting
) -> RecursiveCharacterTextSplitter:
    """
    Create a text splitter that chunks by token count, not character count.
    
    This ensures chunks are actually 500-800 tokens as required,
    rather than guessing based on character count.
    """
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name=model_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_documents(documents: list, chunker=None) -> list:
    """
    Split documents into chunks and enrich metadata.
    
    Args:
        documents: List of LangChain Document objects.
        chunker: Optional pre-configured text splitter.
        
    Returns:
        List of chunked Document objects with enriched metadata.
    """
    if chunker is None:
        chunker = create_chunker()
    
    chunks = chunker.split_documents(documents)
    
    # Add chunk IDs and token counts for traceability
    encoding = tiktoken.encoding_for_model("gpt-4o")
    
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i:04d}"
        chunk.metadata["token_count"] = len(encoding.encode(chunk.page_content))
    
    print(f"Created {len(chunks)} chunks from {len(documents)} pages")

    if not chunks:
        return chunks

    # Print token distribution for verification
    token_counts = [c.metadata["token_count"] for c in chunks]
    print(f"Token range: {min(token_counts)} - {max(token_counts)}, "
          f"avg: {sum(token_counts) / len(token_counts):.0f}")
    
    return chunks