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

Architecture:
    memory/
        domain/
            value_objects.py     # MemoryDocument, SearchResult, AccessLevel, etc.
            interfaces.py        # ISessionStore, IVectorMemory, IEntityStore ports
        application/
            memory_manager.py    # MemoryManager facade + singleton
            access_control.py    # Role-based access control
        infrastructure/
            session_store.py     # SessionStore (in-memory / Redis)
            vector_memory.py     # VectorMemory (ChromaDB)
            entity_store.py      # EntityStore (SQLAlchemy)
"""

from __future__ import annotations

# Application layer
from backend.memory.application.access_control import (
    AccessDecision,
    AccessRequest,
    MemoryAccessControl,
    MemoryScope,
    RolePermissions,
    create_access_control,
)
from backend.memory.application.memory_manager import (
    MemoryManager,
    MemoryStats,
    get_memory_manager,
    reset_memory_manager,
)

# Re-export from subpackages to maintain backward compatibility
# Configuration
from backend.memory.config import (
    AccessControlConfig,
    EntityMemoryConfig,
    MemoryConfig,
    SessionMemoryConfig,
    VectorMemoryConfig,
    get_memory_config,
    set_memory_config,
)

# Domain value objects
from backend.memory.domain.value_objects import AccessLevel, MemoryDocument, SearchResult

# Infrastructure stores
from backend.memory.infrastructure.entity_store import EntityStore
from backend.memory.infrastructure.session_store import SessionStore
from backend.memory.infrastructure.vector_memory import VectorMemory

# Models (SQLAlchemy ORM)
from backend.memory.models import (
    AgentMemoryEntry,
    ConversationContext,
    EntityReference,
    MemoryAccessLog,
    init_memory_database,
)

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
