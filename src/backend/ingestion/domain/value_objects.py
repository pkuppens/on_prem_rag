"""Domain value objects for the Ingestion Bounded Context.

Defines the core types that flow through the ingestion pipeline:
- IngestionDocument: domain replacement for LlamaIndex Document
- Chunk: a single chunk of text with metadata
- ChunkMetadata: metadata about a chunk
- FileContentHash: value object for SHA-256 content hash
- IngestionResult: result of an ingestion operation
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngestionDocument:
    """Domain document — replaces direct LlamaIndex ``Document`` dependency.

    This is the core domain type for the ingestion pipeline. All infrastructure
    adapters (document loaders, chunkers) work with this type. The LlamaIndex
    ``Document`` type is only used inside infrastructure adapters that interface
    with LlamaIndex readers/parsers.
    """

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_text(cls, text: str, **metadata: Any) -> IngestionDocument:
        """Create an IngestionDocument from plain text with optional metadata."""
        return cls(text=text, metadata=metadata)

    @property
    def content(self) -> str:
        """Return the text content."""
        return self.text

    @content.setter
    def content(self, value: str) -> None:
        self.text = value


@dataclass
class Chunk:
    """A single chunk of text produced by the chunking pipeline.

    Attributes:
        text: The chunk text content.
        chunk_index: Sequential index within the document.
        document_id: Stable document identifier.
        document_name: Source filename.
        page_number: Sequential page number (1-based).
        page_label: PDF internal page label.
        source: Original file path.
        content_hash: SHA-256 of the chunk text.
        metadata: Additional metadata keys.
        is_empty: Whether this is an empty placeholder chunk.
    """

    text: str
    chunk_index: int = 0
    document_id: str = ""
    document_name: str = ""
    page_number: int | None = None
    page_label: str | None = None
    source: str = ""
    content_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    is_empty: bool = False

    @classmethod
    def from_text(cls, text: str, **metadata: Any) -> Chunk:
        """Create a Chunk from plain text with optional metadata."""
        return cls(text=text, metadata=metadata)


@dataclass
class ChunkMetadata:
    """Metadata for a single chunk — serializable form for storage."""

    chunk_index: int
    document_id: str
    document_name: str
    page_number: int | None = None
    page_label: str | None = None
    source: str = ""
    content_hash: str = ""


@dataclass
class FileContentHash:
    """Value object representing a SHA-256 content hash."""

    value: str

    def __init__(self, data: bytes | str) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8", errors="replace")
        self.value = hashlib.sha256(data).hexdigest()

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FileContentHash):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class IngestionResult:
    """Result of a single document ingestion operation."""

    chunks_processed: int = 0
    records_stored: int = 0
    was_duplicate: bool = False
    file_name: str = ""
    error: str | None = None
    success: bool = True
