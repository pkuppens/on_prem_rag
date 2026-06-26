"""ChromaDB vector store adapter implementing IVectorStoreRead (read-only).

Extracted from ChromaVectorStoreManager in rag_pipeline/core/vector_store.py.
Only the read-side methods are exposed here. The write side (add_embeddings,
delete_by_document_name, get_storage_context) stays in the old location for
Phase 3 (Ingestion BC) to extract.
"""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb import Collection

from backend.retrieval.domain.interfaces import IVectorStoreRead
from backend.retrieval.infrastructure.vector_store_config import (
    VectorStoreConfig,
)


class ChromaVectorStoreReadAdapter(IVectorStoreRead):
    """Read-only ChromaDB adapter implementing IVectorStoreRead.

    Wraps a ChromaDB collection and provides search, metadata retrieval,
    and chunk enumeration without write capabilities.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        """Initialize adapter from config.

        Args:
            config: VectorStoreConfig with persist_directory / host / port
                and collection_name.
        """
        self._config = config
        self._client = self._create_client()
        self._collection: Collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def config(self) -> VectorStoreConfig:
        return self._config

    def _create_client(self):
        if self._config.host:
            return chromadb.HttpClient(host=self._config.host, port=self._config.port or 8000)
        persist_dir = str(self._config.persist_directory) if self._config.persist_directory else None
        return chromadb.PersistentClient(path=persist_dir)

    # ------------------------------------------------------------------
    # IVectorStoreRead implementation
    # ------------------------------------------------------------------

    def query(self, embedding: list[float], top_k: int) -> tuple[list[str], list[float]]:
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["distances"],
        )
        return (
            result["ids"][0] if result["ids"] else [],
            result["distances"][0] if result["distances"] else [],
        )

    def search(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        """Search the store and return full result dicts.

        Returns dicts with keys: text, similarity_score, document_id,
        document_name, chunk_index, record_id, page_number, page_label.
        """
        ids, distances = self.query(embedding, top_k)
        if not ids:
            return []

        results = self._collection.get(ids=ids, include=["documents", "metadatas"])

        formatted: list[dict[str, Any]] = []
        for i, doc_id in enumerate(ids):
            metadata = results["metadatas"][i] if results["metadatas"] and i < len(results["metadatas"]) else {}
            document_text = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""

            formatted.append(
                {
                    "text": document_text,
                    "similarity_score": 1 - distances[i],  # Convert distance to similarity
                    "document_id": metadata.get("document_id", "unknown"),
                    "document_name": metadata.get("document_name", "unknown"),
                    "chunk_index": metadata.get("chunk_index", "unknown"),
                    "record_id": doc_id,
                    "page_number": metadata.get("page_number", "unknown"),
                    "page_label": metadata.get("page_label", "unknown"),
                }
            )

        return formatted

    def get_chunk_count(self) -> int:
        result = self._collection.get(include=[])
        return len(result["ids"]) if result.get("ids") else 0

    def get_all_chunks(self, limit: int = 100_000) -> tuple[list[str], list[str], list[dict]]:
        try:
            result = self._collection.get(
                where={"chunk_index": {"$gte": 0}},
                include=["documents", "metadatas"],
                limit=limit,
            )
        except Exception:
            result = self._collection.get(
                include=["documents", "metadatas"],
                limit=limit,
            )
        ids = result.get("ids") or []
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        texts: list[str] = []
        for i in range(len(ids)):
            doc = documents[i] if i < len(documents) else None
            meta = metadatas[i] if i < len(metadatas) else {}
            text = (doc or (meta.get("text", "") if isinstance(meta, dict) else "")) or ""
            texts.append(text)
        while len(metadatas) < len(ids):
            metadatas.append({})
        return ids, texts, metadatas[: len(ids)]

    def has_document_with_file_hash(
        self,
        file_content_hash: str,
        embedding_model: str | None = None,
    ) -> bool:
        try:
            where: dict = {"file_content_hash": file_content_hash}
            if embedding_model:
                where["embedding_model"] = embedding_model
            result = self._collection.get(
                where=where,
                include=[],
                limit=1,
            )
            return len(result.get("ids") or []) > 0
        except Exception:
            return False


def get_vector_store_read(
    config: VectorStoreConfig | None = None,
) -> ChromaVectorStoreReadAdapter:
    """Factory: create IVectorStoreRead from config or environment.

    Args:
        config: Optional VectorStoreConfig. If None, reads from env vars.

    Returns:
        ChromaVectorStoreReadAdapter implementing IVectorStoreRead.
    """
    cfg = config or VectorStoreConfig()
    return ChromaVectorStoreReadAdapter(cfg)
