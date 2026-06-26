"""Compatibility shim — delegates to ``ingestion.infrastructure.document_loader``.

This module previously contained the document loader implementation. The
implementation now lives in ``backend.ingestion.infrastructure.document_loader``
as part of the DDD bounded context extraction (Phase 3).

This shim wraps the new domain-based ``DocumentLoader`` to preserve the
old API (returning ``llama_index.core.Document`` objects).
"""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from pydantic import BaseModel

from backend.ingestion.infrastructure.document_loader import (  # noqa: F401
    HtmlProcessor,
    _HTMLHeadingExtractor,
    _HTMLTextExtractor,
)

logger = logging.getLogger(__name__)


# Re-export DocumentMetadata for backward compatibility
class DocumentMetadata(BaseModel):
    """Metadata for a processed document.

    This class can be extended with additional fields for future features such as:
    - Validity periods (valid_at, invalid_at)
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
    section_headings: list[str] = []
    creation_date: str | None = None  # ISO 8601 format (YYYY-MM-DD or full datetime)


class DocumentLoader:
    """Compatibility shim — converts domain ``IngestionDocument`` → LlamaIndex ``Document``.

    Wraps ``backend.ingestion.infrastructure.document_loader.DocumentLoader``
    and converts the returned domain documents back to ``llama_index.core.Document``
    objects for backward compatibility.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html", ".htm"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self) -> None:
        """Initialize the document loader compatibility shim."""
        from backend.ingestion.infrastructure.document_loader import (
            DocumentLoader as NewDocumentLoader,
        )

        self._inner = NewDocumentLoader()
        self.processed_files: set[tuple[str, str]] = set()

    def _to_llama_document(self, ing_doc: object) -> object:
        """Convert an ``IngestionDocument`` to a LlamaIndex ``Document``.

        Args:
            ing_doc: An ``IngestionDocument`` from the ingestion BC.

        Returns:
            A ``llama_index.core.Document``.
        """
        from llama_index.core import Document as LlamaDocument

        text = getattr(ing_doc, "text", "") or ""
        metadata = getattr(ing_doc, "metadata", {}) or {}
        return LlamaDocument(text=text, metadata=dict(metadata))

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

    def _extract_creation_date(self, file_path: Path) -> str | None:
        """Extract creation or modification date from file. Returns ISO 8601 date string."""
        try:
            if file_path.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader

                    reader = PdfReader(file_path)
                    if reader.metadata and reader.metadata.get("/CreationDate"):
                        raw = str(reader.metadata.get("/CreationDate", ""))
                        if raw.startswith("D:"):
                            raw = raw[2:]
                        if len(raw) >= 8:
                            return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                except Exception:  # noqa: S110
                    pass
            mtime = file_path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except Exception:  # noqa: S110
            return None

    def _extract_section_headings(self, documents: list, file_path: Path, file_type: str) -> list[str]:
        """Extract section headings from document content."""
        headings: list[str] = []
        try:
            if file_type in (".md", ".markdown"):
                content = file_path.read_text(encoding="utf-8", errors="replace")
                for match in re.finditer(r"^#{1,6}\s+(.+)$", content, re.MULTILINE):
                    headings.append(match.group(1).strip())
            elif file_type in (".html", ".htm"):
                content = file_path.read_text(encoding="utf-8", errors="replace")
                from backend.ingestion.infrastructure.document_loader import _HTMLHeadingExtractor

                extractor = _HTMLHeadingExtractor()
                extractor.feed(content)
                headings = extractor.headings
        except Exception:  # noqa: S110
            pass
        return headings

    def load_document(
        self,
        file_path: str | Path,
        *,
        params_key: str = "default",
    ) -> tuple[list[object], DocumentMetadata]:
        """Load a document and return its content and metadata.

        Delegates to the ingestion BC's document loader and converts
        domain ``IngestionDocument`` objects back to LlamaIndex ``Document``.

        Args:
            file_path: Path to the document file.
            params_key: Identifier for the parameter set used.

        Returns:
            Tuple of (list of LlamaIndex Document objects, DocumentMetadata).

        Raises:
            ValueError: If file validation fails.
            OSError: If file processing fails.
        """
        file_path = Path(file_path)

        # Validate file
        is_valid, error_msg = self._validate_file(file_path)
        if not is_valid:
            raise ValueError(error_msg)

        # Check for duplicate files
        file_hash = self._compute_file_hash(file_path)
        dedup_key = (file_hash, params_key)
        if dedup_key in self.processed_files:
            logger.debug(f"Skipping duplicate file: {file_path} ({params_key})")
            return [], self._get_metadata(file_path, file_hash)

        try:
            # Delegate to new domain-based loader
            ing_docs, ing_metadata = self._inner.load_document(file_path, params_key=params_key)

            # Convert domain documents to LlamaIndex Documents
            llama_docs = [self._to_llama_document(d) for d in ing_docs]

            # Build old-style metadata
            metadata = self._get_metadata(file_path, file_hash)
            if file_path.suffix.lower() == ".pdf":
                metadata.num_pages = len(ing_docs)
            elif file_path.suffix.lower() == ".docx":
                metadata.num_pages = len(ing_docs)

            metadata.creation_date = self._extract_creation_date(file_path)
            metadata.section_headings = self._extract_section_headings(llama_docs, file_path, file_path.suffix.lower())

            # Mark as processed
            self.processed_files.add(dedup_key)

            logger.info(f"Successfully loaded document: {file_path}")
            return llama_docs, metadata

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            metadata = self._get_metadata(file_path, file_hash)
            metadata.processing_status = "error"
            metadata.error_message = error_msg
            raise OSError(error_msg) from e
