"""Load PDF documents and extract text content.

Uses the `pdftotext` CLI (poppler) rather than PyPDFLoader: on TeX-generated
PDFs pypdf drops inter-word spaces, wrecking retrieval. pdftotext preserves
word spacing and a clean per-page line structure that clean_page can parse.

A "book" is either a single top-level PDF (e.g. "11 Mathematics Standard
textbook.pdf") or a folder of PDFs (e.g. "12 Investigating Science textbook/"
with one PDF per chapter). Book-level metadata (years/subject/course) is parsed
from the file stem or the folder name; per-file chapter info (Science) is parsed
from each PDF's own name.
"""

import subprocess
from pathlib import Path

from langchain_core.documents import Document

from src.ingestion.clean import clean_page, parse_source_metadata, parse_pdf_structure


def _pdf_to_pages(file_path: Path) -> list[str]:
    """Extract a PDF to a list of per-page text strings via pdftotext."""
    result = subprocess.run(
        ["pdftotext", str(file_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split("\x0c")  # form-feed separates pages


def load_pdf(file_path: str | Path, book_name: str | None = None) -> list:
    """
    Load one PDF into per-page Document objects.

    Args:
        file_path: path to the PDF.
        book_name: the book this PDF belongs to (file stem for a single-PDF book,
            or the folder name for a multi-PDF book). Drives years/subject/course.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    book = book_name or file_path.stem
    source_meta = parse_source_metadata(book)          # years, subject, course
    struct_meta = parse_pdf_structure(file_path.name)  # chapter/title from filename (Science)

    documents = []
    for i, raw in enumerate(_pdf_to_pages(file_path)):
        text, page_meta = clean_page(raw)
        if not text:
            continue  # pure boilerplate / blank page
        metadata = {"source_file": book, "page": i + 1}
        metadata.update(source_meta)   # years, subject, course
        metadata.update(page_meta)     # CambridgeMATHS chapter/section (if detected)
        metadata.update(struct_meta)   # filename chapter/title — wins for Science
        documents.append(Document(page_content=text, metadata=metadata))

    print(f"Loaded {len(documents)} pages from {file_path.name} [{book}]")
    return documents


def load_all_pdfs(directory: str | Path) -> list:
    """Load every book under a directory. Top-level PDFs are single-PDF books;
    sub-folders are multi-PDF books (all their PDFs share the folder's metadata)."""
    directory = Path(directory)
    all_documents = []

    for entry in sorted(directory.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_file() and entry.suffix.lower() == ".pdf":
            all_documents.extend(load_pdf(entry, book_name=entry.stem))
        elif entry.is_dir():
            for pdf in sorted(entry.glob("*.pdf")):
                all_documents.extend(load_pdf(pdf, book_name=entry.name))

    print(f"Total: {len(all_documents)} pages from {directory}")
    return all_documents
