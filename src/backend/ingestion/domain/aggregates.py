"""Aggregate root for the Ingestion Bounded Context.

The IngestionJob aggregate tracks a document processing lifecycle
from upload through chunking, embedding, and storage.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IngestionStatus(str, Enum):
    """Lifecycle states for an IngestionJob."""

    PENDING = "pending"
    LOADING = "loading"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class IngestionJob:
    """Aggregate root tracking document processing lifecycle.

    An IngestionJob represents the processing of a single file from upload
    through chunking, embedding, and storage in the vector store.
    """

    file_name: str
    file_path: str = ""
    status: IngestionStatus = IngestionStatus.PENDING

    file_size: int = 0
    file_hash: str = ""
    total_chunks: int = 0
    records_stored: int = 0
    error_message: str | None = None

    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def start_loading(self) -> None:
        """Transition to loading state."""
        self.status = IngestionStatus.LOADING
        self.updated_at = time.time()

    def start_chunking(self) -> None:
        """Transition to chunking state."""
        self.status = IngestionStatus.CHUNKING
        self.updated_at = time.time()

    def start_embedding(self) -> None:
        """Transition to embedding state."""
        self.status = IngestionStatus.EMBEDDING
        self.updated_at = time.time()

    def start_storing(self) -> None:
        """Transition to storing state."""
        self.status = IngestionStatus.STORING
        self.updated_at = time.time()

    def complete(self, total_chunks: int, records_stored: int) -> None:
        """Mark the job as completed."""
        self.status = IngestionStatus.COMPLETED
        self.total_chunks = total_chunks
        self.records_stored = records_stored
        self.updated_at = time.time()

    def fail(self, error_message: str) -> None:
        """Mark the job as failed."""
        self.status = IngestionStatus.FAILED
        self.error_message = error_message
        self.updated_at = time.time()

    def cancel(self) -> None:
        """Cancel the job."""
        self.status = IngestionStatus.CANCELLED
        self.updated_at = time.time()

    @property
    def is_terminal(self) -> bool:
        """Check if the job has reached a terminal state."""
        return self.status in (
            IngestionStatus.COMPLETED,
            IngestionStatus.FAILED,
            IngestionStatus.CANCELLED,
        )

    @property
    def progress_pct(self) -> float:
        """Return progress as a 0.0-1.0 value."""
        mapping = {
            IngestionStatus.PENDING: 0.0,
            IngestionStatus.LOADING: 0.1,
            IngestionStatus.CHUNKING: 0.4,
            IngestionStatus.EMBEDDING: 0.7,
            IngestionStatus.STORING: 0.9,
            IngestionStatus.COMPLETED: 1.0,
            IngestionStatus.FAILED: 1.0,
            IngestionStatus.CANCELLED: 1.0,
        }
        return mapping.get(self.status, 0.0)
