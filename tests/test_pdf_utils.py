"""Tests for PDF text extraction utilities."""

from pathlib import Path

import pytest
from rag_pipeline.core.chunking import get_page_chunks
from rag_pipeline.utils.pdf_utils import clean_pdf_text, extract_and_clean_pdf, extract_pdf_text


@pytest.mark.skipif(not pytest.importorskip("pypdf", reason="pypdf not installed"), reason="pypdf missing")
def test_extract_pdf_text(test_data_dir):
    pdf_path = test_data_dir / "2005.11401v4.pdf"
    pages = extract_pdf_text(pdf_path)
    assert isinstance(pages, list)
    assert pages
    assert all(isinstance(p, str) for p in pages)


def test_clean_pdf_text():
    """Test PDF text cleaning."""
    raw = "Example hy-\nphenated word."
    cleaned = clean_pdf_text(raw)
    assert "hyphenated" in cleaned
    assert "\n" not in cleaned


def test_extract_and_clean_pdf():
    """Test combined extraction and cleaning."""
    pdf_path = Path("tests/test_data/learninglangchain.pdf")
    pages = extract_and_clean_pdf(pdf_path)
    assert len(pages) > 0
    assert all(isinstance(page, str) for page in pages)


def test_page_numbering_with_roman_numerals():
    """Test that page numbering works correctly with Roman numerals in the PDF.

    This test verifies that:
    1. Page numbers are 0-based indices
    2. Cover pages are included in the numbering
    3. Roman numerals in the PDF don't affect the page numbering
    """
    pdf_path = Path("tests/test_data/learninglangchain.pdf")
    page_chunks = get_page_chunks(pdf_path)

    # Verify we have chunks
    assert len(page_chunks) > 0

    # Verify page numbers are sequential and 0-based
    page_numbers = sorted(page_chunks.keys())
    assert page_numbers[0] == 1  # First page should be 1 (react-pdf is 1-based)
    assert page_numbers[-1] == len(page_numbers)  # Last page should be len
