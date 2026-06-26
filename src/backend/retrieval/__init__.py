"""Retrieval Bounded Context.

Provides similarity search over embedded chunks: dense, sparse (BM25), hybrid,
with re-ranking and MMR. Depends on the LLM Gateway for embedding query encoding.

See docs/technical/DDD_TARGET_ARCHITECTURE.md#22-retrieval-bc for design.
"""

from __future__ import annotations

from backend.retrieval.application.reranking import CrossEncoderReranker
from backend.retrieval.application.search_service import (
    RetrievalService,
    create_retrieval_service,
)
from backend.retrieval.domain.interfaces import IVectorStoreRead
from backend.retrieval.domain.services import (
    BM25SparseRetriever,
    DenseRetriever,
    HybridRetriever,
    QueryEmbeddingsDenseRetriever,
    SparseRetriever,
    _cosine_similarity,
    _reciprocal_rank_fusion,
    mmr_rerank,
)
from backend.retrieval.domain.value_objects import RetrievalStrategy, SearchResult
from backend.retrieval.infrastructure.bm25_store import BM25Store
from backend.retrieval.infrastructure.vector_store_config import VectorStoreConfig

__all__ = [
    # Value objects
    "RetrievalStrategy",
    "SearchResult",
    # Port interfaces
    "IVectorStoreRead",
    # Domain services
    "DenseRetriever",
    "QueryEmbeddingsDenseRetriever",
    "SparseRetriever",
    "BM25SparseRetriever",
    "HybridRetriever",
    "CrossEncoderReranker",
    "mmr_rerank",
    # Application services
    "RetrievalService",
    "create_retrieval_service",
    # Infrastructure
    "BM25Store",
    "VectorStoreConfig",
    # Internal helpers (used by tests)
    "_cosine_similarity",
    "_reciprocal_rank_fusion",
]
