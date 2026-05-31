"""Load PDF documents and extract text content.

Uses the `pdftotext` CLI (poppler) rather than PyPDFLoader: on these TeX-generated
CambridgeMATHS PDFs, pypdf drops inter-word spaces (e.g. "Grosspay,deductionsfrom
payandnetpay"), which wrecks both BM25 and embedding quality. pdftotext preserves
word spacing and emits a clean per-page line structure that clean_page can parse.
"""

import subprocess
from pathlib import Path

from langchain_core.documents import Document

from src.ingestion.clean import clean_page, parse_source_metadata


def _pdf_to_pages(file_path: Path) -> list[str]:
    """Extract a PDF to a list of per-page text strings via pdftotext."""
    result = subprocess.run(
        ["pdftotext", str(file_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    # pdftotext separates pages with a form-feed (\x0c)
    return result.stdout.split("\x0c")


def load_pdf(file_path: str | Path) -> list:
    """
    Load a PDF file and return a list of Document objects (one per page).

    Strips per-page boilerplate (copyright/ISBN footer, running headers) and lifts
    year/subject/course (from the filename) plus chapter/section (from the running
    header) into each page's metadata so answers can cite where they came from.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of LangChain Document objects with page_content and metadata.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    source_meta = parse_source_metadata(file_path.name)
    raw_pages = _pdf_to_pages(file_path)

    documents = []
    for i, raw in enumerate(raw_pages):
        text, page_meta = clean_page(raw)
        if not text:
            continue  # skip pages that were pure boilerplate / blank
        metadata = {"source_file": file_path.name, "page": i + 1}
        metadata.update(source_meta)
        metadata.update(page_meta)
        documents.append(Document(page_content=text, metadata=metadata))

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
