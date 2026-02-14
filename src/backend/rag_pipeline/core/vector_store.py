"""Vector store abstractions and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import chromadb
from llama_index.core import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore

from backend.rag_pipeline.config.vector_store import VectorStoreConfig


class VectorStoreManager(ABC):
    """Abstract vector store manager."""

    config: VectorStoreConfig

    @abstractmethod
    def get_storage_context(self) -> StorageContext:
        """Return a LlamaIndex storage context bound to the vector store."""

    @abstractmethod
    def add_embeddings(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add embeddings to the store."""

    @abstractmethod
    def query(self, embedding: list[float], top_k: int) -> tuple[list[str], list[float]]:
        """Query the store and return matching IDs and distances."""

    @abstractmethod
    def delete_by_document_name(self, document_name: str) -> int:
        """Delete all chunks for a document by its filename.

        Args:
            document_name: Filename of the document (e.g. 'report.pdf')

        Returns:
            Number of chunks deleted (0 if none matched)
        """


@dataclass
class ChromaVectorStoreManager(VectorStoreManager):
    """ChromaDB-based vector store manager."""

    config: VectorStoreConfig

    def __post_init__(self) -> None:
        self._client = self._create_client()
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _create_client(self):
        if self.config.host:
            return chromadb.HttpClient(host=self.config.host, port=self.config.port or 8000)
        # Convert Path to string for ChromaDB
        persist_dir = str(self.config.persist_directory) if self.config.persist_directory else None
        return chromadb.PersistentClient(path=persist_dir)

    def get_storage_context(self) -> StorageContext:
        vector_store = ChromaVectorStore(chroma_collection=self._collection)
        return StorageContext.from_defaults(vector_store=vector_store)

    def add_embeddings(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None) -> None:
        self._collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query(self, embedding: list[float], top_k: int) -> tuple[list[str], list[float]]:
        result = self._collection.query(query_embeddings=[embedding], n_results=top_k, include=["distances"])
        return (result["ids"][0] if result["ids"] else [], result["distances"][0] if result["distances"] else [])

    def delete_by_document_name(self, document_name: str) -> int:
        """Delete all chunks for a document by its filename.

        ChromaDB stores document_name in metadata. Uses where filter to delete
        all records matching the document.
        """
        result = self._collection.get(where={"document_name": document_name}, include=[])
        ids_to_delete = result["ids"] if result["ids"] else []
        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)


def get_vector_store_manager_from_env() -> VectorStoreManager:
    """Factory that creates a vector store manager based on environment config."""

    config = VectorStoreConfig()
    if config.implementation == "chroma":
        return ChromaVectorStoreManager(config)
    raise ValueError(f"Unsupported vector store implementation: {config.implementation}")
