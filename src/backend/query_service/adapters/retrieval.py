"""Adapter to the Retrieval BC.

Connects the Query Service's IRetrievalService port to the
Retrieval BC's create_retrieval_service factory.
"""

from __future__ import annotations

from typing import Any

from backend.retrieval.application.search_service import create_retrieval_service

from backend.query_service.ports.retrieval import IRetrievalService


class RetrievalAdapter(IRetrievalService):
    """Adapter that delegates to the Retrieval BC.

    Wraps the Retrieval BC's create_retrieval_service factory and
    provides a simplified retrieve method for the Query Service.
    """

    def __init__(
        self,
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
    ) -> None:
        """Initialize with retrieval configuration.

        Args:
            strategy: Retrieval strategy (dense, sparse, hybrid, bm25).
            model_name: Embedding model name.
            persist_dir: Vector store persist directory.
            collection_name: ChromaDB collection name.
            hybrid_alpha: Hybrid search alpha.
            use_reranker: Whether to apply cross-encoder reranking.
            reranker_model: Cross-encoder model name.
            use_mmr: Whether to apply MMR diversity re-ranking.
            mmr_lambda: MMR lambda balance.
            rerank_candidates: Candidates before reranking.
        """
        self._config = {
            "strategy": strategy,
            "model_name": model_name,
            "persist_dir": persist_dir,
            "collection_name": collection_name,
            "hybrid_alpha": hybrid_alpha,
            "use_reranker": use_reranker,
            "reranker_model": reranker_model,
            "use_mmr": use_mmr,
            "mmr_lambda": mmr_lambda,
            "rerank_candidates": rerank_candidates,
        }
        self._service = None

    def _get_service(self, strategy: str | None = None) -> Any:
        """Get or create the retrieval service, optionally with a strategy override.

        Args:
            strategy: Optional strategy override.

        Returns:
            RetrievalService instance.
        """
        config = dict(self._config)
        if strategy is not None:
            config["strategy"] = strategy
        return create_retrieval_service(**config)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant document chunks for a query.

        Args:
            query: The search query text.
            top_k: Maximum number of chunks.
            similarity_threshold: Minimum similarity score.
            strategy: Optional strategy override.

        Returns:
            List of result dicts.
        """
        service = self._get_service(strategy)
        return service.retrieve(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
