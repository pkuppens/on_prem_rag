# tests/backend/memory/test_entity_store.py
"""Unit tests for entity store (structured memory).

Tests cover:
- Memory entry CRUD operations
- Conversation context management
- Entity reference storage
- Access logging
"""

from datetime import UTC, datetime, timedelta

import pytest

from backend.memory.config import EntityMemoryConfig
from backend.memory.entity_store import EntityStore


class TestEntityStore:
    """Tests for EntityStore."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a fresh entity store with temp database."""
        db_path = tmp_path / "test_entities.db"
        config = EntityMemoryConfig(database_url=f"sqlite:///{db_path}")
        return EntityStore(config)

    # === Memory Entry Tests ===

    def test_create_memory_entry(self, store):
        """Should create memory entries successfully."""
        entry = store.create_memory_entry(
            agent_role="TestAgent",
            session_id="session-123",
            content="Test content",
            memory_type="fact",
            importance_score=0.8,
        )

        assert entry.id is not None
        assert entry.agent_role == "TestAgent"
        assert entry.session_id == "session-123"
        assert entry.content == "Test content"
        assert entry.memory_type == "fact"
        assert entry.importance_score == 0.8
        assert entry.is_active is True

    def test_get_memory_entry(self, store):
        """Should retrieve memory entries by ID."""
        created = store.create_memory_entry(
            agent_role="TestAgent",
            session_id="session-123",
            content="Test content",
        )

        retrieved = store.get_memory_entry(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Test content"

    def test_get_memory_entry_not_found(self, store):
        """Should return None for nonexistent entry."""
        assert store.get_memory_entry(99999) is None

    def test_get_memory_entries_by_agent(self, store):
        """Should filter entries by agent role."""
        store.create_memory_entry(agent_role="AgentA", session_id="s1", content="A1")
        store.create_memory_entry(agent_role="AgentA", session_id="s1", content="A2")
        store.create_memory_entry(agent_role="AgentB", session_id="s1", content="B1")

        entries = store.get_memory_entries(agent_role="AgentA")
        assert len(entries) == 2
        assert all(e.agent_role == "AgentA" for e in entries)

    def test_get_memory_entries_by_session(self, store):
        """Should filter entries by session ID."""
        store.create_memory_entry(agent_role="Agent", session_id="s1", content="S1")
        store.create_memory_entry(agent_role="Agent", session_id="s2", content="S2")

        entries = store.get_memory_entries(session_id="s1")
        assert len(entries) == 1
        assert entries[0].session_id == "s1"

    def test_get_memory_entries_by_type(self, store):
        """Should filter entries by memory type."""
        store.create_memory_entry(agent_role="Agent", session_id="s1", content="F1", memory_type="fact")
        store.create_memory_entry(agent_role="Agent", session_id="s1", content="O1", memory_type="observation")

        entries = store.get_memory_entries(memory_type="fact")
        assert len(entries) == 1
        assert entries[0].memory_type == "fact"

    def test_update_memory_entry(self, store):
        """Should update memory entry fields."""
        entry = store.create_memory_entry(
            agent_role="Agent",
            session_id="s1",
            content="Original",
            importance_score=0.5,
        )

        updated = store.update_memory_entry(
            entry.id,
            content="Updated",
            importance_score=0.9,
        )

        assert updated is not None
        assert updated.content == "Updated"
        assert updated.importance_score == 0.9

    def test_delete_memory_entry(self, store):
        """Should delete memory entries."""
        entry = store.create_memory_entry(agent_role="Agent", session_id="s1", content="Test")

        assert store.delete_memory_entry(entry.id) is True
        assert store.get_memory_entry(entry.id) is None

    def test_deactivate_expired_entries(self, store):
        """Should deactivate expired entries."""
        # Create entry that expires in the past
        past = datetime.now(UTC) - timedelta(hours=1)
        entry = store.create_memory_entry(
            agent_role="Agent",
            session_id="s1",
            content="Expired",
            expires_at=past,
        )

        # Create entry that doesn't expire
        store.create_memory_entry(
            agent_role="Agent",
            session_id="s1",
            content="Active",
        )

        count = store.deactivate_expired_entries()
        assert count == 1

        # Verify the expired entry is inactive
        entries = store.get_memory_entries(active_only=False)
        expired_entry = next(e for e in entries if e.id == entry.id)
        assert expired_entry.is_active is False

    # === Conversation Context Tests ===

    def test_create_conversation_context(self, store):
        """Should create conversation contexts."""
        context = store.create_conversation_context(
            session_id="session-123",
            patient_context_id="patient-456",
            user_id="user-789",
        )

        assert context.id is not None
        assert context.session_id == "session-123"
        assert context.patient_context_id == "patient-456"
        assert context.user_id == "user-789"
        assert context.status == "active"

    def test_get_conversation_context(self, store):
        """Should retrieve conversation context by session ID."""
        store.create_conversation_context(session_id="session-123")

        context = store.get_conversation_context("session-123")
        assert context is not None
        assert context.session_id == "session-123"

    def test_update_conversation_context(self, store):
        """Should update conversation context."""
        store.create_conversation_context(session_id="session-123")

        updated = store.update_conversation_context(
            session_id="session-123",
            summary="Test summary",
            status="completed",
            participating_agents=["AgentA", "AgentB"],
        )

        assert updated is not None
        assert updated.summary == "Test summary"
        assert updated.status == "completed"
        assert updated.participating_agents == "AgentA,AgentB"
        assert updated.completed_at is not None

    # === Entity Reference Tests ===

    def test_create_entity_reference(self, store):
        """Should create entity references."""
        entry = store.create_memory_entry(agent_role="Agent", session_id="s1", content="Test")

        entity = store.create_entity_reference(
            memory_entry_id=entry.id,
            entity_type="medication",
            entity_value="aspirin",
            normalized_value="Aspirin",
            confidence_score=0.95,
        )

        assert entity.id is not None
        assert entity.entity_type == "medication"
        assert entity.entity_value == "aspirin"
        assert entity.normalized_value == "Aspirin"
        assert entity.confidence_score == 0.95

    def test_get_entity_references(self, store):
        """Should retrieve entity references with filters."""
        entry = store.create_memory_entry(agent_role="Agent", session_id="s1", content="Test")

        store.create_entity_reference(memory_entry_id=entry.id, entity_type="medication", entity_value="aspirin")
        store.create_entity_reference(memory_entry_id=entry.id, entity_type="diagnosis", entity_value="headache")

        entities = store.get_entity_references(entity_type="medication")
        assert len(entities) == 1
        assert entities[0].entity_type == "medication"

    def test_search_entities(self, store):
        """Should search entities by value."""
        entry = store.create_memory_entry(agent_role="Agent", session_id="s1", content="Test")

        store.create_entity_reference(memory_entry_id=entry.id, entity_type="medication", entity_value="aspirin 100mg")
        store.create_entity_reference(memory_entry_id=entry.id, entity_type="medication", entity_value="ibuprofen 400mg")

        results = store.search_entities(entity_type="medication", search_value="aspirin")
        assert len(results) == 1
        assert "aspirin" in results[0].entity_value

    # === Access Log Tests ===

    def test_log_access(self, store):
        """Should log memory access operations."""
        log = store.log_access(
            session_id="session-123",
            agent_role="TestAgent",
            operation="read",
            memory_type="entity",
            target_id="entry-456",
            success=True,
        )

        assert log.id is not None
        assert log.session_id == "session-123"
        assert log.agent_role == "TestAgent"
        assert log.operation == "read"
        assert log.success is True

    def test_get_access_logs(self, store):
        """Should retrieve access logs with filters."""
        store.log_access(session_id="s1", agent_role="AgentA", operation="read", memory_type="entity", success=True)
        store.log_access(session_id="s1", agent_role="AgentB", operation="write", memory_type="entity", success=True)

        logs = store.get_access_logs(agent_role="AgentA")
        assert len(logs) == 1
        assert logs[0].agent_role == "AgentA"

    # === Statistics Tests ===

    def test_get_stats(self, store):
        """Should return correct statistics."""
        store.create_memory_entry(agent_role="Agent", session_id="s1", content="Test")
        store.create_conversation_context(session_id="s1")

        stats = store.get_stats()
        assert stats["total_memory_entries"] == 1
        assert stats["total_contexts"] == 1
