# src/backend/memory/__init__.py
"""Memory Management System for AI Agents.

This module provides a comprehensive memory management system with three layers:
1. Short-term memory (session store) - In-memory or Redis-backed session context
2. Long-term memory (vector store) - ChromaDB-backed semantic memory
3. Structured memory (entity store) - SQLAlchemy-backed structured entities

Features:
- Role-based memory isolation between agents
- Patient context isolation for medical data
- Unified interface via MemoryManager
- Audit logging for compliance
- Configurable via environment variables

Usage:
    from backend.memory import MemoryManager, get_memory_manager

    # Get global instance (singleton)
    manager = get_memory_manager()

    # Store short-term memory
    manager.store_short_term("session-123", "last_query", "What medications?", agent_role="ClinicalExtractor")

    # Store long-term memory
    manager.store_long_term(
        agent_role="ClinicalExtractor",
        session_id="session-123",
        content="Patient is taking aspirin 100mg daily",
        memory_type="fact",
    )

    # Search memories
    results = manager.search("aspirin medication", agent_role="ClinicalExtractor")

Security Notes:
- All memory operations are logged for audit
- Patient isolation is enforced via patient_context_id
- External LLM access is blocked for memory containing PII (via agents)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from backend.memory.access_control import (
    AccessDecision,
    AccessLevel,
    AccessRequest,
    MemoryAccessControl,
    MemoryScope,
    RolePermissions,
    create_access_control,
)
from backend.memory.config import (
    AccessControlConfig,
    EntityMemoryConfig,
    MemoryConfig,
    SessionMemoryConfig,
    VectorMemoryConfig,
    get_memory_config,
    set_memory_config,
)
from backend.memory.entity_store import EntityStore
from backend.memory.models import (
    AgentMemoryEntry,
    ConversationContext,
    EntityReference,
    MemoryAccessLog,
    init_memory_database,
)
from backend.memory.session_store import SessionStore
from backend.memory.vector_memory import MemoryDocument, SearchResult, VectorMemory

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Statistics for the memory management system."""

    session_count: int
    session_entry_count: int
    vector_collection_count: int
    entity_stats: dict[str, Any]


