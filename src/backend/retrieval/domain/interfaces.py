"""Port interfaces for the Retrieval bounded context.

Follows the port/adapter pattern (hexagonal architecture):
- IVectorStoreRead: read-only vector store port
- EmbeddingProvider: imported from llm_gateway for query encoding
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.llm_gateway.domain.interfaces import EmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "IVectorStoreRead",
    "IVectorStoreWrite",
]


class IVectorStoreWrite(ABC):
    """Write interface for vector store, used by the Ingestion BC.

    Implementations provide append, delete, and duplicate-check operations
    without exposing read/query capabilities beyond what ingestion needs.
    """

    @abstractmethod
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
        ...

    @abstractmethod
    def delete_by_document_name(self, document_name: str) -> int:
        """Delete all chunks for a document by its filename.

        Args:
            document_name: Filename of the document (e.g. 'report.pdf').

        Returns:
            Number of chunks deleted (0 if none matched).
        """
        ...

    @abstractmethod
    def has_document_with_file_hash(
        self,
        file_content_hash: str,
        embedding_model: str | None = None,
    ) -> bool:
        """Check if any chunk with this file content hash exists.

        When embedding_model is provided, also requires matching model.
        Used for exact duplicate detection before re-ingestion.

        Args:
            file_content_hash: SHA-256 hash of the file content.
            embedding_model: Optional model name to scope the check.

        Returns:
            True if a matching chunk already exists.
        """
        ...


class IVectorStoreRead(ABC):
    """Read-only vector store interface for retrieval.

    Implementations provide query access to vector stores without write
    capabilities. The write side lives in the Ingestion BC.
    """

    @abstractmethod
    def query(self, embedding: list[float], top_k: int) -> tuple[list[str], list[float]]:
        """Query the store and return matching IDs and distances.

        Args:
            embedding: Query embedding vector.
            top_k: Maximum number of results.

        Returns:
            Tuple of (ids, distances).
        """
        ...

    @abstractmethod
    def search(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        """Search the store and return full result dicts (text + metadata).

        The returned dicts have keys matching the EmbeddingResult format:
        text, similarity_score, document_id, document_name, chunk_index,
        record_id, page_number, page_label.

        Args:
            embedding: Query embedding vector.
            top_k: Maximum number of results.

        Returns:
            List of result dicts sorted by similarity (descending).
        """
        ...

    @abstractmethod
    def get_chunk_count(self) -> int:
        """Return the number of chunks in the store."""
        ...

    @abstractmethod
    def get_all_chunks(self, limit: int = 100_000) -> tuple[list[str], list[str], list[dict]]:
        """Fetch all chunk ids, texts, and metadatas.

        Used by BM25 index building.

        Returns:
            Tuple of (ids, texts, metadatas).
        """
        ...

    @abstractmethod
    def has_document_with_file_hash(
        self,
        file_content_hash: str,
        embedding_model: str | None = None,
    ) -> bool:
        """Check if any chunk with this file content hash exists."""
        ...
