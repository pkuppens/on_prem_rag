"""Tests for DOCX text extraction utilities."""

from pathlib import Path

import pytest
from rag_pipeline.utils.docx_utils import clean_docx_text, extract_and_clean_docx, extract_docx_text


@pytest.mark.skipif(not pytest.importorskip("docx", reason="python-docx not installed"), reason="python-docx missing")
def test_extract_docx_text(test_data_dir):
    """Test DOCX text extraction.

    Verifies that:
    1. The function returns a non-empty list
    2. Each paragraph is a string
    3. The list contains the expected number of paragraphs
    """
    docx_path = test_data_dir / "toolsfairy-com-sample-docx-files-sample4.docx"
    paragraphs = extract_docx_text(docx_path)

    # Use pytest's assertion helpers
    assert paragraphs, "Expected non-empty list of paragraphs"
    assert all(isinstance(p, str) for p in paragraphs), "All paragraphs should be strings"
    assert len(paragraphs) > 0, "Expected at least one paragraph"


def test_clean_docx_text():
    """Test DOCX text cleaning.

    Verifies that:
    1. Special characters are removed
    2. Multiple whitespace is collapsed
    3. The text is properly cleaned
    """
    raw = "Example text with  multiple   spaces\nand special chars\x00\x01"
    cleaned = clean_docx_text(raw)

    assert "\x00" not in cleaned, "Special characters should be removed"
    assert "\n" not in cleaned, "Newlines should be removed"
    assert "  " not in cleaned, "Multiple spaces should be collapsed"
    assert cleaned == "Example text with multiple spaces and special chars", "Text should be properly cleaned"


@pytest.mark.skipif(
    not Path("tests/test_data/toolsfairy-com-sample-docx-files-sample4.docx").exists(),
    reason="Sample DOCX file not found in test data directory",
)
def test_extract_and_clean_docx():
    """Test combined extraction and cleaning.

    Verifies that:
    1. The function returns a non-empty list
    2. Each paragraph is a string
    3. The text is properly cleaned
    """
    docx_path = Path("tests/test_data/toolsfairy-com-sample-docx-files-sample4.docx")
    paragraphs = extract_and_clean_docx(docx_path)

    assert paragraphs, "Expected non-empty list of paragraphs"
    assert all(isinstance(p, str) for p in paragraphs), "All paragraphs should be strings"
    assert len(paragraphs) > 0, "Expected at least one paragraph"
    assert all("\n" not in p for p in paragraphs), "No paragraphs should contain newlines"
    assert all("  " not in p for p in paragraphs), "No paragraphs should contain multiple spaces"
