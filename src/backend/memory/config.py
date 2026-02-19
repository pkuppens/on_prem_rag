# src/backend/memory/config.py
"""Configuration for the memory management system.

This module provides configuration dataclasses for all memory types:
- Short-term (session) memory
- Long-term (vector) memory
- Entity (structured) memory
- Role-based access control

All settings can be overridden via environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from backend.shared.utils.directory_utils import get_data_dir


@dataclass
class SessionMemoryConfig:
    """Configuration for short-term session memory."""

    # Session TTL in seconds (default 1 hour)
    ttl_seconds: int = int(os.getenv("MEMORY_SESSION_TTL", "3600"))

    # Backend type: "memory" (in-process dict) or "redis"
    backend: str = os.getenv("MEMORY_SESSION_BACKEND", "memory")

    # Redis configuration (only used if backend="redis")
    redis_url: str = os.getenv("MEMORY_REDIS_URL", "redis://localhost:6379/0")

    # Maximum entries per session before cleanup
    max_entries_per_session: int = int(os.getenv("MEMORY_SESSION_MAX_ENTRIES", "1000"))


@dataclass
class VectorMemoryConfig:
    """Configuration for long-term vector memory (ChromaDB)."""

    # Persist directory for ChromaDB
    persist_directory: Path = field(
        default_factory=lambda: Path(os.getenv("MEMORY_CHROMA_DIR", str(get_data_dir() / "memory" / "chroma")))
    )

    # Maximum memory entries per role/collection
    max_entries_per_role: int = int(os.getenv("MEMORY_MAX_ENTRIES_PER_ROLE", "10000"))

    # Retention period in days (0 = no auto-cleanup)
    retention_days: int = int(os.getenv("MEMORY_RETENTION_DAYS", "90"))

    # Default embedding model
    embedding_model: str = os.getenv("MEMORY_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ChromaDB collection prefix
    collection_prefix: str = os.getenv("MEMORY_COLLECTION_PREFIX", "agent_memory_")


@dataclass
class EntityMemoryConfig:
    """Configuration for structured entity memory (SQLAlchemy)."""

    # Database URL (defaults to SQLite in data directory)
    database_url: str = field(
        default_factory=lambda: os.getenv("MEMORY_DATABASE_URL", f"sqlite:///{get_data_dir() / 'memory' / 'entities.db'}")
    )

    # Maximum entity references per agent
    max_entities_per_agent: int = int(os.getenv("MEMORY_MAX_ENTITIES", "5000"))


@dataclass
class AccessControlConfig:
    """Configuration for role-based memory access control."""

    # Enable role-based memory isolation
    role_isolation_enabled: bool = os.getenv("MEMORY_ROLE_ISOLATION", "true").lower() == "true"

    # Enable shared memory pool across agents
    shared_memory_enabled: bool = os.getenv("MEMORY_SHARED_ENABLED", "true").lower() == "true"

    # Enable audit logging for memory access
    audit_logging_enabled: bool = os.getenv("MEMORY_AUDIT_LOGGING", "true").lower() == "true"

    # Roles allowed to access shared memory
    shared_memory_roles: list[str] = field(
        default_factory=lambda: os.getenv(
            "MEMORY_SHARED_ROLES",
            "PreprocessingAgent,LanguageAssessorAgent,ClinicalExtractorAgent,SummarizationAgent,QualityControlAgent",
        ).split(",")
    )


@dataclass
class MemoryConfig:
    """Top-level configuration for the memory management system."""

    session: SessionMemoryConfig = field(default_factory=SessionMemoryConfig)
    vector: VectorMemoryConfig = field(default_factory=VectorMemoryConfig)
    entity: EntityMemoryConfig = field(default_factory=EntityMemoryConfig)
    access_control: AccessControlConfig = field(default_factory=AccessControlConfig)

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """Create configuration from environment variables."""
        return cls(
            session=SessionMemoryConfig(),
            vector=VectorMemoryConfig(),
            entity=EntityMemoryConfig(),
            access_control=AccessControlConfig(),
        )


# Default global configuration instance
_default_config: MemoryConfig | None = None


def get_memory_config() -> MemoryConfig:
    """Get the default memory configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = MemoryConfig.from_env()
    return _default_config


def set_memory_config(config: MemoryConfig) -> None:
    """Set the default memory configuration instance."""
    global _default_config
    _default_config = config
