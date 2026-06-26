"""Domain events for the Ingestion Bounded Context.

Events follow the ``past-tense`` naming convention common in DDD.
They are immutable dataclasses carrying the minimum context needed
for event handlers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentLoaded:
    """Published when a file has been loaded into documents."""

    file_name: str
    file_path: str
    file_hash: str
    page_count: int
    file_size: int
    timestamp: float = time.time()


@dataclass(frozen=True)
class ChunkingCompleted:
    """Published when chunking finishes for a document."""

    file_name: str
    file_path: str
    total_chunks: int
    chunks_filtered: int
    pages_processed: int
    timestamp: float = time.time()


@dataclass(frozen=True)
class EmbeddingCompleted:
    """Published when embeddings have been generated."""

    file_name: str
    file_path: str
    embeddings_count: int
    model_name: str
    timestamp: float = time.time()


@dataclass(frozen=True)
class IngestionFinished:
    """Published when the full ingestion pipeline completes."""

    file_name: str
    file_path: str
    total_chunks: int
    records_stored: int
    success: bool
    error: str | None = None
    timestamp: float = time.time()


@dataclass(frozen=True)
class DuplicateSkipped:
    """Published when a document is skipped due to content hash match."""

    file_name: str
    file_hash: str
    timestamp: float = time.time()
