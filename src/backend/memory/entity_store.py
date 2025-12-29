# src/backend/memory/entity_store.py
"""Structured entity memory store using SQLAlchemy.

Provides CRUD operations for structured memory entries, conversation contexts,
and entity references. Uses the same patterns as the WBSO database module.

Features:
- Agent memory entry management
- Conversation context tracking
- Entity reference storage and lookup
- Audit logging for memory operations
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from backend.memory.config import EntityMemoryConfig, get_memory_config
from backend.memory.models import (
    AgentMemoryEntry,
    ConversationContext,
    EntityReference,
    MemoryAccessLog,
    create_session_factory,
    get_memory_session,
)

logger = logging.getLogger(__name__)


class EntityStore:
    """Structured entity memory store.

    Provides CRUD operations for SQLAlchemy-backed memory storage.
    Handles agent memory entries, conversation contexts, and entity references.
    """

    def __init__(self, config: EntityMemoryConfig | None = None):
        self.config = config or get_memory_config().entity
        self._session_factory = None

        # Always create custom session factory when config is provided
        # This ensures test isolation and custom database paths work correctly
        if config is not None:
            self._session_factory = create_session_factory(self.config.database_url)

    def _get_session(self) -> Session:
        """Get a database session."""
        if self._session_factory:
            return self._session_factory()
        return get_memory_session()

    # === Memory Entry Operations ===

    def create_memory_entry(
        self,
        agent_role: str,
        session_id: str,
        content: str,
        memory_type: str = "observation",
        importance_score: float = 0.5,
        metadata: dict[str, Any] | None = None,
        source_document_id: str | None = None,
        expires_at: datetime | None = None,
    ) -> AgentMemoryEntry:
        """Create a new memory entry.

        Args:
            agent_role: The agent's role name
            session_id: The session ID
            content: The memory content
            memory_type: Type of memory ("fact", "observation", "result")
            importance_score: Importance score (0.0 to 1.0)
            metadata: Optional metadata dictionary
            source_document_id: Optional source document reference
            expires_at: Optional expiration datetime

        Returns:
            The created AgentMemoryEntry
        """
        session = self._get_session()
        try:
            entry = AgentMemoryEntry(
                agent_role=agent_role,
                session_id=session_id,
                memory_type=memory_type,
                content=content,
                importance_score=importance_score,
                metadata_json=json.dumps(metadata) if metadata else None,
                source_document_id=source_document_id,
                expires_at=expires_at,
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)

            # Update conversation context entry count
            self._update_context_entry_count(session, session_id)

            logger.debug(f"Created memory entry {entry.id} for {agent_role}")
            return entry
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create memory entry: {e}")
            raise
        finally:
            session.close()

    def get_memory_entry(self, entry_id: int) -> AgentMemoryEntry | None:
        """Get a memory entry by ID."""
        session = self._get_session()
        try:
            return session.query(AgentMemoryEntry).filter(AgentMemoryEntry.id == entry_id).first()
        finally:
            session.close()

    def get_memory_entries(
        self,
        agent_role: str | None = None,
        session_id: str | None = None,
        memory_type: str | None = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[AgentMemoryEntry]:
        """Get memory entries with optional filters.

        Args:
            agent_role: Filter by agent role
            session_id: Filter by session ID
            memory_type: Filter by memory type
            active_only: Only return active entries
            limit: Maximum number of entries to return

        Returns:
            List of matching memory entries
        """
        session = self._get_session()
        try:
            query = session.query(AgentMemoryEntry)

            if agent_role:
                query = query.filter(AgentMemoryEntry.agent_role == agent_role)
            if session_id:
                query = query.filter(AgentMemoryEntry.session_id == session_id)
            if memory_type:
                query = query.filter(AgentMemoryEntry.memory_type == memory_type)
            if active_only:
                query = query.filter(AgentMemoryEntry.is_active == True)  # noqa: E712

            return query.order_by(AgentMemoryEntry.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def update_memory_entry(
        self,
        entry_id: int,
        content: str | None = None,
        importance_score: float | None = None,
        is_active: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentMemoryEntry | None:
        """Update a memory entry.

        Args:
            entry_id: The entry ID to update
            content: New content (optional)
            importance_score: New importance score (optional)
            is_active: New active status (optional)
            metadata: New metadata (optional)

        Returns:
            The updated entry or None if not found
        """
        session = self._get_session()
        try:
            entry = session.query(AgentMemoryEntry).filter(AgentMemoryEntry.id == entry_id).first()
            if not entry:
                return None

            if content is not None:
                entry.content = content
            if importance_score is not None:
                entry.importance_score = importance_score
            if is_active is not None:
                entry.is_active = is_active
            if metadata is not None:
                entry.metadata_json = json.dumps(metadata)

            session.commit()
            session.refresh(entry)
            return entry
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update memory entry {entry_id}: {e}")
            raise
        finally:
            session.close()

    def delete_memory_entry(self, entry_id: int) -> bool:
        """Delete a memory entry.

        Args:
            entry_id: The entry ID to delete

        Returns:
            True if entry was deleted
        """
        session = self._get_session()
        try:
            entry = session.query(AgentMemoryEntry).filter(AgentMemoryEntry.id == entry_id).first()
            if not entry:
                return False

            session_id = entry.session_id
            session.delete(entry)
            session.commit()

            # Update conversation context entry count
            self._update_context_entry_count(session, session_id)

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete memory entry {entry_id}: {e}")
            raise
        finally:
            session.close()

    def deactivate_expired_entries(self) -> int:
        """Deactivate entries that have expired.

        Returns:
            Number of entries deactivated
        """
        session = self._get_session()
        try:
            now = datetime.now(UTC)
            result = (
                session.query(AgentMemoryEntry)
                .filter(
                    and_(
                        AgentMemoryEntry.is_active == True,  # noqa: E712
                        AgentMemoryEntry.expires_at != None,  # noqa: E711
                        AgentMemoryEntry.expires_at < now,
                    )
                )
                .update({"is_active": False})
            )
            session.commit()

            if result > 0:
                logger.info(f"Deactivated {result} expired memory entries")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to deactivate expired entries: {e}")
            raise
        finally:
            session.close()

    # === Conversation Context Operations ===

    def create_conversation_context(
        self,
        session_id: str,
        patient_context_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationContext:
        """Create a new conversation context.

        Args:
            session_id: Unique session identifier
            patient_context_id: Optional patient context for isolation
            user_id: Optional user identifier
            metadata: Optional metadata dictionary

        Returns:
            The created ConversationContext
        """
        session = self._get_session()
        try:
            context = ConversationContext(
                session_id=session_id,
                patient_context_id=patient_context_id,
                user_id=user_id,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            session.add(context)
            session.commit()
            session.refresh(context)
            return context
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create conversation context: {e}")
            raise
        finally:
            session.close()

    def get_conversation_context(self, session_id: str) -> ConversationContext | None:
        """Get a conversation context by session ID."""
        session = self._get_session()
        try:
            return session.query(ConversationContext).filter(ConversationContext.session_id == session_id).first()
        finally:
            session.close()

    def update_conversation_context(
        self,
        session_id: str,
        summary: str | None = None,
        status: str | None = None,
        participating_agents: list[str] | None = None,
    ) -> ConversationContext | None:
        """Update a conversation context.

        Args:
            session_id: The session ID
            summary: New summary (optional)
            status: New status (optional)
            participating_agents: List of agent roles (optional)

        Returns:
            The updated context or None if not found
        """
        session = self._get_session()
        try:
            context = session.query(ConversationContext).filter(ConversationContext.session_id == session_id).first()
            if not context:
                return None

            if summary is not None:
                context.summary = summary
            if status is not None:
                context.status = status
                if status == "completed":
                    context.completed_at = datetime.now(UTC)
            if participating_agents is not None:
                context.participating_agents = ",".join(participating_agents)

            context.last_activity_at = datetime.now(UTC)
            session.commit()
            session.refresh(context)
            return context
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update conversation context {session_id}: {e}")
            raise
        finally:
            session.close()

    def _update_context_entry_count(self, session: Session, session_id: str) -> None:
        """Update the total_memory_entries count for a context."""
        context = session.query(ConversationContext).filter(ConversationContext.session_id == session_id).first()
        if context:
            count = session.query(func.count(AgentMemoryEntry.id)).filter(AgentMemoryEntry.session_id == session_id).scalar()
            context.total_memory_entries = count
            context.last_activity_at = datetime.now(UTC)

    # === Entity Reference Operations ===

    def create_entity_reference(
        self,
        memory_entry_id: int,
        entity_type: str,
        entity_value: str,
        normalized_value: str | None = None,
        confidence_score: float = 1.0,
        source_span: tuple[int, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EntityReference:
        """Create an entity reference linked to a memory entry.

        Args:
            memory_entry_id: The parent memory entry ID
            entity_type: Type of entity (e.g., "medication", "diagnosis")
            entity_value: The extracted entity value
            normalized_value: Optional standardized form
            confidence_score: Extraction confidence (0.0 to 1.0)
            source_span: Optional (start, end) character positions
            metadata: Optional metadata dictionary

        Returns:
            The created EntityReference
        """
        session = self._get_session()
        try:
            entity = EntityReference(
                memory_entry_id=memory_entry_id,
                entity_type=entity_type,
                entity_value=entity_value,
                normalized_value=normalized_value,
                confidence_score=confidence_score,
                source_span_start=source_span[0] if source_span else None,
                source_span_end=source_span[1] if source_span else None,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create entity reference: {e}")
            raise
        finally:
            session.close()

    def get_entity_references(
        self,
        entity_type: str | None = None,
        entity_value: str | None = None,
        memory_entry_id: int | None = None,
        limit: int = 100,
    ) -> list[EntityReference]:
        """Get entity references with optional filters.

        Args:
            entity_type: Filter by entity type
            entity_value: Filter by entity value (partial match)
            memory_entry_id: Filter by parent memory entry
            limit: Maximum number of results

        Returns:
            List of matching entity references
        """
        session = self._get_session()
        try:
            query = session.query(EntityReference)

            if entity_type:
                query = query.filter(EntityReference.entity_type == entity_type)
            if entity_value:
                query = query.filter(EntityReference.entity_value.ilike(f"%{entity_value}%"))
            if memory_entry_id:
                query = query.filter(EntityReference.memory_entry_id == memory_entry_id)

            return query.order_by(EntityReference.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def search_entities(
        self,
        entity_type: str,
        search_value: str,
        min_confidence: float = 0.5,
        limit: int = 20,
    ) -> list[EntityReference]:
        """Search for entities by type and value.

        Args:
            entity_type: The entity type to search
            search_value: Value to search for (partial match)
            min_confidence: Minimum confidence threshold
            limit: Maximum results

        Returns:
            List of matching entity references
        """
        session = self._get_session()
        try:
            return (
                session.query(EntityReference)
                .filter(
                    and_(
                        EntityReference.entity_type == entity_type,
                        EntityReference.entity_value.ilike(f"%{search_value}%"),
                        EntityReference.confidence_score >= min_confidence,
                    )
                )
                .order_by(EntityReference.confidence_score.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    # === Access Log Operations ===

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
    ) -> MemoryAccessLog:
        """Log a memory access operation.

        Args:
            session_id: The session ID
            agent_role: The agent performing the operation
            operation: Type of operation ("read", "write", "delete", "search")
            memory_type: Type of memory accessed
            target_id: Optional target resource ID
            success: Whether operation succeeded
            error_message: Error message if operation failed
            metadata: Optional metadata

        Returns:
            The created access log entry
        """
        session = self._get_session()
        try:
            log = MemoryAccessLog(
                session_id=session_id,
                agent_role=agent_role,
                operation=operation,
                memory_type=memory_type,
                target_id=target_id,
                success=success,
                error_message=error_message,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log memory access: {e}")
            raise
        finally:
            session.close()

    def get_access_logs(
        self,
        session_id: str | None = None,
        agent_role: str | None = None,
        operation: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[MemoryAccessLog]:
        """Get access logs with optional filters.

        Args:
            session_id: Filter by session ID
            agent_role: Filter by agent role
            operation: Filter by operation type
            since: Only logs after this datetime
            limit: Maximum results

        Returns:
            List of matching access log entries
        """
        session = self._get_session()
        try:
            query = session.query(MemoryAccessLog)

            if session_id:
                query = query.filter(MemoryAccessLog.session_id == session_id)
            if agent_role:
                query = query.filter(MemoryAccessLog.agent_role == agent_role)
            if operation:
                query = query.filter(MemoryAccessLog.operation == operation)
            if since:
                query = query.filter(MemoryAccessLog.timestamp >= since)

            return query.order_by(MemoryAccessLog.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    # === Statistics ===

    def get_stats(self) -> dict[str, Any]:
        """Get memory store statistics.

        Returns:
            Dictionary with store statistics
        """
        session = self._get_session()
        try:
            return {
                "total_memory_entries": session.query(func.count(AgentMemoryEntry.id)).scalar(),
                "active_memory_entries": session.query(func.count(AgentMemoryEntry.id))
                .filter(AgentMemoryEntry.is_active == True)  # noqa: E712
                .scalar(),
                "total_contexts": session.query(func.count(ConversationContext.id)).scalar(),
                "active_contexts": session.query(func.count(ConversationContext.id))
                .filter(ConversationContext.status == "active")
                .scalar(),
                "total_entities": session.query(func.count(EntityReference.id)).scalar(),
                "total_access_logs": session.query(func.count(MemoryAccessLog.id)).scalar(),
            }
        finally:
            session.close()
