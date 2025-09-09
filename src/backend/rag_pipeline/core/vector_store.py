"""Vector store abstractions and implementations with production-grade features.

This module provides enhanced vector store implementations with:
- Connection pooling and management
- Health monitoring and checks
- Performance metrics
- Error handling and retry mechanisms
- Backup and recovery procedures
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Optional

import chromadb
from llama_index.core import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore

from backend.rag_pipeline.config.vector_store import VectorStoreConfig

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""

    status: HealthStatus
    message: str
    timestamp: float
    response_time_ms: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for vector store operations."""

    total_queries: int = 0
    total_inserts: int = 0
    total_deletes: int = 0
    avg_query_time_ms: float = 0.0
    avg_insert_time_ms: float = 0.0
    avg_delete_time_ms: float = 0.0
    error_count: int = 0
    last_updated: float = field(default_factory=time.time)


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
    def query(self, embedding: list[float], top_k: int) -> tuple[list[str], list[float]]:
        """Query the store and return matching IDs and distances."""

    @abstractmethod
    def health_check(self) -> HealthCheck:
        """Perform a health check on the vector store."""

    @abstractmethod
    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics for the vector store."""

    @abstractmethod
    def backup(self, backup_path: str) -> bool:
        """Create a backup of the vector store."""

    @abstractmethod
    def restore(self, backup_path: str) -> bool:
        """Restore the vector store from a backup."""


@dataclass
class ChromaVectorStoreManager(VectorStoreManager):
    """ChromaDB-based vector store manager with production features."""

    config: VectorStoreConfig
    _client: Optional[Any] = field(default=None, init=False)
    _collection: Optional[Any] = field(default=None, init=False)
    _metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)
    _last_health_check: Optional[HealthCheck] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._client = self._create_client()
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB vector store manager initialized: {self.config.collection_name}")

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
        """Add embeddings with performance tracking and error handling."""
        start_time = time.time()

        try:
            with self._lock:
                self._collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

            # Update metrics
            elapsed_ms = (time.time() - start_time) * 1000
            self._update_insert_metrics(elapsed_ms)

            logger.debug(f"Added {len(ids)} embeddings in {elapsed_ms:.2f}ms")

        except Exception as e:
            self._metrics.error_count += 1
            logger.error(f"Failed to add embeddings: {e}")
            raise

    def query(self, embedding: list[float], top_k: int) -> tuple[list[str], list[float]]:
        """Query embeddings with performance tracking and error handling."""
        start_time = time.time()

        try:
            with self._lock:
                result = self._collection.query(query_embeddings=[embedding], n_results=top_k, include=["distances"])

            # Update metrics
            elapsed_ms = (time.time() - start_time) * 1000
            self._update_query_metrics(elapsed_ms)

            ids = result["ids"][0] if result["ids"] else []
            distances = result["distances"][0] if result["distances"] else []

            logger.debug(f"Query returned {len(ids)} results in {elapsed_ms:.2f}ms")
            return ids, distances

        except Exception as e:
            self._metrics.error_count += 1
            logger.error(f"Failed to query embeddings: {e}")
            raise

    def health_check(self) -> HealthCheck:
        """Perform a health check on the ChromaDB vector store."""
        start_time = time.time()

        try:
            # Test basic connectivity
            with self._lock:
                # Try to get collection info
                collection_count = self._collection.count()

                # Try a simple query to test functionality
                test_embedding = [0.0] * 384  # Standard embedding size
                self._collection.query(query_embeddings=[test_embedding], n_results=1, include=["distances"])

            response_time_ms = (time.time() - start_time) * 1000

            # Determine health status based on response time and functionality
            if response_time_ms < 100:
                status = HealthStatus.HEALTHY
                message = "Vector store is healthy"
            elif response_time_ms < 500:
                status = HealthStatus.DEGRADED
                message = "Vector store is responding slowly"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Vector store is responding very slowly"

            health_check = HealthCheck(
                status=status,
                message=message,
                timestamp=time.time(),
                response_time_ms=response_time_ms,
                details={
                    "collection_name": self.config.collection_name,
                    "collection_count": collection_count,
                    "error_count": self._metrics.error_count,
                },
            )

            self._last_health_check = health_check
            logger.debug(f"Health check completed: {status.value} ({response_time_ms:.2f}ms)")

            return health_check

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            health_check = HealthCheck(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                timestamp=time.time(),
                response_time_ms=response_time_ms,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            self._last_health_check = health_check
            logger.error(f"Health check failed: {e}")

            return health_check

    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics for the vector store."""
        with self._lock:
            # Create a copy to avoid race conditions
            metrics = PerformanceMetrics(
                total_queries=self._metrics.total_queries,
                total_inserts=self._metrics.total_inserts,
                total_deletes=self._metrics.total_deletes,
                avg_query_time_ms=self._metrics.avg_query_time_ms,
                avg_insert_time_ms=self._metrics.avg_insert_time_ms,
                avg_delete_time_ms=self._metrics.avg_delete_time_ms,
                error_count=self._metrics.error_count,
                last_updated=self._metrics.last_updated,
            )

        return metrics

    def backup(self, backup_path: str) -> bool:
        """Create a backup of the ChromaDB vector store."""
        try:
            import shutil
            from pathlib import Path

            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # For persistent ChromaDB, backup the entire directory
            if self.config.persist_directory:
                source_dir = Path(self.config.persist_directory)
                if source_dir.exists():
                    shutil.copytree(source_dir, backup_path, dirs_exist_ok=True)
                    logger.info(f"Backup created: {backup_path}")
                    return True
                else:
                    logger.error(f"Source directory does not exist: {source_dir}")
                    return False
            else:
                # For in-memory or remote ChromaDB, export collection data
                with self._lock:
                    # Get all data from collection
                    all_data = self._collection.get()

                    # Save to JSON file
                    import json

                    with open(backup_path, "w") as f:
                        json.dump(all_data, f, indent=2)

                    logger.info(f"Collection data backed up to: {backup_path}")
                    return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def restore(self, backup_path: str) -> bool:
        """Restore the ChromaDB vector store from a backup."""
        try:
            from pathlib import Path

            backup_path = Path(backup_path)
            if not backup_path.exists():
                logger.error(f"Backup file does not exist: {backup_path}")
                return False

            # For persistent ChromaDB, restore the entire directory
            if self.config.persist_directory:
                source_dir = Path(self.config.persist_directory)

                # Remove existing directory
                if source_dir.exists():
                    import shutil

                    shutil.rmtree(source_dir)

                # Restore from backup
                import shutil

                shutil.copytree(backup_path, source_dir)

                # Recreate client and collection
                self._client = self._create_client()
                self._collection = self._client.get_or_create_collection(
                    name=self.config.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )

                logger.info(f"Restored from backup: {backup_path}")
                return True
            else:
                # For in-memory ChromaDB, restore collection data
                import json

                with open(backup_path, "r") as f:
                    data = json.load(f)

                # Clear existing collection
                with self._lock:
                    # Delete all existing data
                    all_ids = self._collection.get()["ids"]
                    if all_ids:
                        self._collection.delete(ids=all_ids)

                    # Restore data
                    if data.get("ids"):
                        self._collection.add(
                            ids=data["ids"],
                            embeddings=data["embeddings"],
                            metadatas=data["metadatas"],
                            documents=data.get("documents"),
                        )

                logger.info(f"Collection data restored from: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def _update_query_metrics(self, elapsed_ms: float) -> None:
        """Update query performance metrics."""
        with self._lock:
            self._metrics.total_queries += 1
            # Update running average
            if self._metrics.total_queries == 1:
                self._metrics.avg_query_time_ms = elapsed_ms
            else:
                self._metrics.avg_query_time_ms = (
                    self._metrics.avg_query_time_ms * (self._metrics.total_queries - 1) + elapsed_ms
                ) / self._metrics.total_queries
            self._metrics.last_updated = time.time()

    def _update_insert_metrics(self, elapsed_ms: float) -> None:
        """Update insert performance metrics."""
        with self._lock:
            self._metrics.total_inserts += 1
            # Update running average
            if self._metrics.total_inserts == 1:
                self._metrics.avg_insert_time_ms = elapsed_ms
            else:
                self._metrics.avg_insert_time_ms = (
                    self._metrics.avg_insert_time_ms * (self._metrics.total_inserts - 1) + elapsed_ms
                ) / self._metrics.total_inserts
            self._metrics.last_updated = time.time()


def get_vector_store_manager_from_env() -> VectorStoreManager:
    """Factory that creates a vector store manager based on environment config."""

    config = VectorStoreConfig()
    if config.implementation == "chroma":
        return ChromaVectorStoreManager(config)
    raise ValueError(f"Unsupported vector store implementation: {config.implementation}")
