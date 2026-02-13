# src/backend/memory/session_store.py
"""Short-term session memory store.

Provides in-memory (default) and Redis-backed session storage for
conversation context that persists within a session but not across restarts.

Features:
- Session-scoped key-value storage
- TTL-based expiration
- Per-agent isolation within sessions
- Cleanup of expired entries

For distributed deployments, use Redis backend.
For single-instance deployments, in-memory backend is faster.
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.memory.config import SessionMemoryConfig, get_memory_config

logger = logging.getLogger(__name__)


@dataclass
class SessionEntry:
    """A single entry in session memory."""

    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    agent_role: str | None = None

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class SessionStoreBackend(ABC):
    """Abstract base class for session store backends."""

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


class InMemorySessionStore(SessionStoreBackend):
    """In-memory session store using Python dictionaries.

    Thread-safe implementation suitable for single-instance deployments.
    Data is lost on process restart.
    """

    def __init__(self, config: SessionMemoryConfig | None = None):
        self.config = config or get_memory_config().session
        self._store: dict[str, dict[str, SessionEntry]] = {}
        self._lock = threading.RLock()

    def get(self, session_id: str, key: str) -> Any | None:
        with self._lock:
            session_data = self._store.get(session_id, {})
            entry = session_data.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del session_data[key]
                return None
            return entry.value

    def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        agent_role: str | None = None,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds
        expires_at = time.time() + ttl if ttl > 0 else None

        entry = SessionEntry(
            key=key,
            value=value,
            expires_at=expires_at,
            agent_role=agent_role,
        )

        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = {}

            # Check max entries limit
            session_data = self._store[session_id]
            if len(session_data) >= self.config.max_entries_per_session:
                # Remove oldest entry
                oldest_key = min(session_data.keys(), key=lambda k: session_data[k].created_at)
                del session_data[oldest_key]
                logger.debug(f"Session {session_id}: removed oldest entry {oldest_key} due to limit")

            session_data[key] = entry

    def delete(self, session_id: str, key: str) -> bool:
        with self._lock:
            session_data = self._store.get(session_id, {})
            if key in session_data:
                del session_data[key]
                return True
            return False

    def get_all(self, session_id: str, agent_role: str | None = None) -> dict[str, Any]:
        with self._lock:
            session_data = self._store.get(session_id, {})
            result = {}
            expired_keys = []

            for key, entry in session_data.items():
                if entry.is_expired():
                    expired_keys.append(key)
                    continue
                if agent_role is not None and entry.agent_role != agent_role:
                    continue
                result[key] = entry.value

            # Cleanup expired entries
            for key in expired_keys:
                del session_data[key]

            return result

    def clear_session(self, session_id: str) -> int:
        with self._lock:
            session_data = self._store.pop(session_id, {})
            return len(session_data)

    def cleanup_expired(self) -> int:
        removed_count = 0
        with self._lock:
            empty_sessions = []
            for session_id, session_data in self._store.items():
                expired_keys = [key for key, entry in session_data.items() if entry.is_expired()]
                for key in expired_keys:
                    del session_data[key]
                    removed_count += 1
                if not session_data:
                    empty_sessions.append(session_id)

            # Remove empty sessions
            for session_id in empty_sessions:
                del self._store[session_id]

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired session entries")
        return removed_count

    def get_session_count(self) -> int:
        with self._lock:
            return len(self._store)

    def get_entry_count(self, session_id: str) -> int:
        with self._lock:
            return len(self._store.get(session_id, {}))


class RedisSessionStore(SessionStoreBackend):
    """Redis-backed session store for distributed deployments.

    Requires redis package: `uv add redis`
    Data persists across process restarts (subject to Redis configuration).
    """

    def __init__(self, config: SessionMemoryConfig | None = None):
        self.config = config or get_memory_config().session

        try:
            import redis

            self._redis = redis.from_url(self.config.redis_url, decode_responses=True)
            # Test connection
            self._redis.ping()
        except ImportError as e:
            raise ImportError("Redis package not installed. Install with: uv add redis") from e
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis at {self.config.redis_url}: {e}") from e

    def _make_key(self, session_id: str, key: str) -> str:
        """Create a Redis key from session_id and key."""
        return f"memory:session:{session_id}:{key}"

    def _make_session_pattern(self, session_id: str) -> str:
        """Create a pattern to match all keys in a session."""
        return f"memory:session:{session_id}:*"

    def get(self, session_id: str, key: str) -> Any | None:
        import json

        redis_key = self._make_key(session_id, key)
        data = self._redis.get(redis_key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        agent_role: str | None = None,
    ) -> None:
        import json

        ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds
        redis_key = self._make_key(session_id, key)

        # Store as JSON for complex types
        if isinstance(value, dict | list):
            value = json.dumps(value)

        if ttl > 0:
            self._redis.setex(redis_key, ttl, value)
        else:
            self._redis.set(redis_key, value)

        # Store agent role metadata if provided
        if agent_role:
            meta_key = f"{redis_key}:meta:agent_role"
            if ttl > 0:
                self._redis.setex(meta_key, ttl, agent_role)
            else:
                self._redis.set(meta_key, agent_role)

    def delete(self, session_id: str, key: str) -> bool:
        redis_key = self._make_key(session_id, key)
        meta_key = f"{redis_key}:meta:agent_role"
        deleted = self._redis.delete(redis_key, meta_key)
        return deleted > 0

    def get_all(self, session_id: str, agent_role: str | None = None) -> dict[str, Any]:
        import json

        pattern = self._make_session_pattern(session_id)
        keys = [k for k in self._redis.scan_iter(pattern) if ":meta:" not in k]

        result = {}
        for redis_key in keys:
            # Extract the original key from the Redis key
            key = redis_key.split(":")[-1]

            # Check agent role filter if specified
            if agent_role:
                meta_key = f"{redis_key}:meta:agent_role"
                stored_role = self._redis.get(meta_key)
                if stored_role != agent_role:
                    continue

            value = self._redis.get(redis_key)
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value

        return result

    def clear_session(self, session_id: str) -> int:
        pattern = self._make_session_pattern(session_id)
        keys = list(self._redis.scan_iter(pattern))
        if keys:
            return self._redis.delete(*keys)
        return 0

    def cleanup_expired(self) -> int:
        # Redis handles TTL automatically, so nothing to do here
        return 0

    def get_session_count(self) -> int:
        # Count unique session IDs
        pattern = "memory:session:*"
        session_ids = set()
        for key in self._redis.scan_iter(pattern):
            parts = key.split(":")
            if len(parts) >= 3:
                session_ids.add(parts[2])
        return len(session_ids)

    def get_entry_count(self, session_id: str) -> int:
        pattern = self._make_session_pattern(session_id)
        # Exclude metadata keys
        return sum(1 for k in self._redis.scan_iter(pattern) if ":meta:" not in k)


class SessionStore:
    """High-level session store interface.

    Provides a unified interface regardless of backend (in-memory or Redis).
    Use this class for all session memory operations.
    """

    def __init__(self, config: SessionMemoryConfig | None = None):
        self.config = config or get_memory_config().session
        self._backend = self._create_backend()

    def _create_backend(self) -> SessionStoreBackend:
        """Create the appropriate backend based on configuration."""
        if self.config.backend.lower() == "redis":
            return RedisSessionStore(self.config)
        return InMemorySessionStore(self.config)

    def get(self, session_id: str, key: str) -> Any | None:
        """Get a value from session memory."""
        return self._backend.get(session_id, key)

    def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        agent_role: str | None = None,
    ) -> None:
        """Store a value in session memory."""
        self._backend.set(session_id, key, value, ttl_seconds, agent_role)

    def delete(self, session_id: str, key: str) -> bool:
        """Delete a key from session memory."""
        return self._backend.delete(session_id, key)

    def get_all(self, session_id: str, agent_role: str | None = None) -> dict[str, Any]:
        """Get all values for a session."""
        return self._backend.get_all(session_id, agent_role)

    def clear_session(self, session_id: str) -> int:
        """Clear all entries for a session."""
        return self._backend.clear_session(session_id)

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        return self._backend.cleanup_expired()

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        return self._backend.get_session_count()

    def get_entry_count(self, session_id: str) -> int:
        """Get the number of entries in a session."""
        return self._backend.get_entry_count(session_id)

    @property
    def backend_type(self) -> str:
        """Get the backend type name."""
        return self.config.backend
