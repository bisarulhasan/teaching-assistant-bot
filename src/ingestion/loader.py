"""Load PDF documents and extract text content."""

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path: str | Path) -> list:
    """
    Load a PDF file and return a list of Document objects (one per page).
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        List of LangChain Document objects with page_content and metadata.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    
    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    
    # Add source filename to metadata
    for doc in documents:
        doc.metadata["source_file"] = file_path.name
    
    print(f"Loaded {len(documents)} pages from {file_path.name}")
    return documents


def load_all_pdfs(directory: str | Path) -> list:
    """Load all PDFs from a directory."""
    directory = Path(directory)
    all_documents = []
    
    for pdf_path in sorted(directory.glob("*.pdf")):
        docs = load_pdf(pdf_path)
        all_documents.extend(docs)
    
    print(f"Total: {len(all_documents)} pages from {directory}")
    return all_documents