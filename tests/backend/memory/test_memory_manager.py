# tests/backend/memory/test_memory_manager.py
"""Unit tests for MemoryManager and integration.

Tests cover:
- MemoryManager unified interface
- Cross-store operations
- Access control integration
- Module exports
"""


import pytest

from backend.memory import (
    AccessControlConfig,
    AccessDecision,
    AccessLevel,
    AccessRequest,
    AgentMemoryEntry,
    ConversationContext,
    EntityMemoryConfig,
    EntityReference,
    EntityStore,
    MemoryAccessControl,
    MemoryConfig,
    MemoryDocument,
    MemoryManager,
    MemoryScope,
    RolePermissions,
    SearchResult,
    SessionMemoryConfig,
    SessionStore,
    VectorMemory,
    VectorMemoryConfig,
    get_memory_manager,
    reset_memory_manager,
)


class TestMemoryModuleExports:
    """Tests for module exports."""

    def test_main_classes_exported(self):
        """Should export all main classes."""
        assert MemoryManager is not None
        assert SessionStore is not None
        assert VectorMemory is not None
        assert EntityStore is not None
        assert MemoryAccessControl is not None

    def test_config_classes_exported(self):
        """Should export all config classes."""
        assert MemoryConfig is not None
        assert SessionMemoryConfig is not None
        assert VectorMemoryConfig is not None
        assert EntityMemoryConfig is not None
        assert AccessControlConfig is not None

    def test_access_control_classes_exported(self):
        """Should export access control classes."""
        assert AccessRequest is not None
        assert AccessDecision is not None
        assert AccessLevel is not None
        assert MemoryScope is not None
        assert RolePermissions is not None

    def test_data_classes_exported(self):
        """Should export data classes."""
        assert MemoryDocument is not None
        assert SearchResult is not None
        assert AgentMemoryEntry is not None
        assert ConversationContext is not None
        assert EntityReference is not None


