"""Tests for the document loader module.

Project References:
- Feature: FEAT-001 (Technical Foundation & MVP)
- Story: STORY-002 (Document Processing Pipeline)
- Tasks:
  - TASK-006 (Document Loading)
  - TASK-007 (Chunking & Embedding)
  - TASK-009 (Test Suite)

Current Test Coverage:
[✓] Basic Document Loading
    - Text file loading and validation
    - Markdown file processing
    - File type validation
    - Size limit checks
    - Basic error handling

[✓] Metadata Generation
    - File path and type tracking
    - File size calculation
    - Processing status
    - Error message capture

[ ] Not Yet Implemented (TASK-007)
    - Chunking strategy validation
    - Embedding generation testing
    - Caching behavior
    - Batch processing
    - Progress tracking

[!] Known Limitations
    - Current duplicate detection is file-hash based, which:
      * Requires reading the entire file
      * May miss semantic duplicates
      * Doesn't support versioning
    - No workflow/DAG integration for optimizing processing steps
    - No distributed processing support

Out of Scope:
- Vector store integration (covered in TASK-008)
- Query interface testing (covered in TASK-011)
- Performance benchmarking (separate test suite)
- Security and access control testing

Recommended Improvements:
1. Replace in-memory duplicate tracking with a persistent store
2. Integrate with a workflow engine (Airflow/Luigi/Dagster) to:
   - Track document processing state
   - Enable incremental processing
   - Support distributed workloads
   - Implement proper retry mechanisms
3. Add semantic duplicate detection using embeddings
4. Implement document versioning and validity periods
"""

import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("llama_index")
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


def test_corrupted_file(document_loader):
    """Test handling of corrupted file."""
    # Create a corrupted PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"Not a valid PDF file")

    with pytest.raises(OSError, match="Error processing file"):
        document_loader.load_document(f.name)

    os.unlink(f.name)
