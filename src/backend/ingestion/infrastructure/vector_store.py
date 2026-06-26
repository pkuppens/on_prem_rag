"""ChromaDB vector store adapter implementing IVectorStoreWrite.

This is the write-side ChromaDB adapter used by the Ingestion BC.
It implements the ``IVectorStoreWrite`` port interface defined in the
Retrieval BC.
"""

from __future__ import annotations

from typing import Any

import chromadb

from backend.ingestion.domain.value_objects import Chunk
from backend.retrieval.domain.interfaces import IVectorStoreWrite
from backend.retrieval.infrastructure.vector_store_config import (
    VectorStoreConfig,
)


def _create_client(config: VectorStoreConfig):
    """Create a ChromaDB client from config."""
    if config.host:
        return chromadb.HttpClient(host=config.host, port=config.port or 8000)
    persist_dir = str(config.persist_directory) if config.persist_directory else None
    return chromadb.PersistentClient(path=persist_dir)


class ChromaVectorStoreWriteAdapter(IVectorStoreWrite):
    """ChromaDB write adapter implementing IVectorStoreWrite.

    Supports adding embeddings, deleting by document name, and
    duplicate detection via content hash.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        """Initialize adapter from config.

        Args:
            config: VectorStoreConfig with persist_directory and collection_name.
        """
        self._config = config
        self._client = _create_client(config)
        self._collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # IVectorStoreWrite implementation
    # ------------------------------------------------------------------

    def add_embeddings(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add embeddings to the store.

        Args:
            ids: Unique identifiers for each embedding.
            embeddings: List of embedding vectors.
            metadatas: Optional list of metadata dicts (same length).
        """
        # Extract documents from metadata if available
        documents: list[str] = []
        if metadatas:
            for meta in metadatas:
                doc_text = meta.get("text", "")
                documents.append(doc_text)
        else:
            documents = [""] * len(ids)

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def delete_by_document_name(self, document_name: str) -> int:
        """Delete all chunks for a document by its filename.

        Args:
            document_name: Filename of the document (e.g. 'report.pdf').

        Returns:
            Number of chunks deleted.
        """
        result = self._collection.get(where={"document_name": document_name}, include=[])
        ids_to_delete = result["ids"] if result["ids"] else []
        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    def has_document_with_file_hash(
        self,
        file_content_hash: str,
        embedding_model: str | None = None,
    ) -> bool:
        """Check if any chunk with this file content hash exists.

        Args:
            file_content_hash: SHA-256 hash of the file content.
            embedding_model: Optional model name to scope the check.

        Returns:
            True if a matching chunk already exists.
        """
        try:
            where: dict[str, Any] = {"file_content_hash": file_content_hash}
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

    def store_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        *,
        file_content_hash: str | None = None,
        embedding_model: str | None = None,
    ) -> int:
        """Store domain Chunks with their embeddings.

        Convenience method that creates clean metadata from domain Chunks
        and delegates to add_embeddings.

        Args:
            chunks: Domain Chunk objects.
            embeddings: Corresponding embedding vectors.
            file_content_hash: Optional file-level content hash.
            embedding_model: Optional model name for metadata.

        Returns:
            Number of records stored.
        """
        if not chunks or not embeddings:
            return 0

        ids: list[str] = []
        metadatas_list: list[dict] = []

        for i, chunk in enumerate(chunks):
            if i >= len(embeddings):
                break
            doc_id = f"{chunk.document_id}" if chunk.document_id else f"chunk_{i}"
            ids.append(doc_id)

            # Build clean metadata
            meta: dict[str, Any] = {
                "text": chunk.text,
                "document_name": chunk.document_name,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "source": chunk.source,
                "page_number": chunk.page_number or "unknown",
                "page_label": chunk.page_label or "unknown",
                "content_hash": chunk.content_hash,
            }
            if file_content_hash:
                meta["file_content_hash"] = file_content_hash
            if embedding_model:
                meta["embedding_model"] = embedding_model
            metadatas_list.append(meta)

        self.add_embeddings(ids, embeddings[: len(ids)], metadatas_list)
        return len(ids)


def get_vector_store_write(
    config: VectorStoreConfig | None = None,
) -> ChromaVectorStoreWriteAdapter:
    """Factory: create IVectorStoreWrite from config or environment.

    Args:
        config: Optional VectorStoreConfig. If None, reads from env vars.

    Returns:
        ChromaVectorStoreWriteAdapter implementing IVectorStoreWrite.
    """
    cfg = config or VectorStoreConfig()
    return ChromaVectorStoreWriteAdapter(cfg)
