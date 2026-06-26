"""Domain services for retrieval strategies: dense, sparse, hybrid, RRF, MMR.

DenseRetriever and SparseRetriever are abstract ports. Concrete implementations
live in the application layer or are wired via dependency injection.

See docs/technical/DDD_TARGET_ARCHITECTURE.md#22-retrieval-bc for design.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.retrieval.domain.interfaces import (
    EmbeddingProvider,
    IVectorStoreRead,
)

logger = StructuredLogger(__name__)


class DenseRetriever(ABC):
    """Abstract dense (embedding-based) retriever port."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Retrieve top_k chunks for query using dense similarity."""
        ...


class QueryEmbeddingsDenseRetriever(DenseRetriever):
    """Dense retriever using EmbeddingProvider port and IVectorStoreRead.

    Replaces the old implementation that called query_embeddings() directly.
    Now depends on abstractions from both LLM Gateway (EmbeddingProvider) and
    Retrieval (IVectorStoreRead), respecting bounded context boundaries.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: IVectorStoreRead,
    ) -> None:
        """Initialize with port dependencies.

        Args:
            embedding_provider: Port for query embedding generation.
            vector_store: Read-only vector store port.
        """
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Retrieve chunks using embedding + vector search."""
        query_embedding = self._embedding_provider.get_text_embedding(query)
        return self._vector_store.search(query_embedding, top_k=top_k)


class SparseRetriever(ABC):
    """Abstract sparse (keyword/BM25) retriever port."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Retrieve top_k chunks for query using sparse retrieval."""
        ...


class BM25SparseRetriever(SparseRetriever):
    """BM25 sparse retriever using BM25Store."""

    def __init__(self, bm25_store: Any) -> None:
        """Initialize with a BM25Store instance.

        Args:
            bm25_store: A BM25Store or compatible sparse index.
        """
        self._store = bm25_store

    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        return self._store.query(query, top_k=top_k)


def _reciprocal_rank_fusion(ranked_lists: list[list[dict[str, Any]]], k: int = 60) -> list[dict[str, Any]]:
    """Merge ranked lists using Reciprocal Rank Fusion (RRF).

    RRF score = sum(1 / (k + rank)) for each occurrence across lists.
    """
    rrf_scores: dict[str, tuple[float, dict[str, Any]]] = {}

    for lst in ranked_lists:
        for rank, item in enumerate(lst):
            record_id = str(item.get("record_id", id(item)))
            if record_id not in rrf_scores:
                rrf_scores[record_id] = (0.0, item)
            old_score, _ = rrf_scores[record_id]
            rrf_scores[record_id] = (
                old_score + 1.0 / (k + rank + 1),
                rrf_scores[record_id][1],
            )

    sorted_items = sorted(rrf_scores.values(), key=lambda x: -x[0])
    results = []
    max_s = sorted_items[0][0] if sorted_items else 1.0
    min_s = sorted_items[-1][0] if sorted_items else 0.0
    norm = (max_s - min_s) or 1.0

    for score, item in sorted_items:
        copy = dict(item)
        # When all items have the same RRF score (e.g. single chunk), norm
        # makes score 0. Use 1.0 for tied top results so they pass
        # similarity_threshold.
        if norm <= 0 or max_s == min_s:
            copy["similarity_score"] = 1.0
        else:
            copy["similarity_score"] = min(1.0, max(0.0, (score - min_s) / norm))
        results.append(copy)

    return results


class HybridRetriever:
    """Combines dense and sparse retrieval via RRF."""

    def __init__(
        self,
        dense: DenseRetriever,
        sparse: SparseRetriever,
        alpha: float = 0.5,
    ) -> None:
        """Initialize hybrid retriever.

        Args:
            dense: Dense retriever implementation.
            sparse: Sparse retriever implementation.
            alpha: Not used when using RRF; kept for API compatibility.
        """
        self.dense = dense
        self.sparse = sparse
        self.alpha = alpha

    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Retrieve using RRF merge of dense and sparse results."""
        dense_results = self.dense.retrieve(query, top_k=top_k * 2)
        sparse_results = self.sparse.retrieve(query, top_k=top_k * 2)
        merged = _reciprocal_rank_fusion([dense_results, sparse_results])
        return merged[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def mmr_rerank(
    candidates: list[dict[str, Any]],
    query_embedding: list[float],
    embedding_fn: Any,
    lambda_param: float = 0.7,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Re-rank candidates for diversity using Maximal Marginal Relevance.

    MMR score = λ * relevance - (1-λ) * max_similarity_to_selected.

    Args:
        candidates: List of chunks with "text" key.
        query_embedding: Query embedding vector.
        embedding_fn: Callable that takes text and returns embedding
            (list[float]).
        lambda_param: Balance relevance (high) vs diversity (low).
        top_k: Number of results to return.

    Returns:
        Re-ranked list of candidates.
    """
    if not candidates or top_k <= 0:
        return []

    # Pre-compute candidate embeddings to avoid repeated calls
    cand_embeddings = [embedding_fn(c.get("text", "")) for c in candidates]

    selected: list[dict[str, Any]] = []
    selected_embeddings: list[list[float]] = []
    remaining = list(candidates)
    remaining_embeddings = list(cand_embeddings)

    while len(selected) < top_k and remaining:
        best_score = float("-inf")
        best_idx = 0

        for i in range(len(remaining)):
            rel = _cosine_similarity(query_embedding, remaining_embeddings[i])
            if not selected:
                mmr = rel
            else:
                max_sim = max(_cosine_similarity(selected_embeddings[j], remaining_embeddings[i]) for j in range(len(selected)))
                mmr = lambda_param * rel - (1 - lambda_param) * max_sim

            if mmr > best_score:
                best_score = mmr
                best_idx = i

        chosen = remaining.pop(best_idx)
        chosen_emb = remaining_embeddings.pop(best_idx)
        chosen["similarity_score"] = min(1.0, max(0.0, best_score))
        selected.append(chosen)
        selected_embeddings.append(chosen_emb)

    return selected
