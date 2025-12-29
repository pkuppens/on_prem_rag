# src/backend/memory/models.py
"""SQLAlchemy models for structured entity memory.

This module defines the database schema for storing structured memory entries,
conversation context, and entity references. It follows the same patterns
established in the WBSO database module.

Tables:
- AgentMemoryEntry: Individual memory entries from agents
- ConversationContext: Session-level conversation metadata
- EntityReference: Named entity references extracted from text
- MemoryAccessLog: Audit log for memory access operations
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    relationship,
    sessionmaker,
)

from backend.rag_pipeline.utils.directory_utils import ensure_directory_exists, get_data_dir

# Ensure memory database directory exists
memory_dir = get_data_dir() / "memory"
ensure_directory_exists(memory_dir)

# Database configuration
MEMORY_DATABASE_URL = f"sqlite:///{memory_dir / 'entities.db'}"
engine = create_engine(MEMORY_DATABASE_URL, connect_args={"check_same_thread": False})
MemorySessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class AgentMemoryEntry(Base):
    """Individual memory entry from an agent.

    Stores discrete pieces of information learned by agents during processing,
    such as extracted facts, observations, or intermediate results.
    """

    __tablename__ = "agent_memory_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "fact", "observation", "result"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON string for flexible metadata
    source_document_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_memory_agent_session", "agent_role", "session_id"),
        Index("ix_memory_type_active", "memory_type", "is_active"),
    )

    # Relationships
    entity_references: Mapped[list["EntityReference"]] = relationship(
        "EntityReference", back_populates="memory_entry", cascade="all, delete-orphan"
    )


class ConversationContext(Base):
    """Session-level conversation metadata and context.

    Tracks high-level information about a conversation/processing session,
    including which agents participated and overall status.
    """

    __tablename__ = "conversation_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    patient_context_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # For patient isolation
    user_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    participating_agents: Mapped[Optional[str]] = mapped_column(Text)  # Comma-separated agent roles
    status: Mapped[str] = mapped_column(String(50), default="active")  # "active", "completed", "archived"
    total_memory_entries: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class EntityReference(Base):
    """Named entity references extracted from text.

    Stores structured information about entities (persons, medications,
    diagnoses, etc.) extracted during processing for later retrieval.
    """

    __tablename__ = "entity_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    memory_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_memory_entries.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # "medication", "diagnosis", etc.
    entity_value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[Optional[str]] = mapped_column(String(500))  # Standardized form
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    source_span_start: Mapped[Optional[int]] = mapped_column(Integer)
    source_span_end: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Indexes
    __table_args__ = (Index("ix_entity_type_value", "entity_type", "entity_value"),)

    # Relationships
    memory_entry: Mapped["AgentMemoryEntry"] = relationship("AgentMemoryEntry", back_populates="entity_references")


class MemoryAccessLog(Base):
    """Audit log for memory access operations.

    Tracks all read/write operations to memory for compliance and debugging.
    Required for GDPR compliance and patient data isolation verification.
    """

    __tablename__ = "memory_access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    agent_role: Mapped[str] = mapped_column(String(100), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)  # "read", "write", "delete", "search"
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "session", "vector", "entity"
    target_id: Mapped[Optional[str]] = mapped_column(String(255))  # ID of accessed resource
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Index for audit queries
    __table_args__ = (Index("ix_access_log_session_time", "session_id", "timestamp"),)


def init_memory_database() -> None:
    """Initialize the memory database with all tables."""
    Base.metadata.create_all(bind=engine)


def get_memory_session() -> Session:
    """Get a database session for memory operations."""
    return MemorySessionLocal()


def close_memory_session(session: Session) -> None:
    """Close a database session."""
    session.close()


def get_engine_for_url(database_url: str):
    """Create a new engine for a custom database URL."""
    return create_engine(database_url, connect_args={"check_same_thread": False})


def create_session_factory(database_url: str):
    """Create a session factory for a custom database URL."""
    custom_engine = get_engine_for_url(database_url)
    Base.metadata.create_all(bind=custom_engine)
    return sessionmaker(bind=custom_engine, autoflush=False)


# Initialize database on module import
init_memory_database()
