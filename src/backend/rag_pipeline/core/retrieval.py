"""Compatibility shim — re-exports from ``backend.retrieval``.

All retrieval logic has been extracted to ``src/backend/retrieval/`` as part
of the DDD bounded context extraction (Phase 2). This file exists only for
backward compatibility during the migration.

See docs/technical/DDD_EXTRACTION_PLAN.md#phase-2-retrieval-bc-extraction.
"""

from __future__ import annotations

# Re-export all public retrieval symbols from the new bounded context
from backend.retrieval import (  # noqa: F401
    BM25SparseRetriever,
    CrossEncoderReranker,
    DenseRetriever,
    HybridRetriever,
    QueryEmbeddingsDenseRetriever,
    RetrievalService,
    SparseRetriever,
    _cosine_similarity,
    _reciprocal_rank_fusion,
    create_retrieval_service,
    mmr_rerank,
)
from backend.retrieval.infrastructure.bm25_store import BM25Store  # noqa: F401
from backend.retrieval.infrastructure.vector_store_config import (  # noqa: F401
    VectorStoreConfig,
)


class RetrievalResult(dict):
    """Single chunk result compatible with EmbeddingResult format."""

    pass
