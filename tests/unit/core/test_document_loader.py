"""Tests for the document loader module.

As a developer I want comprehensive tests for document loading,
so I can trust that all formats, metadata extraction, and error paths work.
Technical: covers PDF, DOCX, TXT, MD, HTML loading; metadata extraction;
duplicate detection; edge cases.
"""

import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("llama_index")
from llama_index.core import Document
from rag_pipeline.core.document_loader import (
    DocumentLoader,
    DocumentMetadata,
    HtmlProcessor,
    _HTMLHeadingExtractor,
    _HTMLTextExtractor,
)


@pytest.fixture
def document_loader():
    """Create a document loader instance for testing."""
    return DocumentLoader()


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document.\nIt has multiple lines.\n")
    yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def sample_markdown_file():
    """Create a sample markdown file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Document\n\nThis is a test markdown file.\n")
    yield Path(f.name)
    os.unlink(f.name)


def test_load_text_file(document_loader, sample_text_file):
    """Test loading a text file."""
    documents, metadata = document_loader.load_document(sample_text_file)

    assert isinstance(documents, list)
    assert len(documents) > 0
    assert isinstance(documents[0], Document)
    assert "test document" in documents[0].text.lower()

    assert isinstance(metadata, DocumentMetadata)
    assert metadata.file_path == str(sample_text_file)
    assert metadata.file_type == ".txt"
    assert metadata.processing_status == "success"


def test_load_markdown_file(document_loader, sample_markdown_file):
    """Test loading a markdown file."""
    documents, metadata = document_loader.load_document(sample_markdown_file)

    assert isinstance(documents, list)
    assert len(documents) > 0
    assert isinstance(documents[0], Document)
    assert "test document" in documents[0].text.lower()

    assert isinstance(metadata, DocumentMetadata)
    assert metadata.file_path == str(sample_markdown_file)
    assert metadata.file_type == ".md"
    assert metadata.processing_status == "success"


def test_duplicate_detection(document_loader, sample_text_file):
    """Test duplicate file detection."""
    # Load file first time
    documents1, metadata1 = document_loader.load_document(sample_text_file)
    assert len(documents1) > 0

    # Load same file again
    documents2, metadata2 = document_loader.load_document(sample_text_file)
    assert len(documents2) == 0  # Should be empty due to duplicate detection
    assert metadata2.file_hash == metadata1.file_hash


def test_invalid_file_format(document_loader):
    """Test handling of invalid file format."""
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"test")

    with pytest.raises(ValueError, match="Unsupported file format"):
        document_loader.load_document(f.name)

    os.unlink(f.name)


def test_nonexistent_file(document_loader):
    """Test handling of nonexistent file."""
    with pytest.raises(ValueError, match="File not found"):
        document_loader.load_document("nonexistent.txt")


def test_large_file(document_loader):
    """Test handling of file exceeding size limit."""
    # Create a file larger than the size limit
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"x" * (DocumentLoader.MAX_FILE_SIZE + 1))

    with pytest.raises(ValueError, match="File too large"):
        document_loader.load_document(f.name)

    os.unlink(f.name)


def test_corrupted_file(document_loader):
    """Test handling of corrupted file."""
    # Create a corrupted PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"Not a valid PDF file")

    with pytest.raises(OSError, match="Error processing file"):
        document_loader.load_document(f.name)

    os.unlink(f.name)


# --- HTML loading tests ---


@pytest.fixture
def sample_html_file():
    """Create a sample HTML file with headings and content."""
    content = """<!DOCTYPE html>
