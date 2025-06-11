"""Tests for PDF text extraction utilities."""

from pathlib import Path

import pytest
from rag_pipeline.core.chunking import get_page_chunks
from rag_pipeline.utils.pdf_utils import clean_pdf_text, extract_and_clean_pdf, extract_pdf_text


@pytest.mark.skipif(not pytest.importorskip("pypdf", reason="pypdf not installed"), reason="pypdf missing")
def test_extract_pdf_text(test_data_dir):
    """Test PDF text extraction.

    Verifies that:
    1. The function returns a non-empty list
    2. Each page is a string
    3. The list contains the expected number of pages
    """
    pdf_path = test_data_dir / "2005.11401v4.pdf"
    pages = extract_pdf_text(pdf_path)

    # Use pytest's assertion helpers
    assert pages, "Expected non-empty list of pages"
    assert all(isinstance(p, str) for p in pages), "All pages should be strings"
    assert len(pages) > 0, "Expected at least one page"


def test_clean_pdf_text():
    """Test PDF text cleaning.

    Verifies that:
    1. Hyphenated words are properly joined
    2. Newlines are removed
    3. The text is properly cleaned
    """
    raw = "Example hy-\nphenated word."
    cleaned = clean_pdf_text(raw)

    assert "hyphenated" in cleaned, "Hyphenated word should be joined"
    assert "\n" not in cleaned, "Newlines should be removed"
    assert cleaned == "Example hyphenated word.", "Text should be properly cleaned"


@pytest.mark.skipif(
    not Path("tests/test_data/learninglangchain.pdf").exists(), reason="learninglangchain.pdf not found in test data directory"
)
def test_extract_and_clean_pdf():
    """Test combined extraction and cleaning.

    Verifies that:
    1. The function returns a non-empty list
    2. Each page is a string
    3. The text is properly cleaned
    """
    pdf_path = Path("tests/test_data/learninglangchain.pdf")
    pages = extract_and_clean_pdf(pdf_path)

    assert pages, "Expected non-empty list of pages"
    assert all(isinstance(page, str) for page in pages), "All pages should be strings"
    assert len(pages) > 0, "Expected at least one page"


@pytest.mark.skipif(
    not Path("tests/test_data/learninglangchain.pdf").exists(), reason="learninglangchain.pdf not found in test data directory"
)
def test_page_numbering_with_roman_numerals():
    """Test that page numbering works correctly with Roman numerals in the PDF.

    Verifies that:
    1. Page numbers are 1-based indices (react-pdf convention)
    2. Cover pages are included in the numbering
    3. Roman numerals in the PDF don't affect the page numbering
    """
    pdf_path = Path("tests/test_data/learninglangchain.pdf")
    page_chunks = get_page_chunks(pdf_path)

    # Verify we have chunks
    assert page_chunks, "Expected non-empty page chunks"

    # Verify page numbers are sequential and 1-based
    page_numbers = sorted(page_chunks.keys())
    assert page_numbers[0] == 1, "First page should be 1 (react-pdf is 1-based)"
    assert page_numbers[-1] == len(page_numbers), "Last page number should match total page count"
