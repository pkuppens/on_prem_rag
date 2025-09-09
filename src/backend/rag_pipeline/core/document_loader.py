"""Document loader module for handling various file formats and preprocessing.

Project References:
- Feature: FEAT-001 (Technical Foundation & MVP)
- Story: STORY-002 (Document Processing Pipeline)
- Task: TASK-006 (Implement robust file ingestion module)
  - [✓] Idempotent document loading with duplicate detection
  - [✓] File validation and preprocessing pipeline
  - [✓] LlamaIndex document loaders with error handling
  - [✓] Support PDF, DOCX, MD, and TXT file types
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
    - Support for PDF, DOCX, MD, and TXT files
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
from pathlib import Path
from typing import Any

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

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}
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
        }

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file for duplicate detection.

        Args:
            file_path: Path to the file to hash

        Returns:
            SHA-256 hash as hexadecimal string

        Raises:
            OSError: If file cannot be read or accessed
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    if not byte_block:  # End of file
                        break
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except PermissionError as e:
            raise OSError(f"Permission denied while computing hash for {file_path}: {str(e)}") from e
        except OSError as e:
            raise OSError(f"Cannot read file for hash computation {file_path}: {str(e)}") from e
        except Exception as e:
            raise OSError(f"Unexpected error computing hash for {file_path}: {str(e)}") from e

    def _validate_file(self, file_path: Path) -> tuple[bool, str | None]:
        """Validate file format, size, and permissions.

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            # Check if path is a file (not directory or symlink)
            if not file_path.is_file():
                if file_path.is_dir():
                    return False, f"Path is a directory, not a file: {file_path}"
                elif file_path.is_symlink():
                    return False, f"Path is a symbolic link, not a file: {file_path}"
                else:
                    return False, f"Path is not a regular file: {file_path}"

            # Check file extension
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                return (
                    False,
                    f"Unsupported file format: {file_path.suffix}. Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                )

            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size == 0:
                    return False, f"File is empty: {file_path}"
                if file_size > self.MAX_FILE_SIZE:
                    return False, f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE} bytes)"
            except OSError as e:
                return False, f"Cannot access file size: {str(e)}"

            # Check read permissions
            try:
                with open(file_path, "rb") as f:
                    # Try to read first byte to verify read access
                    f.read(1)
            except PermissionError:
                return False, f"Permission denied: cannot read file {file_path}"
            except OSError as e:
                return False, f"Cannot read file: {str(e)}"

            return True, None

        except Exception as e:
            return False, f"Unexpected error during file validation: {str(e)}"

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
            ValueError: If file validation fails
            OSError: If file cannot be loaded or processed
            RuntimeError: If document processing fails
        """
        file_path = Path(file_path)
        logger.debug(f"Loading document: {file_path} with params_key: {params_key}")

        # Validate file
        is_valid, error_msg = self._validate_file(file_path)
        if not is_valid:
            logger.warning(f"File validation failed: {error_msg}")
            raise ValueError(error_msg)

        # Check for duplicate files using file hash + parameter key
        try:
            file_hash = self._compute_file_hash(file_path)
            dedup_key = (file_hash, params_key)
            if dedup_key in self.processed_files:
                logger.debug(f"Skipping duplicate file: {file_path} ({params_key})")
                return [], self._get_metadata(file_path, file_hash)
        except OSError as e:
            logger.error(f"Failed to compute file hash: {str(e)}")
            raise

        try:
            # Get appropriate processor
            file_extension = file_path.suffix.lower()
            if file_extension not in self.processors:
                raise RuntimeError(f"No processor available for file type: {file_extension}")

            processor = self.processors[file_extension]
            logger.debug(f"Using processor: {type(processor).__name__} for {file_extension}")

            # Load documents with processor-specific error handling
            try:
                documents = processor.load(file_path)
                if not documents:
                    logger.warning(f"Processor returned no documents for: {file_path}")
                    documents = []
            except Exception as e:
                raise RuntimeError(f"Processor failed to load {file_path}: {str(e)}") from e

            # Update metadata
            metadata = self._get_metadata(file_path, file_hash)
            metadata.processing_status = "completed"

            # Set page count based on document type
            if file_extension == ".pdf":
                metadata.num_pages = len(documents)
            elif file_extension == ".docx":
                # For DOCX, we use paragraphs as the basic unit
                metadata.num_pages = len(documents)
            elif file_extension in [".txt", ".md"]:
                # For text files, don't set page count (None)
                metadata.num_pages = None

            # Mark as processed
            self.processed_files.add(dedup_key)

            logger.info(f"Successfully loaded document: {file_path} ({len(documents)} documents, {metadata.num_pages} pages)")
            return documents, metadata

        except (ValueError, OSError):
            # Re-raise validation and file system errors as-is
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing file {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Create error metadata
            try:
                metadata = self._get_metadata(file_path, file_hash)
                metadata.processing_status = "error"
                metadata.error_message = error_msg
            except Exception as meta_error:
                logger.error(f"Failed to create error metadata: {str(meta_error)}")
                # Create minimal metadata
                metadata = DocumentMetadata(
                    file_path=str(file_path),
                    file_hash="unknown",
                    file_type=file_path.suffix.lower(),
                    file_size=0,
                    processing_status="error",
                    error_message=error_msg,
                )

            raise OSError(error_msg) from e