<html><head><title>Test</title></head>
<body>
<h1>Main Title</h1>
<p>First paragraph with content.</p>
<h2>Section One</h2>
<p>Some section content.</p>
<h3>Subsection</h3>
<p>More details here.</p>
</body></html>"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(content)
    yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def empty_html_file():
    """Create an HTML file with no text content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write("<html><body></body></html>")
    yield Path(f.name)
    os.unlink(f.name)


def test_load_html_file(document_loader, sample_html_file):
    """As a user I want to ingest HTML files, so I can include web content in my RAG pipeline.
    Technical: HtmlProcessor extracts text, metadata includes headings."""
    documents, metadata = document_loader.load_document(sample_html_file)

    assert len(documents) == 1
    assert "First paragraph" in documents[0].text
    assert "Main Title" in documents[0].text
    assert metadata.file_type == ".html"
    assert metadata.processing_status == "success"
    assert "Main Title" in metadata.section_headings
    assert "Section One" in metadata.section_headings
    assert "Subsection" in metadata.section_headings


def test_load_empty_html_file(document_loader, empty_html_file):
    """As a user I want empty HTML files handled gracefully.
    Technical: HtmlProcessor returns placeholder text for empty content."""
    documents, metadata = document_loader.load_document(empty_html_file)

    assert len(documents) == 1
    assert "No text content" in documents[0].text
    assert metadata.processing_status == "success"


def test_html_text_extractor():
    """Test _HTMLTextExtractor strips tags and extracts text."""
    extractor = _HTMLTextExtractor()
    extractor.feed("<p>Hello <b>world</b></p><div>More text</div>")
    assert "Hello" in extractor.get_text()
    assert "world" in extractor.get_text()
    assert "More text" in extractor.get_text()
    assert "<p>" not in extractor.get_text()


def test_html_heading_extractor():
    """Test _HTMLHeadingExtractor finds h1-h6 tags."""
    extractor = _HTMLHeadingExtractor()
    extractor.feed("<h1>Title</h1><p>text</p><h2>Subtitle</h2><h6>Deep</h6>")
    assert extractor.headings == ["Title", "Subtitle", "Deep"]


def test_html_heading_extractor_empty():
    """Test _HTMLHeadingExtractor with no headings."""
    extractor = _HTMLHeadingExtractor()
    extractor.feed("<p>Just a paragraph</p>")
    assert extractor.headings == []


# --- Metadata extraction tests ---


def test_creation_date_extracted(document_loader, sample_text_file):
    """As a user I want document creation dates, so I can filter by recency.
    Technical: _extract_creation_date returns ISO date from file mtime."""
    _, metadata = document_loader.load_document(sample_text_file)
    assert metadata.creation_date is not None
    # Should be ISO format YYYY-MM-DD
    assert len(metadata.creation_date) == 10
    assert metadata.creation_date[4] == "-"
    assert metadata.creation_date[7] == "-"


def test_markdown_section_headings(document_loader):
    """As a user I want section headings extracted from Markdown.
    Technical: _extract_section_headings parses # heading lines."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Main Heading\n\nContent.\n\n## Sub Heading\n\nMore content.\n")
    try:
        _, metadata = document_loader.load_document(f.name)
        assert "Main Heading" in metadata.section_headings
        assert "Sub Heading" in metadata.section_headings
    finally:
        os.unlink(f.name)


def test_duplicate_detection_different_params(document_loader, sample_text_file):
    """As a user I want to reprocess a file with different parameters.
    Technical: different params_key bypasses file-level dedup."""
    docs1, _ = document_loader.load_document(sample_text_file, params_key="set_a")
    assert len(docs1) > 0

    # Same file, different params_key should NOT be treated as duplicate
    docs2, _ = document_loader.load_document(sample_text_file, params_key="set_b")
    assert len(docs2) > 0


def test_htm_extension_supported(document_loader):
    """Test that .htm extension is handled same as .html."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False, encoding="utf-8") as f:
        f.write("<html><body><p>HTM content</p></body></html>")
    try:
        documents, metadata = document_loader.load_document(f.name)
        assert len(documents) == 1
        assert "HTM content" in documents[0].text
        assert metadata.file_type == ".htm"
    finally:
        os.unlink(f.name)
