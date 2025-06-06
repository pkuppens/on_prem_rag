"""Vector store abstractions and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import chromadb
from llama_index.core import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore

from rag_pipeline.config.vector_store import VectorStoreConfig


class VectorStoreManager(ABC):
    """Abstract vector store manager."""

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
    def query(self, embedding: list[float], top_k: int) -> list[str]:
        """Query the store and return matching IDs."""


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
        return chromadb.PersistentClient(path=self.config.persist_directory)

    def get_storage_context(self) -> StorageContext:
        vector_store = ChromaVectorStore(chroma_collection=self._collection)
        return StorageContext.from_defaults(vector_store=vector_store)

    def add_embeddings(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None) -> None:
        self._collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query(self, embedding: list[float], top_k: int) -> list[str]:
        result = self._collection.query(query_embeddings=[embedding], n_results=top_k)
        return result["ids"][0] if result["ids"] else []


def get_vector_store_manager_from_env() -> VectorStoreManager:
    """Factory that creates a vector store manager based on environment config."""

    config = VectorStoreConfig()
    if config.implementation == "chroma":
        return ChromaVectorStoreManager(config)
    raise ValueError(f"Unsupported vector store implementation: {config.implementation}")
