# src/backend/memory/session_store.py
"""Backward-compatibility shim for session store.

All symbols are now defined in backend.memory.infrastructure.session_store.
This shim re-exports from the canonical location so existing imports continue to work.
"""

from __future__ import annotations

from backend.memory.infrastructure.session_store import (  # noqa: F401
    InMemorySessionStore,
    RedisSessionStore,
    SessionEntry,
    SessionStore,
    SessionStoreBackend,
)
