"""BM25 sparse retrieval for the RAG pipeline.

Provides keyword/lexical retrieval complementary to dense semantic search.
Strong for exact medical terminology (ICD-10, drug names, procedure codes).

Refactored for DDD: depends on IVectorStoreRead instead of VectorStoreManager.

See docs/technical/DDD_TARGET_ARCHITECTURE.md#22-retrieval-bc for design.
"""

from __future__ import annotations

import re
from typing import Any

from rank_bm25 import BM25Okapi

from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.retrieval.domain.interfaces import IVectorStoreRead
from backend.retrieval.infrastructure.vector_store_config import (
    VectorStoreConfig,
)

logger = StructuredLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """Tokenize text for BM25: lowercase, split on non-alphanumeric, filter empty."""
    text_lower = text.lower().strip()
    tokens = re.split(r"[^a-z0-9]+", text_lower)
    return [t for t in tokens if len(t) > 0]


class BM25Store:
    """BM25 sparse index over chunk corpus from vector store.

    Builds index from vector store documents on-demand. Suitable for
    small-to-medium collections; for large corpora consider persistent index.
    """

    def __init__(
        self,
        config: VectorStoreConfig,
        vector_store: IVectorStoreRead | None = None,
    ) -> None:
        """Initialize BM25 store with vector store config or injected reader.

        Args:
            config: VectorStoreConfig with persist_directory and collection_name.
            vector_store: Optional injected IVectorStoreRead. If None, created
                from config using get_vector_store_read().
        """
        self.config = config
        self._vector_store = vector_store
        self._bm25: BM25Okapi | None = None
        self._corpus_ids: list[str] = []
        self._corpus_documents: list[str] = []
        self._corpus_metadatas: list[dict[str, Any]] = []

    def _get_vector_store(self) -> IVectorStoreRead:
        """Lazy-init vector store reader from config if not injected."""
        if self._vector_store is None:
            # Deferred import to avoid circular dependency
            from backend.retrieval.infrastructure.vector_store import (
                get_vector_store_read,
            )

            self._vector_store = get_vector_store_read(self.config)
        return self._vector_store

    def _build_index(self) -> None:
        """Build BM25 index from vector store documents."""
        store = self._get_vector_store()
        ids, documents, metadatas = store.get_all_chunks(limit=100_000)

        if not ids or not documents:
            self._bm25 = None
            self._corpus_ids = []
            self._corpus_documents = []
            self._corpus_metadatas = []
            logger.debug("BM25 index empty - no documents in vector store")
            return

        tokenized = [_tokenize(doc or "") for doc in documents]
        self._bm25 = BM25Okapi(tokenized)
        self._corpus_ids = ids
        self._corpus_documents = [doc or "" for doc in documents]
        self._corpus_metadatas = metadatas
        logger.debug(
            "BM25 index built",
            chunk_count=len(ids),
        )

    def query(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Query BM25 index and return chunks in EmbeddingResult-like format.

        Args:
            query: Search query text.
            top_k: Maximum number of results to return.

        Returns:
            List of dicts with keys: text, similarity_score, document_id,
            document_name, chunk_index, record_id, page_number.
            similarity_score is BM25 score normalized to [0, 1] via min-max.
        """
        if self._bm25 is None:
            self._build_index()

        if self._bm25 is None or not self._corpus_ids:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        indices = scores.argsort()[::-1][:top_k]

        selected_scores = scores[indices]
        min_s, max_s = float(selected_scores.min()), float(selected_scores.max())
        norm = (max_s - min_s) or 1.0

        results: list[dict[str, Any]] = []
        for j, i in enumerate(indices):
            i = int(i)
            meta = self._corpus_metadatas[i] if i < len(self._corpus_metadatas) else {}
            doc_text = self._corpus_documents[i] if i < len(self._corpus_documents) else meta.get("text", "")

            raw = float(scores[i])
            norm_score = (raw - min_s) / norm if norm else 0.0

            results.append(
                {
                    "text": doc_text,
                    "similarity_score": min(1.0, max(0.0, norm_score)),
                    "document_id": meta.get("document_id", "unknown"),
                    "document_name": meta.get("document_name", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "record_id": self._corpus_ids[i],
                    "page_number": meta.get("page_number", "unknown"),
                    "page_label": meta.get("page_label", "unknown"),
                }
            )

        return results
