"""IAccessControlCheck port — interface for Access Control BC.

The Query Service uses this port to verify that a user has permission
to perform queries and access specific data scopes before processing
a question.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IAccessControlCheck(ABC):
    """Port for checking access permissions.

    Implementations connect to the Access Control BC to verify
    user permissions and data scopes.
    """

    @abstractmethod
    def check_permission(self, user_id: str, permission_name: str) -> bool:
        """Check if a user has a specific permission.

        Args:
            user_id: The user to check.
            permission_name: The permission to verify.

        Returns:
            True if the user has the permission.
        """
        ...

    @abstractmethod
    def apply_scope(self, user_id: str, role: str, query_params: dict[str, Any]) -> dict[str, Any]:
        """Apply data scope restrictions to query parameters.

        Args:
            user_id: The user identifier.
            role: The user's role.
            query_params: Original query parameters.

        Returns:
            Modified query parameters with scope restrictions.

        Raises:
            PermissionError: If the role cannot access patient data.
        """
        ...
