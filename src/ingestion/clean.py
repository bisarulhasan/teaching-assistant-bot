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
    # CambridgeMATHS
    re.compile(r"^©\s.*\d{4}\s*$"),                       # © Powers et al. 2025 / © Licensed ... 2025
    re.compile(r"^Cambridge University Press.*$", re.I),
    re.compile(r"^ISBN\s.*$", re.I),
    re.compile(r"^Photocopying is restricted.*$", re.I),
    re.compile(r"^CambridgeMATHS\b.*$", re.I),
    re.compile(r"^Year\s+\d{1,2}\s*$"),                   # lone "Year 11" footer line
    re.compile(r"^Uncorrected\b.*sample.*$", re.I),
    # Jacaranda (Commerce)
    re.compile(r"^Jacaranda\b.*$", re.I),
    # PDHPE workbooks
    re.compile(r"^Stage\s+\d\b.*Workbook\s*$", re.I),     # "Stage 4 PDHPE Student Workbook"
    re.compile(r"^©\s*Licensed\b.*$", re.I),              # "© Licensed to Western Grammar School ..."
    # Nelson (Investigating Science) print-production artefacts
    re.compile(r"^CHAPTER\s+\d+\s*».*$", re.I),           # running header "CHAPTER 1 » ..."
    re.compile(r"^\S*\.indd\s+\d+\s*$", re.I),            # "01_ISIF_HSC_11264_txt.indd 12"
    re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}\s*[AP]M\s*$", re.I),  # timestamp
    re.compile(r"^97[89]\d{10}\s*$"),                     # bare ISBN-13
]

# Header band, in the order it appears at the top of a page.
_PAGENUM = re.compile(r"^\d{1,4}$")
_SECTION_CODE = re.compile(r"^(\d{1,2}[A-Z])$")          # 1G, 4B
_CHAPTER = re.compile(r"^Chapter\s+(\d+)\s+(.+?)\s*$")


KNOWN_COURSES = {"standard", "advanced", "extension", "general"}


def parse_source_metadata(book_name: str) -> dict:
    """Derive years / subject / course from a book name (file stem OR folder name):

      '11 Mathematics Standard textbook'  -> years [11], 'Mathematics', 'Standard'
      '7:8 PDHPE textbook'                -> years [7, 8], 'PDHPE', ''
      '9 Commerce textbook'               -> years [9], 'Commerce', ''
      '12 Investigating Science textbook' -> years [12], 'Investigating Science', ''

    'course' is only set when the trailing word is a known senior stream
    (Standard/Advanced/Extension); otherwise the whole tail is the subject.
    """
    stem = re.sub(r"\.pdf$", "", book_name, flags=re.I).strip()
    stem = re.sub(r"\s+textbook$", "", stem, flags=re.I)
    stem = re.sub(r"\s+lesson\s+\d+$", "", stem, flags=re.I)

    m = re.match(r"^(\d{1,2}(?::\d{1,2})*)\s+(.+)$", stem)
    if not m:
        return {"years": [0], "subject": stem, "course": ""}

    years = [int(y) for y in m.group(1).split(":")]
    rest = m.group(2).split()
    if rest and rest[-1].lower() in KNOWN_COURSES:
        return {"years": years, "subject": " ".join(rest[:-1]), "course": rest[-1]}
    return {"years": years, "subject": " ".join(rest), "course": ""}


def parse_pdf_structure(filename: str) -> dict:
    """Best-effort chapter number/title from a per-file name such as
    'INVSC12_03_Chapter_3_Module_5_Scientific_investigations.pdf'."""
    meta: dict = {}
    m = re.search(r"chapter[_ ](\d+)", filename, re.I)
    if m:
        meta["chapter"] = int(m.group(1))
        rest = re.search(r"chapter[_ ]\d+[_ ](.+?)(?:\.pdf)?$", filename, re.I)
        if rest:
            meta["chapter_title"] = rest.group(1).replace("_", " ").strip()
    return meta


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
