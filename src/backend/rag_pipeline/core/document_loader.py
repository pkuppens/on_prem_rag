"""Document loader module for handling various file formats and preprocessing.

Project References:
- Feature: FEAT-001 (Technical Foundation & MVP)
- Story: STORY-002 (Document Processing Pipeline)
- Task: TASK-006 (Implement robust file ingestion module)
  - [✓] Idempotent document loading with duplicate detection
  - [✓] File validation and preprocessing pipeline
  - [✓] LlamaIndex document loaders with error handling
  - [✓] Support PDF, DOCX, MD, TXT, and HTML file types
  - [ ] Advanced chunking and embedding system (TASK-007)
  - [ ] Document obsoletion/invalidation (TASK-007)

This module is part of the core RAG (Retrieval-Augmented Generation) pipeline,
addressing the following business needs:

1. Data Privacy & Compliance
   - Zero cloud dependencies for document processing
   - Complete data sovereignty for sensitive information
   - Compliance with GDPR, HIPAA, and other regulations

2. Cost Control & Efficiency
   - Eliminate per-query API costs
   - Predictable resource usage
   - Efficient document processing

3. Operational Independence
   - No internet dependency for core functionality
   - Reliable document processing pipeline
   - Robust error handling and recovery

Features:
[✓] Core Document Processing
    - Support for PDF, DOCX, MD, TXT, and HTML files
    - File validation and size limits
    - Duplicate detection using SHA-256 hashing
    - Error handling and logging

[✓] Document Metadata
    - File path and type tracking
    - File size and hash information
    - Processing status and error messages
    - Page count for PDF documents

[ ] Planned Enhancements (TASK-007)
    - Document versioning and history
    - Validity periods (valid_at, invalid_at)
    - Access control integration
    - Document obsoletion/invalidation
    - Batch processing optimization
    - Progress tracking and resumability

This module is part of FEAT-001 (Technical Foundation & MVP) and supports
FEAT-002 (Enterprise User Interface) for document upload capabilities.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from html.parser import HTMLParser
from pathlib import Path

# Import from LlamaIndex lazily to allow tests to run without optional deps
# Removing this could be the cause for failing test_embedding_shapes.py tests
Document = object
SimpleDirectoryReader = object
DocxReader = MarkdownReader = PDFReader = None
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Template interface for document processors."""

    @abstractmethod
    def load(self, file_path: Path) -> list[Document]:
        """Return Document objects for the given file."""


class PDFProcessor(BaseProcessor):
    def __init__(self) -> None:
        global PDFReader
        from llama_index.readers.file import PDFReader

        self.reader = PDFReader()

    def load(self, file_path: Path) -> list[Document]:
        return self.reader.load_data(file_path)


class DocxProcessor(BaseProcessor):
    def __init__(self) -> None:
        global DocxReader
        from llama_index.readers.file import DocxReader

        self.reader = DocxReader()

    def load(self, file_path: Path) -> list[Document]:
        return self.reader.load_data(file_path)


class MarkdownProcessor(BaseProcessor):
    def __init__(self) -> None:
        global MarkdownReader
        from llama_index.readers.file import MarkdownReader

        self.reader = MarkdownReader()

    def load(self, file_path: Path) -> list[Document]:
        return self.reader.load_data(file_path)


class TextProcessor(BaseProcessor):
    def __init__(self) -> None:
        global SimpleDirectoryReader
        from llama_index.core import SimpleDirectoryReader

        self.reader_cls = SimpleDirectoryReader

    def load(self, file_path: Path) -> list[Document]:
        reader = self.reader_cls(input_files=[str(file_path)])
        return reader.load_data(file_path)


class _HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML, stripping tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)

    def get_text(self) -> str:
        return "".join(self.text_parts)


class HtmlProcessor(BaseProcessor):
    """Load HTML files and extract text content for RAG ingestion."""

    def load(self, file_path: Path) -> list[Document]:
        global Document
        from llama_index.core import Document

        content = file_path.read_text(encoding="utf-8", errors="replace")
        extractor = _HTMLTextExtractor()
        extractor.feed(content)
        text = extractor.get_text().strip()
        if not text:
            text = "(No text content extracted from HTML)"
        return [Document(text=text, metadata={"file_path": str(file_path)})]


class DocumentMetadata(BaseModel):
    """Metadata for a processed document.

    This class can be extended with additional fields for future features such as:
    - Validity periods (valid_at, invalid_at)
    - Creation and modification timestamps
    - Access control information
    - Document versioning
    """

    file_path: str
    file_hash: str
    file_type: str
    file_size: int
    num_pages: int | None = None
    processing_status: str = "success"
    error_message: str | None = None


class DocumentLoader:
    """Handles loading and preprocessing of various document formats."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html", ".htm"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self) -> None:
        """Initialize the document loader with document processors."""
        self.processed_files: set[tuple[str, str]] = set()
        self._setup_processors()

    def _setup_processors(self) -> None:
        """Set up processors for different file types."""
        global Document
        from llama_index.core import Document

        self.processors = {
            ".pdf": PDFProcessor(),
            ".docx": DocxProcessor(),
            ".md": MarkdownProcessor(),
            ".txt": TextProcessor(),
            ".html": HtmlProcessor(),
            ".htm": HtmlProcessor(),
        }

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file for duplicate detection."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _validate_file(self, file_path: Path) -> tuple[bool, str | None]:
        """Validate file format and size."""
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file format: {file_path.suffix}"

        if file_path.stat().st_size > self.MAX_FILE_SIZE:
            return False, f"File too large: {file_path.stat().st_size} bytes"

        return True, None

    def _get_metadata(self, file_path: Path, file_hash: str) -> DocumentMetadata:
        """Create metadata object for a document."""
        return DocumentMetadata(
            file_path=str(file_path),
            file_hash=file_hash,
            file_type=file_path.suffix.lower(),
            file_size=file_path.stat().st_size,
        )

    def load_document(self, file_path: str | Path, *, params_key: str = "default") -> tuple[list[Document], DocumentMetadata]:
        """Load a document and return its content and metadata.

        Args:
            file_path: Path to the document file
            params_key: Identifier for the parameter set used

        Returns:
            Tuple of (list of Document objects, DocumentMetadata)

        Raises:
            OSError: If file cannot be loaded or processed
        """
        file_path = Path(file_path)

        # Validate file
        is_valid, error_msg = self._validate_file(file_path)
        if not is_valid:
            raise ValueError(error_msg)

        # Check for duplicate files using file hash + parameter key
        file_hash = self._compute_file_hash(file_path)
        dedup_key = (file_hash, params_key)
        if dedup_key in self.processed_files:
            logger.debug(f"Skipping duplicate file: {file_path} ({params_key})")
            return [], self._get_metadata(file_path, file_hash)

        try:
            # Get appropriate processor
            processor = self.processors[file_path.suffix.lower()]
            documents = processor.load(file_path)

            # Update metadata
            metadata = self._get_metadata(file_path, file_hash)
            if file_path.suffix.lower() == ".pdf":
                metadata.num_pages = len(documents)
            elif file_path.suffix.lower() == ".docx":
                # For DOCX, we use paragraphs as the basic unit
                metadata.num_pages = len(documents)

            # Mark as processed
            self.processed_files.add(dedup_key)

            logger.info(f"Successfully loaded document: {file_path}")
            return documents, metadata

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            metadata = self._get_metadata(file_path, file_hash)
            metadata.processing_status = "error"
            metadata.error_message = error_msg
            raise OSError(error_msg) from e
