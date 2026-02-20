"""Metrics API endpoint for the RAG pipeline.

Exposes ingestion stats, query counts, and index size for observability.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import APIRouter

from ..core.vector_store import get_vector_store_manager
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)

router = APIRouter(tags=["metrics"])


@dataclass
class PipelineMetrics:
    """In-memory metrics for the RAG pipeline."""

    documents_ingested: int = 0
    queries_total: int = 0
    _last_ingestion_timestamp_ms: float = 0

    def record_ingestion(self) -> None:
        """Record a completed document ingestion."""
        self.documents_ingested += 1
        self._last_ingestion_timestamp_ms = time.time() * 1000

    def record_query(self) -> None:
        """Record a query."""
        self.queries_total += 1

    @property
    def last_ingestion_timestamp_ms(self) -> float:
        """Timestamp of last ingestion (ms since epoch)."""
        return self._last_ingestion_timestamp_ms


# Module-level singleton
_metrics = PipelineMetrics()


def get_metrics() -> PipelineMetrics:
    """Return the shared metrics instance."""
    return _metrics


def _get_index_chunk_count() -> int:
    """Get approximate chunk count from vector store (best effort)."""
    try:
        vsm = get_vector_store_manager()
        return vsm.get_chunk_count()
    except Exception as e:
        logger.warning("Could not get index chunk count", error=str(e))
    return 0


@router.get("/metrics")
async def get_pipeline_metrics() -> dict:
    """Return pipeline metrics for observability.

    Returns:
        JSON with documents_ingested, queries_total, index_chunks, last_ingestion_timestamp_ms.
    """
    m = get_metrics()
    index_chunks = _get_index_chunk_count()
    return {
        "documents_ingested": m.documents_ingested,
        "queries_total": m.queries_total,
        "index_chunks": index_chunks,
        "last_ingestion_timestamp_ms": m.last_ingestion_timestamp_ms,
    }
