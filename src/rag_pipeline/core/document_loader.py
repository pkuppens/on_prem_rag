"""Document loader module for handling various file formats and preprocessing."""

import hashlib
import logging
from pathlib import Path

from llama_index.core import Document
from llama_index.readers.file import (
    DocxReader,
    MarkdownReader,
    PDFReader,
    SimpleDirectoryReader,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentMetadata(BaseModel):
    """Metadata for a processed document."""

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

    def __init__(self):
        """Initialize the document loader with necessary readers."""
        self.processed_files: set[str] = set()
        self._setup_readers()

    def _setup_readers(self) -> None:
        """Set up document readers for different file types."""
        self.readers = {
            ".pdf": PDFReader(),
            ".docx": DocxReader(),
            ".md": MarkdownReader(),
            ".txt": SimpleDirectoryReader(),
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
        """Create metadata for the document."""
        return DocumentMetadata(
            file_path=str(file_path),
            file_hash=file_hash,
            file_type=file_path.suffix.lower(),
            file_size=file_path.stat().st_size,
        )

    def load_document(self, file_path: str | Path) -> tuple[list[Document], DocumentMetadata]:
        """Load and preprocess a document.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (list of Document objects, DocumentMetadata)

        Raises:
            ValueError: If file validation fails
            IOError: If file cannot be read
        """
        file_path = Path(file_path)

        # Validate file
        is_valid, error_msg = self._validate_file(file_path)
        if not is_valid:
            raise ValueError(error_msg)

        # Check for duplicates
        file_hash = self._compute_file_hash(file_path)
        if file_hash in self.processed_files:
            logger.info(f"Skipping duplicate file: {file_path}")
            return [], self._get_metadata(file_path, file_hash)

        try:
            # Get appropriate reader
            reader = self.readers[file_path.suffix.lower()]

            # Load document
            documents = reader.load_data(file_path)

            # Update metadata
            metadata = self._get_metadata(file_path, file_hash)
            if file_path.suffix.lower() == ".pdf":
                metadata.num_pages = len(documents)

            # Mark as processed
            self.processed_files.add(file_hash)

            logger.info(f"Successfully loaded document: {file_path}")
            return documents, metadata

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            metadata = self._get_metadata(file_path, file_hash)
            metadata.processing_status = "error"
            metadata.error_message = error_msg
            raise OSError(error_msg) from e
