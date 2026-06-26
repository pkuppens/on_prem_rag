# src/backend/memory/access_control.py
"""Backward-compatibility shim for memory access control.

All symbols are now defined in:
- backend.memory.application.access_control (MemoryAccessControl, etc.)
- backend.memory.domain.value_objects (AccessLevel)

This shim re-exports from the canonical locations so existing imports continue to work.
"""

from __future__ import annotations

from backend.memory.application.access_control import (  # noqa: F401
    AccessDecision,
    AccessRequest,
    MemoryAccessControl,
    MemoryScope,
    RolePermissions,
    create_access_control,
)
from backend.memory.domain.value_objects import AccessLevel  # noqa: F401
