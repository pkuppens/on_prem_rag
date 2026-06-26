"""RetrievalService — orchestrates strategy selection + execution.

Moved from rag_pipeline/core/retrieval.py and refactored to use port-based
dependencies (EmbeddingProvider, IVectorStoreRead) instead of concrete imports.
"""

from __future__ import annotations

from typing import Any

from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.retrieval.application.reranking import CrossEncoderReranker
from backend.retrieval.domain.interfaces import (
    EmbeddingProvider,
    IVectorStoreRead,
)
from backend.retrieval.domain.services import (
    BM25SparseRetriever,
    DenseRetriever,
    HybridRetriever,
    QueryEmbeddingsDenseRetriever,
    mmr_rerank,
)
from backend.retrieval.infrastructure.bm25_store import BM25Store
from backend.retrieval.infrastructure.vector_store_config import (
    VectorStoreConfig,
)

logger = StructuredLogger(__name__)


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
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: IVectorStoreRead | None = None,
) -> RetrievalService:
    """Factory for RetrievalService with given strategy and options.

    Args:
        strategy: Retrieval strategy (dense, sparse, hybrid, bm25).
        model_name: Embedding model name (for creating embedding provider).
        persist_dir: Vector store persist directory.
        collection_name: ChromaDB collection name.
        hybrid_alpha: Hybrid alpha (unused with RRF, kept for API compat).
        use_reranker: Whether to apply cross-encoder reranking.
        reranker_model: Cross-encoder model name.
        use_mmr: Whether to apply MMR diversity re-ranking.
        mmr_lambda: MMR lambda balance.
        rerank_candidates: Number of candidates to fetch before reranking.
        embedding_provider: Optional pre-configured EmbeddingProvider.
            If None, a default is created using embedding_model_utils.
        vector_store: Optional pre-configured IVectorStoreRead.
            If None, created from persist_dir/collection_name.

    Returns:
        Configured RetrievalService instance.
    """
    config = VectorStoreConfig(persist_directory=persist_dir, collection_name=collection_name)

    # Resolve embedding provider
    if embedding_provider is None:
        embedding_provider = _create_default_embedding_provider(model_name)

    # Resolve vector store
    if vector_store is None:
        from backend.retrieval.infrastructure.vector_store import (
            get_vector_store_read,
        )

        vector_store = get_vector_store_read(config)

    dense = QueryEmbeddingsDenseRetriever(embedding_provider=embedding_provider, vector_store=vector_store)
    bm25_store = BM25Store(config, vector_store=vector_store)
    sparse = BM25SparseRetriever(bm25_store)
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


def _create_default_embedding_provider(
    model_name: str,
) -> EmbeddingProvider:
    """Create a default EmbeddingProvider from model name.

    Uses the legacy embedding_model_utils to wrap HuggingFaceEmbedding
    into an EmbeddingProvider-compatible adapter.
    """
    from backend.rag_pipeline.utils.embedding_model_utils import (
        get_embedding_model,
    )

    hf_model = get_embedding_model(model_name)
    # HuggingFaceEmbedding already has get_text_embedding matching the
    # EmbeddingProvider interface, so it can be used directly.
    return hf_model  # type: ignore[return-value]


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
            from backend.rag_pipeline.utils.embedding_model_utils import (
                get_embedding_model,
            )

            embed_model = get_embedding_model(self.model_name)
            query_emb = embed_model.get_text_embedding(query)

            def emb_fn(text: str) -> list[float]:
                return embed_model.get_text_embedding(text)

            candidates = mmr_rerank(
                candidates,
                query_emb,
                emb_fn,
                self.mmr_lambda,
                top_k,
            )

        if similarity_threshold > 0:
            candidates = [c for c in candidates if c.get("similarity_score", 0) >= similarity_threshold]

        return candidates[:top_k]
