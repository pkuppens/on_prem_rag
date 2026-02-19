"""Unified retrieval strategies: dense, sparse, hybrid, re-ranking, MMR.

Implements retrieval pipeline for RAG with configurable strategies.
See tmp/github/issue-plans/issue-79-hybrid-retrieval.md for design.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.rag_pipeline.config.vector_store import VectorStoreConfig
from backend.rag_pipeline.core.bm25_store import BM25Store
from backend.rag_pipeline.core.embeddings import query_embeddings
from backend.rag_pipeline.core.vector_store import VectorStoreManager

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class RetrievalResult(dict):
    """Single chunk result compatible with EmbeddingResult format."""

    pass


class DenseRetriever(ABC):
    """Abstract dense (embedding-based) retriever."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Retrieve top_k chunks for query using dense similarity."""
        ...


class QueryEmbeddingsDenseRetriever(DenseRetriever):
    """Dense retriever using existing query_embeddings and ChromaDB."""

    def __init__(
        self,
        model_name: str,
        persist_dir: str,
        collection_name: str = "documents",
    ) -> None:
        self.model_name = model_name
        self.persist_dir = persist_dir
        self.collection_name = collection_name

    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        result = query_embeddings(
            query=query,
            model_name=self.model_name,
            persist_dir=self.persist_dir,
            collection_name=self.collection_name,
            top_k=top_k,
        )
        return result.get("all_results", [])


class SparseRetriever(ABC):
    """Abstract sparse (keyword/BM25) retriever."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Retrieve top_k chunks for query using sparse retrieval."""
        ...


class BM25SparseRetriever(SparseRetriever):
    """BM25 sparse retriever using BM25Store."""

    def __init__(self, config: VectorStoreConfig) -> None:
        self._store = BM25Store(config)

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
            rrf_scores[record_id] = (old_score + 1.0 / (k + rank + 1), rrf_scores[record_id][1])

    sorted_items = sorted(rrf_scores.values(), key=lambda x: -x[0])
    results = []
    max_s = sorted_items[0][0] if sorted_items else 1.0
    min_s = sorted_items[-1][0] if sorted_items else 0.0
    norm = (max_s - min_s) or 1.0

    for score, item in sorted_items:
        copy = dict(item)
        # When all items have the same RRF score (e.g. single chunk), norm makes score 0.
        # Use 1.0 for tied top results so they pass similarity_threshold.
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


class CrossEncoderReranker:
    """Re-rank candidates using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Re-rank candidates by cross-encoder relevance."""
        if not candidates:
            return []

        model = self._load_model()
        pairs = [(query, c.get("text", "")) for c in candidates]
        scores = model.predict(pairs)

        indexed = [(float(scores[i]), candidates[i]) for i in range(len(candidates))]
        indexed.sort(key=lambda x: -x[0])

        # Normalize scores to [0, 1]
        if indexed:
            min_s, max_s = min(s[0] for s in indexed), max(s[0] for s in indexed)
            norm = (max_s - min_s) or 1.0
        else:
            norm = 1.0

        results = []
        for raw_score, item in indexed[:top_k]:
            copy = dict(item)
            copy["similarity_score"] = min(1.0, max(0.0, (raw_score - min_s) / norm if norm else 0.0))
            results.append(copy)

        return results


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
        embedding_fn: Callable that takes text and returns embedding (list[float]).
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


# ---------------------------------------------------------------------------
# RetrievalService - strategy orchestration
# ---------------------------------------------------------------------------


def create_retrieval_service(
    strategy: str = "dense",
    model_name: str = "",
    persist_dir: str = "",
    collection_name: str = "documents",
    hybrid_alpha: float = 0.5,
    use_reranker: bool = False,
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    use_mmr: bool = False,
    mmr_lambda: float = 0.7,
    rerank_candidates: int = 100,
) -> "RetrievalService":
    """Factory for RetrievalService with given strategy and options."""
    from backend.rag_pipeline.config.vector_store import VectorStoreConfig

    config = VectorStoreConfig(persist_directory=persist_dir, collection_name=collection_name)
    dense = QueryEmbeddingsDenseRetriever(model_name, persist_dir, collection_name)
    sparse = BM25SparseRetriever(config)
    hybrid = HybridRetriever(dense, sparse, hybrid_alpha)
    reranker = CrossEncoderReranker(reranker_model) if use_reranker else None

    return RetrievalService(
        strategy=strategy,
        dense=dense,
        hybrid=hybrid,
        reranker=reranker,
        use_mmr=use_mmr,
        mmr_lambda=mmr_lambda,
        model_name=model_name,
        persist_dir=persist_dir,
        rerank_candidates=rerank_candidates,
    )


class RetrievalService:
    """Orchestrates retrieval strategies: dense, sparse, hybrid, re-ranking, MMR."""

    def __init__(
        self,
        strategy: str = "dense",
        dense: DenseRetriever | None = None,
        hybrid: HybridRetriever | None = None,
        reranker: CrossEncoderReranker | None = None,
        use_mmr: bool = False,
        mmr_lambda: float = 0.7,
        model_name: str = "",
        persist_dir: str = "",
        rerank_candidates: int = 100,
    ) -> None:
        self.strategy = strategy.lower()
        self.dense = dense
        self.hybrid = hybrid
        self.reranker = reranker
        self.use_mmr = use_mmr
        self.mmr_lambda = mmr_lambda
        self.model_name = model_name
        self.persist_dir = persist_dir
        self.rerank_candidates = rerank_candidates

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Retrieve chunks using configured strategy, optionally re-rank and MMR."""
        fetch_k = self.rerank_candidates if self.reranker else top_k

        if self.strategy == "dense" and self.dense:
            candidates = self.dense.retrieve(query, top_k=fetch_k)
        elif self.strategy in ("sparse", "bm25") and self.hybrid:
            candidates = self.hybrid.sparse.retrieve(query, top_k=fetch_k)
        elif self.strategy == "hybrid" and self.hybrid:
            candidates = self.hybrid.retrieve(query, top_k=fetch_k)
        elif self.dense:
            candidates = self.dense.retrieve(query, top_k=fetch_k)
        else:
            return []

        if self.reranker and candidates:
            candidates = self.reranker.rerank(query, candidates, top_k=top_k)

        if self.use_mmr and candidates:
            from backend.rag_pipeline.utils.embedding_model_utils import get_embedding_model

            embed_model = get_embedding_model(self.model_name)
            query_emb = embed_model.get_text_embedding(query)

            def emb_fn(text: str) -> list[float]:
                return embed_model.get_text_embedding(text)

            candidates = mmr_rerank(candidates, query_emb, emb_fn, self.mmr_lambda, top_k)

        if similarity_threshold > 0:
            candidates = [c for c in candidates if c.get("similarity_score", 0) >= similarity_threshold]

        return candidates[:top_k]
