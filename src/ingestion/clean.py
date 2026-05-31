"""Clean page text and extract structural metadata for CambridgeMATHS textbooks.

These books (CambridgeMATHS NSW Stage 6) repeat a copyright/ISBN footer on every
page and carry a running header band (page number, section code, chapter title) at
the top of each page. Left in place this boilerplate pollutes embeddings and gets
retrieved as noise. We strip it and, where possible, lift the chapter/section into
metadata so answers can cite *where* in the book they came from.
"""

import re

# Footer boilerplate — these lines only ever appear in the page footer, so it is
# safe to remove them wherever they occur.
_FOOTER_PATTERNS = [
    re.compile(r"^©\s.*\d{4}\s*$"),                       # © Powers et al. 2025
    re.compile(r"^Cambridge University Press.*$", re.I),
    re.compile(r"^ISBN\s.*$", re.I),
    re.compile(r"^Photocopying is restricted.*$", re.I),
    re.compile(r"^CambridgeMATHS\b.*$", re.I),
    re.compile(r"^Year\s+\d{1,2}\s*$"),                   # lone "Year 11" footer line
    re.compile(r"^Uncorrected\b.*sample.*$", re.I),
]

# Header band, in the order it appears at the top of a page.
_PAGENUM = re.compile(r"^\d{1,4}$")
_SECTION_CODE = re.compile(r"^(\d{1,2}[A-Z])$")          # 1G, 4B
_CHAPTER = re.compile(r"^Chapter\s+(\d+)\s+(.+?)\s*$")


def parse_source_metadata(filename: str) -> dict:
    """Derive year / subject / course from a filename like
    '11 Mathematics Standard textbook.pdf'.
    """
    stem = re.sub(r"\.pdf$", "", filename, flags=re.I)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+([A-Za-z]+)", stem)
    if m:
        return {
            "year": int(m.group(1)),
            "subject": m.group(2),
            "course": m.group(3),
        }
    return {"year": 0, "subject": stem, "course": ""}


def _strip_footer(lines: list[str]) -> list[str]:
    return [ln for ln in lines if not any(p.match(ln.strip()) for p in _FOOTER_PATTERNS)]


def _consume_header_band(lines: list[str]) -> tuple[list[str], dict]:
    """Remove the leading page-number / section-code / chapter-title band and
    return it as metadata. Consumes each role at most once, in order, and stops at
    the first line that isn't part of the band — so inline content (e.g. a question
    number that looks like a page number) is never touched."""
    meta: dict = {}
    i = 0
    n = len(lines)

    # skip leading blanks
    while i < n and not lines[i].strip():
        i += 1

    if i < n and _PAGENUM.match(lines[i].strip()):
        i += 1
        while i < n and not lines[i].strip():
            i += 1

    if i < n:
        sec = _SECTION_CODE.match(lines[i].strip())
        if sec:
            meta["section"] = sec.group(1)
            i += 1
            while i < n and not lines[i].strip():
                i += 1

    if i < n:
        chap = _CHAPTER.match(lines[i].strip())
        if chap:
            meta["chapter"] = int(chap.group(1))
            meta["chapter_title"] = chap.group(2)
            i += 1

    return lines[i:], meta


_LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
    "ﬃ": "ffi", "ﬄ": "ffl", " ": " ",
}


def _normalize(text: str) -> str:
    for src, dst in _LIGATURES.items():
        text = text.replace(src, dst)
    return text


def clean_page(text: str) -> tuple[str, dict]:
    """Return (cleaned_text, structural_metadata) for one page of extracted text."""
    lines = _normalize(text).split("\n")
    lines = _strip_footer(lines)
    lines, meta = _consume_header_band(lines)

    # drop a trailing lone page-number line
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and _PAGENUM.match(lines[-1].strip()):
        lines.pop()

    cleaned = "\n".join(lines).strip()
    return cleaned, meta