class TestMemoryManagerSingleton:
    """Tests for MemoryManager singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_memory_manager()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_memory_manager()

    def test_get_memory_manager_returns_instance(self):
        """Should return a MemoryManager instance."""
        manager = get_memory_manager()
        assert isinstance(manager, MemoryManager)

    def test_get_memory_manager_singleton(self):
        """Should return same instance on multiple calls."""
        manager1 = get_memory_manager()
        manager2 = get_memory_manager()
        assert manager1 is manager2

    def test_reset_memory_manager(self):
        """Should create new instance after reset."""
        manager1 = get_memory_manager()
        reset_memory_manager()
        manager2 = get_memory_manager()
        assert manager1 is not manager2


class TestMemoryManager:
    """Tests for MemoryManager unified interface."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a MemoryManager with temp storage."""
        reset_memory_manager()

        config = MemoryConfig(
            session=SessionMemoryConfig(backend="memory", ttl_seconds=3600),
            vector=VectorMemoryConfig(persist_directory=tmp_path / "chroma"),
            entity=EntityMemoryConfig(database_url=f"sqlite:///{tmp_path / 'entities.db'}"),
            access_control=AccessControlConfig(
                role_isolation_enabled=True,
                shared_memory_enabled=True,
                audit_logging_enabled=False,
            ),
        )
        return MemoryManager(config)

    # === Short-term Memory Tests ===

    def test_store_and_get_short_term(self, manager):
        """Should store and retrieve short-term memory."""
        success = manager.store_short_term(
            session_id="session-123",
            key="test_key",
            value={"data": "value"},
            agent_role="PreprocessingAgent",
        )

        assert success is True

        result = manager.get_short_term(
            session_id="session-123",
            key="test_key",
            agent_role="PreprocessingAgent",
        )

        assert result == {"data": "value"}

    def test_get_all_short_term(self, manager):
        """Should retrieve all short-term memory for a session."""
        manager.store_short_term("session-123", "key1", "value1", "AgentA")
        manager.store_short_term("session-123", "key2", "value2", "AgentB")

        result = manager.get_all_short_term("session-123", "AgentA")
        assert "key1" in result

    def test_clear_short_term(self, manager):
        """Should clear short-term memory."""
        manager.store_short_term("session-123", "key1", "value1", "AgentA")
        manager.store_short_term("session-123", "key2", "value2", "AgentA")

        count = manager.clear_short_term("session-123", "AgentA")
        assert count == 2

    # === Long-term Memory Tests ===

    def test_store_long_term(self, manager):
        """Should store long-term memory."""
        doc_id = manager.store_long_term(
            agent_role="ClinicalExtractorAgent",
            session_id="session-123",
            content="Patient is taking aspirin 100mg daily",
            memory_type="fact",
            importance=0.8,
        )

        assert doc_id is not None
        assert "ClinicalExtractorAgent" in doc_id

    def test_store_to_shared(self, manager):
        """Should store to shared memory."""
        doc_id = manager.store_to_shared(
            agent_role="PreprocessingAgent",
            session_id="session-123",
            content="Document preprocessing complete",
            memory_type="context",
        )

        assert doc_id is not None
        assert "shared" in doc_id

    def test_search_long_term(self, manager):
        """Should search long-term memory."""
        manager.store_long_term(
            agent_role="ClinicalExtractorAgent",
            session_id="session-123",
            content="Patient is taking aspirin for heart health",
            memory_type="fact",
        )

        results = manager.search(
            query="aspirin medication",
            agent_role="ClinicalExtractorAgent",
            top_k=5,
        )

        assert len(results) >= 1
        assert "aspirin" in results[0].content.lower()

    # === Entity Memory Tests ===

    def test_store_entity(self, manager):
        """Should store entity references."""
        entity_id = manager.store_entity(
            agent_role="ClinicalExtractorAgent",
            session_id="session-123",
            entity_type="medication",
            entity_value="aspirin 100mg",
            source_content="Patient takes aspirin 100mg daily",
            normalized_value="Aspirin",
            confidence=0.95,
        )

        assert entity_id is not None

    def test_search_entities(self, manager):
        """Should search entities."""
        manager.store_entity(
            agent_role="ClinicalExtractorAgent",
            session_id="session-123",
            entity_type="medication",
            entity_value="aspirin 100mg",
            source_content="Test",
        )

        results = manager.search_entities(
            entity_type="medication",
            search_value="aspirin",
            agent_role="ClinicalExtractorAgent",
        )

        assert len(results) >= 1

    # === Context Management Tests ===

    def test_create_context(self, manager):
        """Should create conversation context."""
        context = manager.create_context(
            session_id="session-123",
            agent_role="PreprocessingAgent",
            patient_context_id="patient-456",
            user_id="user-789",
        )

        assert context is not None
        assert context.session_id == "session-123"
        assert context.patient_context_id == "patient-456"

    def test_update_context(self, manager):
        """Should update conversation context."""
        manager.create_context(
            session_id="session-123",
            agent_role="PreprocessingAgent",
        )

        updated = manager.update_context(
            session_id="session-123",
            agent_role="SummarizationAgent",
            summary="Analysis complete",
            status="completed",
        )

        assert updated is not None
        assert updated.summary == "Analysis complete"
        assert "SummarizationAgent" in updated.participating_agents

    # === Access Control Integration ===

    def test_access_denied_for_other_agent(self, manager):
        """Should deny access to other agent's memory."""
        # Store as one agent
        manager.store_long_term(
            agent_role="ClinicalExtractorAgent",
            session_id="session-123",
            content="Private data",
        )

        # Try to search as different agent (should still work for own memory)
        results = manager.search(
            query="private",
            agent_role="SummarizationAgent",  # Different agent
            include_shared=False,
        )

        # Should not find the other agent's memory
        assert len(results) == 0

    # === Maintenance Tests ===

    def test_cleanup(self, manager):
        """Should run cleanup tasks."""
        stats = manager.cleanup()

        assert "session_expired" in stats
        assert "entity_expired" in stats
        assert "vector_pruned" in stats

    def test_get_stats(self, manager):
        """Should return statistics."""
        stats = manager.get_stats()

        assert stats.session_count >= 0
        assert stats.vector_collection_count >= 0
        assert "total_memory_entries" in stats.entity_stats

    # === Store Access Tests ===

    def test_session_store_property(self, manager):
        """Should provide access to session store."""
        assert isinstance(manager.session_store, SessionStore)

    def test_vector_memory_property(self, manager):
        """Should provide access to vector memory."""
        assert isinstance(manager.vector_memory, VectorMemory)

    def test_entity_store_property(self, manager):
        """Should provide access to entity store."""
        assert isinstance(manager.entity_store, EntityStore)

    def test_access_control_property(self, manager):
        """Should provide access to access control."""
        assert isinstance(manager.access_control, MemoryAccessControl)
