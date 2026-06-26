"""Port interfaces for the Memory bounded context.

These interfaces define the boundary between the domain/application layer
and the infrastructure layer. Infrastructure implementations depend on these
interfaces, while application code depends on them through dependency injection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.memory.domain.value_objects import MemoryDocument, SearchResult


class ISessionStore(ABC):
    """Interface for short-term session memory storage.

    Provides key-value storage scoped to a session with optional TTL-based
    expiration. Supports both in-memory and Redis backends.
    """

    @abstractmethod
    def get(self, session_id: str, key: str) -> Any | None:
        """Get a value from the session store."""

    @abstractmethod
    def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        agent_role: str | None = None,
    ) -> None:
        """Set a value in the session store."""

    @abstractmethod
    def delete(self, session_id: str, key: str) -> bool:
        """Delete a key from the session store. Returns True if key existed."""

    @abstractmethod
    def get_all(self, session_id: str, agent_role: str | None = None) -> dict[str, Any]:
        """Get all values for a session, optionally filtered by agent role."""

    @abstractmethod
    def clear_session(self, session_id: str) -> int:
        """Clear all entries for a session. Returns count of cleared entries."""

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""

    @abstractmethod
    def get_session_count(self) -> int:
        """Get the number of active sessions."""

    @abstractmethod
    def get_entry_count(self, session_id: str) -> int:
        """Get the number of entries in a session."""


class IVectorMemory(ABC):
    """Interface for long-term vector memory storage.

    Provides semantic storage and retrieval of memory entries using
    embeddings. Each agent role has its own collection for isolation,
    plus a shared collection for cross-agent context.
    """

    @abstractmethod
    def store(self, document: MemoryDocument) -> str:
        """Store a document in vector memory. Returns the document ID."""

    @abstractmethod
    def store_batch(self, documents: list[MemoryDocument]) -> list[str]:
        """Store multiple documents in vector memory. Returns list of document IDs."""

    @abstractmethod
    def search(
        self,
        query: str,
        agent_role: str,
        top_k: int = 5,
        memory_type: str | None = None,
        session_id: str | None = None,
        min_importance: float = 0.0,
    ) -> list[SearchResult]:
        """Search for similar memories."""

    @abstractmethod
    def search_shared(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search the shared memory pool."""

    @abstractmethod
    def get(self, agent_role: str, document_id: str) -> MemoryDocument | None:
        """Get a specific document by ID."""

    @abstractmethod
    def delete(self, agent_role: str, document_id: str) -> bool:
        """Delete a document from memory. Returns True if deleted."""

    @abstractmethod
    def delete_by_session(self, agent_role: str, session_id: str) -> int:
        """Delete all documents from a session. Returns count deleted."""

    @abstractmethod
    def prune_by_retention(self) -> int:
        """Remove entries older than retention period. Returns count removed."""

    @abstractmethod
    def get_collection_stats(self, agent_role: str) -> dict[str, Any]:
        """Get statistics for a collection."""

    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all agent role collections."""


class IEntityStore(ABC):
    """Interface for structured entity memory storage.

    Provides CRUD operations for structured memory entries, conversation
    contexts, entity references, and audit logging.
    """

    @abstractmethod
    def create_memory_entry(
        self,
        agent_role: str,
        session_id: str,
        content: str,
        memory_type: str = "observation",
        importance_score: float = 0.5,
        metadata: dict[str, Any] | None = None,
        source_document_id: str | None = None,
        expires_at: Any | None = None,
    ) -> Any:
        """Create a new memory entry. Returns the created entry."""

    @abstractmethod
    def get_memory_entry(self, entry_id: int) -> Any | None:
        """Get a memory entry by ID."""

    @abstractmethod
    def get_memory_entries(
        self,
        agent_role: str | None = None,
        session_id: str | None = None,
        memory_type: str | None = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[Any]:
        """Get memory entries with optional filters."""

    @abstractmethod
    def update_memory_entry(
        self,
        entry_id: int,
        content: str | None = None,
        importance_score: float | None = None,
        is_active: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any | None:
        """Update a memory entry. Returns the updated entry or None."""

    @abstractmethod
    def delete_memory_entry(self, entry_id: int) -> bool:
        """Delete a memory entry. Returns True if deleted."""

    @abstractmethod
    def deactivate_expired_entries(self) -> int:
        """Deactivate entries that have expired. Returns count deactivated."""

    @abstractmethod
    def create_conversation_context(
        self,
        session_id: str,
        patient_context_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create a new conversation context. Returns the created context."""

    @abstractmethod
    def get_conversation_context(self, session_id: str) -> Any | None:
        """Get a conversation context by session ID."""

    @abstractmethod
    def update_conversation_context(
        self,
        session_id: str,
        summary: str | None = None,
        status: str | None = None,
        participating_agents: list[str] | None = None,
    ) -> Any | None:
        """Update a conversation context. Returns the updated context or None."""

    @abstractmethod
    def create_entity_reference(
        self,
        memory_entry_id: int,
        entity_type: str,
        entity_value: str,
        normalized_value: str | None = None,
        confidence_score: float = 1.0,
        source_span: tuple[int, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create an entity reference linked to a memory entry."""

    @abstractmethod
    def get_entity_references(
        self,
        entity_type: str | None = None,
        entity_value: str | None = None,
        memory_entry_id: int | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Get entity references with optional filters."""

    @abstractmethod
    def search_entities(
        self,
        entity_type: str,
        search_value: str,
        min_confidence: float = 0.5,
        limit: int = 20,
    ) -> list[Any]:
        """Search for entities by type and value."""

    @abstractmethod
    def log_access(
        self,
        session_id: str,
        agent_role: str,
        operation: str,
        memory_type: str,
        target_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Log a memory access operation."""

    @abstractmethod
    def get_access_logs(
        self,
        session_id: str | None = None,
        agent_role: str | None = None,
        operation: str | None = None,
        since: Any | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Get access logs with optional filters."""

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get memory store statistics."""
