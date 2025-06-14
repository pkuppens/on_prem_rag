"""DOCX text extraction and cleanup utilities.

These helpers provide granular access to DOCX text for debugging
conversion issues. Similar to PDF_PROCESSING.md, see docs/technical/DOCX_PROCESSING.md for details.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document  # imported lazily for optional dependency


def extract_docx_text(docx_path: str | Path) -> list[str]:
    """Return raw text of each paragraph in the DOCX.

    Returns a list of strings, where each string is the text content of a paragraph.
    The list index corresponds to the paragraph number (0-based).
    """
    docx_path = Path(docx_path)
    doc = Document(str(docx_path))
    return [paragraph.text for paragraph in doc.paragraphs]


def clean_docx_text(text: str) -> str:
    """Clean common DOCX extraction artefacts.

    This function is similar to clean_pdf_text but may need DOCX-specific
    cleaning rules in the future.
    """
    # Remove any special characters or formatting artifacts
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_and_clean_docx(docx_path: str | Path) -> list[str]:
    """Extract paragraphs and apply :func:`clean_docx_text` to each."""
    return [clean_docx_text(t) for t in extract_docx_text(docx_path)]


__all__ = ["extract_docx_text", "clean_docx_text", "extract_and_clean_docx"]
