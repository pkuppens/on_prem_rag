# src/backend/memory/vector_memory.py
"""Long-term vector memory using ChromaDB.

Provides persistent memory storage using embeddings for semantic search.
Each agent role gets its own collection, plus a shared collection for
cross-agent context.

Features:
- Role-based collections for memory isolation
- Shared memory pool for cross-agent access
- Semantic similarity search
- Retention policies and pruning
- Embedding storage with metadata

Uses the existing ChromaDB patterns from the RAG pipeline.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from backend.memory.config import VectorMemoryConfig, get_memory_config
from backend.shared.utils.directory_utils import ensure_directory_exists

logger = logging.getLogger(__name__)


@dataclass
class MemoryDocument:
    """A document stored in vector memory."""

    id: str
    content: str
    agent_role: str
    session_id: str
    memory_type: str = "general"  # "fact", "observation", "result", "context"
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_metadata(self) -> dict[str, Any]:
        """Convert to ChromaDB metadata format."""
        return {
            "agent_role": self.agent_role,
            "session_id": self.session_id,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            **{k: json.dumps(v) if isinstance(v, dict | list) else str(v) for k, v in self.metadata.items()},
        }


@dataclass
class SearchResult:
    """Result from a memory search."""

    id: str
    content: str
    distance: float
    metadata: dict[str, Any]

    @property
    def similarity(self) -> float:
        """Convert distance to similarity score (0-1, higher is better)."""
        # Assuming cosine distance, convert to similarity
        return max(0.0, 1.0 - self.distance)


class DefaultEmbeddingFunction(EmbeddingFunction):
    """Default embedding function using sentence-transformers.

    Uses all-MiniLM-L6-v2 by default (384 dimensions, fast, good quality).
    Falls back to simple character-based hashing if sentence-transformers not available.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._use_fallback = False

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback embeddings")
            self._use_fallback = True

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for the input documents."""
        if self._use_fallback:
            return self._fallback_embeddings(input)

        embeddings = self._model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()

    def _fallback_embeddings(self, texts: Documents) -> Embeddings:
        """Simple fallback embeddings based on character hashing.

        Not suitable for production - install sentence-transformers for real embeddings.
        """
        import hashlib

        embeddings = []
        for text in texts:
            # Create a deterministic 384-dim vector from text hash
            text_bytes = text.encode("utf-8")
            hash_bytes = hashlib.sha384(text_bytes).digest()
            # Convert to floats in [-1, 1] range
            embedding = [(b / 127.5) - 1.0 for b in hash_bytes]
            embeddings.append(embedding)
        return embeddings


class VectorMemory:
    """Long-term vector memory store using ChromaDB.

    Provides semantic storage and retrieval of memory entries using embeddings.
    Each agent role has its own collection for isolation.
    """

    # Collection name for shared cross-agent memory
    SHARED_COLLECTION = "shared_context"

    def __init__(self, config: VectorMemoryConfig | None = None):
        self.config = config or get_memory_config().vector
        self._client = self._create_client()
        self._embedding_fn = DefaultEmbeddingFunction(self.config.embedding_model)
        self._collections: dict[str, chromadb.Collection] = {}

    def _create_client(self) -> chromadb.ClientAPI:
        """Create ChromaDB persistent client."""
        persist_dir = self.config.persist_directory
        ensure_directory_exists(persist_dir)
        return chromadb.PersistentClient(path=str(persist_dir))

    def _get_collection_name(self, agent_role: str) -> str:
        """Get the collection name for an agent role."""
        if agent_role == self.SHARED_COLLECTION:
            return f"{self.config.collection_prefix}shared"
        # Sanitize role name for collection name
        safe_role = agent_role.lower().replace(" ", "_").replace("-", "_")
        return f"{self.config.collection_prefix}{safe_role}"

    def _get_collection(self, agent_role: str) -> chromadb.Collection:
        """Get or create a collection for an agent role."""
        collection_name = self._get_collection_name(agent_role)

        if collection_name not in self._collections:
            self._collections[collection_name] = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine", "agent_role": agent_role},
            )
            logger.debug(f"Created/loaded collection: {collection_name}")

        return self._collections[collection_name]

    def store(self, document: MemoryDocument) -> str:
        """Store a document in vector memory.

        Args:
            document: The memory document to store

        Returns:
            The document ID
        """
        collection = self._get_collection(document.agent_role)

        # Check collection size limit
        count = collection.count()
        if count >= self.config.max_entries_per_role:
            # Remove oldest entries to make room
            self._prune_oldest(document.agent_role, count - self.config.max_entries_per_role + 1)

        collection.add(
            ids=[document.id],
            documents=[document.content],
            metadatas=[document.to_metadata()],
        )

        logger.debug(f"Stored memory {document.id} in {document.agent_role} collection")
        return document.id

    def store_batch(self, documents: list[MemoryDocument]) -> list[str]:
        """Store multiple documents in vector memory.

        Args:
            documents: List of memory documents to store

        Returns:
            List of document IDs
        """
        # Group by agent role
        by_role: dict[str, list[MemoryDocument]] = {}
        for doc in documents:
            if doc.agent_role not in by_role:
                by_role[doc.agent_role] = []
            by_role[doc.agent_role].append(doc)

        ids = []
        for agent_role, docs in by_role.items():
            collection = self._get_collection(agent_role)
            doc_ids = [d.id for d in docs]
            collection.add(
                ids=doc_ids,
                documents=[d.content for d in docs],
                metadatas=[d.to_metadata() for d in docs],
            )
            ids.extend(doc_ids)

        return ids

    def search(
        self,
        query: str,
        agent_role: str,
        top_k: int = 5,
        memory_type: str | None = None,
        session_id: str | None = None,
        min_importance: float = 0.0,
    ) -> list[SearchResult]:
        """Search for similar memories.

        Args:
            query: The search query
            agent_role: The agent role's collection to search
            top_k: Number of results to return
            memory_type: Optional filter by memory type
            session_id: Optional filter by session ID
            min_importance: Minimum importance score filter

        Returns:
            List of search results sorted by relevance
        """
        collection = self._get_collection(agent_role)

        # Build where filter
        where_filter: dict[str, Any] | None = None
        conditions = []

        if memory_type:
            conditions.append({"memory_type": memory_type})
        if session_id:
            conditions.append({"session_id": session_id})
        if min_importance > 0:
            conditions.append({"importance": {"$gte": min_importance}})

        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        # Execute query
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to SearchResult objects
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                search_results.append(
                    SearchResult(
                        id=doc_id,
                        content=results["documents"][0][i] if results["documents"] else "",
                        distance=results["distances"][0][i] if results["distances"] else 0.0,
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )

        return search_results

    def search_shared(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search the shared memory pool.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            List of search results from shared memory
        """
        return self.search(query, self.SHARED_COLLECTION, top_k)

    def get(self, agent_role: str, document_id: str) -> MemoryDocument | None:
        """Get a specific document by ID.

        Args:
            agent_role: The agent role's collection
            document_id: The document ID

        Returns:
            The memory document or None if not found
        """
        collection = self._get_collection(agent_role)
        result = collection.get(ids=[document_id], include=["documents", "metadatas"])

        if not result["ids"]:
            return None

        metadata = result["metadatas"][0] if result["metadatas"] else {}
        return MemoryDocument(
            id=document_id,
            content=result["documents"][0] if result["documents"] else "",
            agent_role=metadata.get("agent_role", agent_role),
            session_id=metadata.get("session_id", ""),
            memory_type=metadata.get("memory_type", "general"),
            importance=float(metadata.get("importance", 0.5)),
            metadata={
                k: v
                for k, v in metadata.items()
                if k not in ("agent_role", "session_id", "memory_type", "importance", "created_at")
            },
        )

    def delete(self, agent_role: str, document_id: str) -> bool:
        """Delete a document from memory.

        Args:
            agent_role: The agent role's collection
            document_id: The document ID to delete

        Returns:
            True if document was deleted
        """
        collection = self._get_collection(agent_role)
        try:
            collection.delete(ids=[document_id])
            return True
        except Exception:
            return False

    def delete_by_session(self, agent_role: str, session_id: str) -> int:
        """Delete all documents from a session.

        Args:
            agent_role: The agent role's collection
            session_id: The session ID to delete

        Returns:
            Number of documents deleted
        """
        collection = self._get_collection(agent_role)
        result = collection.get(where={"session_id": session_id}, include=[])

        if result["ids"]:
            collection.delete(ids=result["ids"])
            return len(result["ids"])
        return 0

    def _prune_oldest(self, agent_role: str, count: int) -> int:
        """Remove the oldest entries from a collection.

        Args:
            agent_role: The agent role's collection
            count: Number of entries to remove

        Returns:
            Number of entries removed
        """
        collection = self._get_collection(agent_role)

        # Get all entries with their created_at timestamps
        result = collection.get(include=["metadatas"])

        if not result["ids"]:
            return 0

        # Sort by created_at (oldest first)
        entries = list(zip(result["ids"], result["metadatas"], strict=False))
        entries.sort(key=lambda x: x[1].get("created_at", ""))

        # Delete oldest entries
        ids_to_delete = [e[0] for e in entries[:count]]
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"Pruned {len(ids_to_delete)} oldest entries from {agent_role}")

        return len(ids_to_delete)

    def prune_by_retention(self) -> int:
        """Remove entries older than retention period.

        Returns:
            Total number of entries removed across all collections
        """
        if self.config.retention_days <= 0:
            return 0

        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(days=self.config.retention_days)
        cutoff_str = cutoff.isoformat()
        total_removed = 0

        for collection in self._client.list_collections():
            result = collection.get(include=["metadatas"])

            if not result["ids"]:
                continue

            # Find entries older than cutoff
            ids_to_delete = []
            for i, metadata in enumerate(result["metadatas"]):
                created_at = metadata.get("created_at", "")
                if created_at and created_at < cutoff_str:
                    ids_to_delete.append(result["ids"][i])

            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                total_removed += len(ids_to_delete)

        if total_removed > 0:
            logger.info(f"Retention pruning removed {total_removed} entries")

        return total_removed

    def get_collection_stats(self, agent_role: str) -> dict[str, Any]:
        """Get statistics for a collection.

        Args:
            agent_role: The agent role's collection

        Returns:
            Dictionary with collection statistics
        """
        collection = self._get_collection(agent_role)
        return {
            "name": collection.name,
            "count": collection.count(),
            "max_entries": self.config.max_entries_per_role,
            "retention_days": self.config.retention_days,
        }

    def list_collections(self) -> list[str]:
        """List all agent role collections.

        Returns:
            List of collection names
        """
        return [c.name for c in self._client.list_collections()]
