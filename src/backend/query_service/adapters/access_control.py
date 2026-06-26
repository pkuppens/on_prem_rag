"""Anti-Corruption Layer adapter to the Access Control BC.

Translates Query Service permission check requests into Access Control
BC domain types (DataScope, Permission) and converts responses back.
"""

from __future__ import annotations

from typing import Any

from backend.access_control.domain.value_objects import (
    AccessDecision,
    DataScope,
    Permission,
    Role,
    get_role_permissions,
)
from backend.query_service.ports.access_control import IAccessControlCheck


class AccessControlAdapter(IAccessControlCheck):
    """Adapter that delegates to the Access Control BC.

    Translates between the Query Service's port interface and the
    Access Control domain model.
    """

    def check_permission(self, user_id: str, permission_name: str) -> bool:
        """Check if a user role has a specific permission.

        Args:
            user_id: The user identifier (role encoded in prefix).
            permission_name: The permission to check (e.g. "QUERY_LOCAL_LLM").

        Returns:
            True if the permission is granted.
        """
        try:
            permission = Permission[permission_name]
        except KeyError:
            return False

        # In the current system, user_id format determines role
        # This is a simplification; a real system would look up the user
        role = self._infer_role(user_id)
        role_perms = get_role_permissions(role)
        return role_perms.has_permission(permission)

    def apply_scope(self, user_id: str, role: str, query_params: dict[str, Any]) -> dict[str, Any]:
        """Apply data scope restrictions to query parameters.

        Args:
            user_id: The user identifier.
            role: The user's role string.
            query_params: Original query parameters.

        Returns:
            Query parameters with data scope restrictions applied.

        Raises:
            PermissionError: If the role cannot access patient data.
        """
        try:
            role_enum = Role(role.lower())
        except ValueError:
            role_enum = Role.GP  # Default to GP for unknown roles

        # Determine patient filter from user_id if patient role
        patient_filter: str | None = None
        if role_enum == Role.PATIENT:
            patient_filter = user_id

        scope = DataScope(
            user_id=user_id,
            role=role_enum,
            patient_filter=patient_filter,
        )

        return scope.apply_to_query(query_params)

    def _infer_role(self, user_id: str) -> Role:
        """Infer role from user_id prefix for backward compatibility.

        In production this would call the auth service. For now,
        we use prefixes: "patient_*", "admin_*", "auditor_*".
        """
        if user_id.startswith("patient_"):
            return Role.PATIENT
        if user_id.startswith("admin_"):
            return Role.ADMIN
        if user_id.startswith("auditor_"):
            return Role.AUDITOR
        return Role.GP  # Default
