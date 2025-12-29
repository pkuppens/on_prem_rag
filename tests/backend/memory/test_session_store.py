# tests/backend/memory/test_session_store.py
"""Unit tests for session store (short-term memory).

Tests cover:
- In-memory store CRUD operations
- Session TTL expiration
- Agent role filtering
- Entry limits and cleanup
"""

import time

import pytest

from backend.memory.config import SessionMemoryConfig
from backend.memory.session_store import InMemorySessionStore, SessionEntry, SessionStore


class TestSessionEntry:
    """Tests for SessionEntry dataclass."""

    def test_session_entry_creation(self):
        """Session entries should be created with correct defaults."""
        entry = SessionEntry(key="test", value="data")
        assert entry.key == "test"
        assert entry.value == "data"
        assert entry.created_at > 0
        assert entry.expires_at is None
        assert entry.agent_role is None

    def test_session_entry_not_expired_without_ttl(self):
        """Entries without expires_at should never expire."""
        entry = SessionEntry(key="test", value="data")
        assert not entry.is_expired()

    def test_session_entry_expired(self):
        """Entries with past expires_at should be expired."""
        entry = SessionEntry(key="test", value="data", expires_at=time.time() - 1)
        assert entry.is_expired()

    def test_session_entry_not_expired_future(self):
        """Entries with future expires_at should not be expired."""
        entry = SessionEntry(key="test", value="data", expires_at=time.time() + 3600)
        assert not entry.is_expired()


class TestInMemorySessionStore:
    """Tests for InMemorySessionStore."""

    @pytest.fixture
    def store(self):
        """Create a fresh in-memory store for each test."""
        config = SessionMemoryConfig(ttl_seconds=3600, max_entries_per_session=100)
        return InMemorySessionStore(config)

    def test_set_and_get(self, store):
        """Should store and retrieve values correctly."""
        store.set("session-1", "key1", "value1")
        assert store.get("session-1", "key1") == "value1"

    def test_get_nonexistent_key(self, store):
        """Should return None for nonexistent keys."""
        assert store.get("session-1", "nonexistent") is None

    def test_get_nonexistent_session(self, store):
        """Should return None for nonexistent sessions."""
        assert store.get("nonexistent-session", "key") is None

    def test_delete_key(self, store):
        """Should delete keys correctly."""
        store.set("session-1", "key1", "value1")
        assert store.delete("session-1", "key1") is True
        assert store.get("session-1", "key1") is None

    def test_delete_nonexistent(self, store):
        """Should return False when deleting nonexistent key."""
        assert store.delete("session-1", "nonexistent") is False

    def test_get_all(self, store):
        """Should retrieve all values for a session."""
        store.set("session-1", "key1", "value1")
        store.set("session-1", "key2", "value2")
        store.set("session-2", "key3", "value3")

        result = store.get_all("session-1")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_get_all_with_agent_filter(self, store):
        """Should filter by agent role when specified."""
        store.set("session-1", "key1", "value1", agent_role="AgentA")
        store.set("session-1", "key2", "value2", agent_role="AgentB")

        result = store.get_all("session-1", agent_role="AgentA")
        assert result == {"key1": "value1"}

    def test_clear_session(self, store):
        """Should clear all entries for a session."""
        store.set("session-1", "key1", "value1")
        store.set("session-1", "key2", "value2")

        count = store.clear_session("session-1")
        assert count == 2
        assert store.get_all("session-1") == {}

    def test_ttl_expiration(self, store):
        """Entries should expire after TTL."""
        # Set with very short TTL
        store.set("session-1", "key1", "value1", ttl_seconds=1)

        # Should exist immediately
        assert store.get("session-1", "key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be gone after TTL
        assert store.get("session-1", "key1") is None

    def test_cleanup_expired(self, store):
        """Cleanup should remove expired entries."""
        # Set entries with short TTL
        store.set("session-1", "key1", "value1", ttl_seconds=1)
        store.set("session-1", "key2", "value2", ttl_seconds=3600)

        time.sleep(1.1)

        removed = store.cleanup_expired()
        assert removed == 1
        assert store.get("session-1", "key1") is None
        assert store.get("session-1", "key2") == "value2"

    def test_max_entries_limit(self):
        """Should enforce max entries per session."""
        config = SessionMemoryConfig(max_entries_per_session=3)
        store = InMemorySessionStore(config)

        store.set("session-1", "key1", "value1")
        store.set("session-1", "key2", "value2")
        store.set("session-1", "key3", "value3")
        store.set("session-1", "key4", "value4")  # Should trigger removal of oldest

        assert store.get_entry_count("session-1") == 3
        # key1 should have been removed (oldest)
        assert store.get("session-1", "key1") is None
        assert store.get("session-1", "key4") == "value4"

    def test_get_session_count(self, store):
        """Should count active sessions."""
        store.set("session-1", "key1", "value1")
        store.set("session-2", "key1", "value1")
        store.set("session-3", "key1", "value1")

        assert store.get_session_count() == 3

    def test_get_entry_count(self, store):
        """Should count entries in a session."""
        store.set("session-1", "key1", "value1")
        store.set("session-1", "key2", "value2")

        assert store.get_entry_count("session-1") == 2
        assert store.get_entry_count("nonexistent") == 0


class TestSessionStore:
    """Tests for the high-level SessionStore interface."""

    @pytest.fixture
    def store(self):
        """Create a session store with in-memory backend."""
        config = SessionMemoryConfig(backend="memory", ttl_seconds=3600)
        return SessionStore(config)

    def test_backend_type(self, store):
        """Should report correct backend type."""
        assert store.backend_type == "memory"

    def test_basic_operations(self, store):
        """Should support basic CRUD operations."""
        store.set("session-1", "test", {"data": "value"})
        assert store.get("session-1", "test") == {"data": "value"}

        store.delete("session-1", "test")
        assert store.get("session-1", "test") is None

    def test_complex_values(self, store):
        """Should handle complex value types."""
        store.set("session-1", "list", [1, 2, 3])
        store.set("session-1", "dict", {"nested": {"key": "value"}})
        store.set("session-1", "number", 42)
        store.set("session-1", "string", "hello")

        assert store.get("session-1", "list") == [1, 2, 3]
        assert store.get("session-1", "dict") == {"nested": {"key": "value"}}
        assert store.get("session-1", "number") == 42
        assert store.get("session-1", "string") == "hello"
