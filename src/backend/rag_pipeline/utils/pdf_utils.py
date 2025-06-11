"""PDF text extraction and cleanup utilities.

These helpers provide granular access to PDF text for debugging
conversion issues. See docs/technical/PDF_PROCESSING.md for details.
"""

from __future__ import annotations

import re
from pathlib import Path


def extract_pdf_text(pdf_path: str | Path) -> list[str]:
    """Return raw text of each page in the PDF.

    Returns a list of strings, where each string is the text content of a page.
    The list index corresponds to the page number (0-based), including cover pages.
    """
    from pypdf import PdfReader  # imported lazily for optional dependency

    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))
    return [page.extract_text() or "" for page in reader.pages]


def clean_pdf_text(text: str) -> str:
    """Clean common PDF extraction artefacts."""
    # remove hyphenation at line endings
    text = re.sub(r"-\n(?=\w)", "", text)
    # collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_and_clean_pdf(pdf_path: str | Path) -> list[str]:
    """Extract pages and apply :func:`clean_pdf_text` to each."""
    return [clean_pdf_text(t) for t in extract_pdf_text(pdf_path)]


__all__ = ["extract_pdf_text", "clean_pdf_text", "extract_and_clean_pdf"]