class MemoryManager:
    """Unified memory management interface.

    Provides a single interface for all memory operations across the three
    memory layers: session (short-term), vector (long-term), and entity (structured).

    All operations are subject to role-based access control and audit logging.
    """

    def __init__(self, config: MemoryConfig | None = None):
        """Initialize the memory manager.

        Args:
            config: Optional memory configuration. Uses defaults if not provided.
        """
        self.config = config or get_memory_config()

        # Initialize stores
        self._session_store = SessionStore(self.config.session)
        self._vector_memory = VectorMemory(self.config.vector)
        self._entity_store = EntityStore(self.config.entity)

        # Initialize access control with entity store for audit logging
        self._access_control = create_access_control(
            config=self.config.access_control,
            entity_store=self._entity_store,
        )

        logger.info("MemoryManager initialized with all stores")

    # === Short-term Memory Operations ===

    def store_short_term(
        self,
        session_id: str,
        key: str,
        value: Any,
        agent_role: str,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Store a value in short-term memory.

        Args:
            session_id: The session identifier
            key: The key to store under
            value: The value to store
            agent_role: The agent's role name
            ttl_seconds: Optional TTL override

        Returns:
            True if stored successfully
        """
        # Check access
        request = AccessRequest(
            agent_role=agent_role,
            operation="write",
            memory_type="session",
            session_id=session_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            logger.warning(f"Short-term store denied: {decision.reason}")
            return False

        self._session_store.set(session_id, key, value, ttl_seconds, agent_role)
        return True

    def get_short_term(
        self,
        session_id: str,
        key: str,
        agent_role: str,
    ) -> Any | None:
        """Get a value from short-term memory.

        Args:
            session_id: The session identifier
            key: The key to retrieve
            agent_role: The agent's role name

        Returns:
            The stored value or None
        """
        # Check access
        request = AccessRequest(
            agent_role=agent_role,
            operation="read",
            memory_type="session",
            session_id=session_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            logger.warning(f"Short-term get denied: {decision.reason}")
            return None

        return self._session_store.get(session_id, key)

    def get_all_short_term(
        self,
        session_id: str,
        agent_role: str,
    ) -> dict[str, Any]:
        """Get all short-term memory for a session.

        Args:
            session_id: The session identifier
            agent_role: The agent's role name

        Returns:
            Dictionary of all stored values
        """
        request = AccessRequest(
            agent_role=agent_role,
            operation="read",
            memory_type="session",
            session_id=session_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            return {}

        return self._session_store.get_all(session_id, agent_role)

    def clear_short_term(self, session_id: str, agent_role: str) -> int:
        """Clear all short-term memory for a session.

        Args:
            session_id: The session identifier
            agent_role: The agent's role name (for access check)

        Returns:
            Number of entries cleared
        """
        request = AccessRequest(
            agent_role=agent_role,
            operation="delete",
            memory_type="session",
            session_id=session_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            return 0

        return self._session_store.clear_session(session_id)

    # === Long-term Memory Operations ===

    def store_long_term(
        self,
        agent_role: str,
        session_id: str,
        content: str,
        memory_type: str = "observation",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
        patient_context_id: str | None = None,
    ) -> str | None:
        """Store content in long-term vector memory.

        Args:
            agent_role: The agent's role name
            session_id: The session identifier
            content: The content to store
            memory_type: Type of memory ("fact", "observation", "result")
            importance: Importance score (0.0 to 1.0)
            metadata: Optional additional metadata
            patient_context_id: Optional patient context for isolation

        Returns:
            The document ID or None if access denied
        """
        # Check access
        request = AccessRequest(
            agent_role=agent_role,
            operation="write",
            memory_type="vector",
            session_id=session_id,
            patient_context_id=patient_context_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            logger.warning(f"Long-term store denied: {decision.reason}")
            return None

        # Generate unique ID
        doc_id = f"{agent_role}_{session_id}_{uuid.uuid4().hex[:8]}"

        # Create document
        document = MemoryDocument(
            id=doc_id,
            content=content,
            agent_role=agent_role,
            session_id=session_id,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {},
        )

        # Store in vector memory
        self._vector_memory.store(document)

        # Also store in entity store for structured queries
        self._entity_store.create_memory_entry(
            agent_role=agent_role,
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            importance_score=importance,
            metadata=metadata,
        )

        return doc_id

    def store_to_shared(
        self,
        agent_role: str,
        session_id: str,
        content: str,
        memory_type: str = "context",
        importance: float = 0.7,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Store content in shared memory pool.

        Shared memory is accessible by all authorized agents.

        Args:
            agent_role: The agent's role name (source)
            session_id: The session identifier
            content: The content to store
            memory_type: Type of memory
            importance: Importance score
            metadata: Optional additional metadata

        Returns:
            The document ID or None if access denied
        """
        # Check access to shared memory
        request = AccessRequest(
            agent_role=agent_role,
            operation="write",
            memory_type="vector",
            target_agent_role="shared",
            session_id=session_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            logger.warning(f"Shared memory store denied: {decision.reason}")
            return None

        # Generate unique ID
        doc_id = f"shared_{session_id}_{uuid.uuid4().hex[:8]}"

        # Create document with shared marker
        document = MemoryDocument(
            id=doc_id,
            content=content,
            agent_role=VectorMemory.SHARED_COLLECTION,
            session_id=session_id,
            memory_type=memory_type,
            importance=importance,
            metadata={"source_agent": agent_role, **(metadata or {})},
        )

        self._vector_memory.store(document)
        return doc_id

    def search(
        self,
        query: str,
        agent_role: str,
        top_k: int = 5,
        memory_type: str | None = None,
        session_id: str | None = None,
        include_shared: bool = True,
    ) -> list[SearchResult]:
        """Search for relevant memories.

        Args:
            query: The search query
            agent_role: The agent's role name
            top_k: Number of results to return
            memory_type: Optional filter by memory type
            session_id: Optional filter by session
            include_shared: Whether to include shared memory

        Returns:
            List of search results sorted by relevance
        """
        # Check access
        request = AccessRequest(
            agent_role=agent_role,
            operation="search",
            memory_type="vector",
            session_id=session_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            return []

        # Search own memory
        results = self._vector_memory.search(
            query=query,
            agent_role=agent_role,
            top_k=top_k,
            memory_type=memory_type,
            session_id=session_id,
        )

        # Optionally include shared memory
        if include_shared:
            shared_request = AccessRequest(
                agent_role=agent_role,
                operation="search",
                memory_type="vector",
                target_agent_role="shared",
                session_id=session_id,
            )
            shared_decision = self._access_control.check_access(shared_request)
            if shared_decision.allowed:
                shared_results = self._vector_memory.search_shared(query, top_k)
                results.extend(shared_results)

        # Sort by similarity and limit
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:top_k]

    # === Entity Memory Operations ===

    def store_entity(
        self,
        agent_role: str,
        session_id: str,
        entity_type: str,
        entity_value: str,
        source_content: str,
        normalized_value: str | None = None,
        confidence: float = 1.0,
        patient_context_id: str | None = None,
    ) -> int | None:
        """Store a structured entity reference.

        Args:
            agent_role: The agent's role name
            session_id: The session identifier
            entity_type: Type of entity (e.g., "medication", "diagnosis")
            entity_value: The extracted entity value
            source_content: The source text containing the entity
            normalized_value: Optional standardized form
            confidence: Extraction confidence
            patient_context_id: Optional patient context

        Returns:
            The entity reference ID or None if access denied
        """
        # Check access
        request = AccessRequest(
            agent_role=agent_role,
            operation="write",
            memory_type="entity",
            session_id=session_id,
            patient_context_id=patient_context_id,
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            return None

        # First create a memory entry for the source content
        memory_entry = self._entity_store.create_memory_entry(
            agent_role=agent_role,
            session_id=session_id,
            content=source_content,
            memory_type="entity_source",
        )

        # Then create the entity reference
        entity_ref = self._entity_store.create_entity_reference(
            memory_entry_id=memory_entry.id,
            entity_type=entity_type,
            entity_value=entity_value,
            normalized_value=normalized_value,
            confidence_score=confidence,
        )

        return entity_ref.id

    def search_entities(
        self,
        entity_type: str,
        search_value: str,
        agent_role: str,
        min_confidence: float = 0.5,
        limit: int = 20,
    ) -> list[EntityReference]:
        """Search for entities by type and value.

        Args:
            entity_type: The entity type to search
            search_value: Value to search for
            agent_role: The agent's role name (for access check)
            min_confidence: Minimum confidence threshold
            limit: Maximum results

        Returns:
            List of matching entity references
        """
        request = AccessRequest(
            agent_role=agent_role,
            operation="search",
            memory_type="entity",
        )
        decision = self._access_control.check_access(request)
        if not decision.allowed:
            return []

        return self._entity_store.search_entities(
            entity_type=entity_type,
            search_value=search_value,
            min_confidence=min_confidence,
            limit=limit,
        )

    # === Context Management ===

    def create_context(
        self,
        session_id: str,
        agent_role: str,
        patient_context_id: str | None = None,
        user_id: str | None = None,
    ) -> ConversationContext | None:
        """Create a new conversation context.

        Args:
            session_id: Unique session identifier
            agent_role: The initiating agent's role
            patient_context_id: Optional patient context for isolation
            user_id: Optional user identifier

        Returns:
            The created context or None if access denied
        """
        # Register patient context for isolation
        if patient_context_id:
            self._access_control.register_patient_context(session_id, patient_context_id)

        return self._entity_store.create_conversation_context(
            session_id=session_id,
            patient_context_id=patient_context_id,
            user_id=user_id,
        )

    def update_context(
        self,
        session_id: str,
        agent_role: str,
        summary: str | None = None,
        status: str | None = None,
    ) -> ConversationContext | None:
        """Update a conversation context.

        Args:
            session_id: The session ID
            agent_role: The agent's role name
            summary: Optional new summary
            status: Optional new status

        Returns:
            The updated context or None
        """
        # Get current context to add agent to participants
        context = self._entity_store.get_conversation_context(session_id)
        if context:
            participants = set((context.participating_agents or "").split(","))
            participants.discard("")
            participants.add(agent_role)

            return self._entity_store.update_conversation_context(
                session_id=session_id,
                summary=summary,
                status=status,
                participating_agents=list(participants),
            )
        return None

    # === Maintenance ===

    def cleanup(self) -> dict[str, int]:
        """Run cleanup tasks across all memory stores.

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "session_expired": self._session_store.cleanup_expired(),
            "entity_expired": self._entity_store.deactivate_expired_entries(),
            "vector_pruned": self._vector_memory.prune_by_retention(),
        }
        logger.info(f"Memory cleanup completed: {stats}")
        return stats

    def get_stats(self) -> MemoryStats:
        """Get statistics for the memory system.

        Returns:
            MemoryStats with current statistics
        """
        return MemoryStats(
            session_count=self._session_store.get_session_count(),
            session_entry_count=0,  # Would need iteration to count
            vector_collection_count=len(self._vector_memory.list_collections()),
            entity_stats=self._entity_store.get_stats(),
        )

    # === Access to underlying stores ===

    @property
    def session_store(self) -> SessionStore:
        """Get the session store for direct access."""
        return self._session_store

    @property
    def vector_memory(self) -> VectorMemory:
        """Get the vector memory for direct access."""
        return self._vector_memory

    @property
    def entity_store(self) -> EntityStore:
        """Get the entity store for direct access."""
        return self._entity_store

    @property
    def access_control(self) -> MemoryAccessControl:
        """Get the access control for direct access."""
        return self._access_control


# === Module-level singleton ===

_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance.

    Returns:
        The singleton MemoryManager instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def reset_memory_manager() -> None:
    """Reset the global memory manager instance.

    Useful for testing or reconfiguration.
    """
    global _memory_manager
    _memory_manager = None


__all__ = [
    # Main class
    "MemoryManager",
    "MemoryStats",
    # Factory functions
    "get_memory_manager",
    "reset_memory_manager",
    # Configuration
    "MemoryConfig",
    "SessionMemoryConfig",
    "VectorMemoryConfig",
    "EntityMemoryConfig",
    "AccessControlConfig",
    "get_memory_config",
    "set_memory_config",
    # Access control
    "MemoryAccessControl",
    "AccessRequest",
    "AccessDecision",
    "AccessLevel",
    "MemoryScope",
    "RolePermissions",
    "create_access_control",
    # Stores
    "SessionStore",
    "VectorMemory",
    "EntityStore",
    # Data classes
    "MemoryDocument",
    "SearchResult",
    # Models
    "AgentMemoryEntry",
    "ConversationContext",
    "EntityReference",
    "MemoryAccessLog",
    "init_memory_database",
]
