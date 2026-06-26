# src/backend/memory/entity_store.py
"""Backward-compatibility shim for entity store.

All symbols are now defined in backend.memory.infrastructure.entity_store.
This shim re-exports from the canonical location so existing imports continue to work.
"""

from __future__ import annotations

from backend.memory.infrastructure.entity_store import EntityStore  # noqa: F401
