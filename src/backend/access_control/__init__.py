"""Access Control Bounded Context.

Implements WBSO Knelpunt 1: Bevoegd datatoegang (Authorized Data Access).

This context handles role-based and context-aware access control for natural
language queries, including:
- Role and permission management
- Query scope resolution
- Jailbreak detection
- Access decision logging

Reference: WBSO-AICM-2025-01 WP1 (06-2025)
"""

from backend.access_control.domain.value_objects import (
    DataScope,
    Permission,
    Role,
    RolePermissions,
    ROLE_DEFINITIONS,
)

__all__ = [
    "DataScope",
    "Permission",
    "Role",
    "RolePermissions",
    "ROLE_DEFINITIONS",
]
