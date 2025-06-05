"""Tests for the document loader module."""

import os
import tempfile
from pathlib import Path

import pytest
from llama_index.core import Document

from rag_pipeline.core.document_loader import DocumentLoader, DocumentMetadata


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
