# src/backend/memory/access_control.py
"""Role-based access control for memory operations.

Implements memory isolation between agent roles and patient contexts.
Ensures agents can only access their own memory and authorized shared memory.

Features:
- Role-based memory isolation
- Patient context isolation (critical for medical data)
- Shared memory pool with role authorization
- Audit logging integration

Security Model:
- Each agent role has its own memory namespace
- Patient data is isolated by patient_context_id
- Shared memory requires explicit role authorization
- All access decisions are logged for audit
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from backend.memory.config import AccessControlConfig, get_memory_config

if TYPE_CHECKING:
    from backend.memory.entity_store import EntityStore

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Memory access levels."""

    NONE = "none"  # No access
    READ = "read"  # Read-only access
    WRITE = "write"  # Read and write access
    ADMIN = "admin"  # Full access including delete


class MemoryScope(Enum):
    """Scopes of memory that can be accessed."""

    NONE = "none"  # No scope (access denied)
    OWN = "own"  # Agent's own memory
    SHARED = "shared"  # Shared memory pool
    OTHER_AGENT = "other_agent"  # Another agent's memory (usually denied)
    ALL = "all"  # All memory (admin only)


@dataclass
class AccessRequest:
    """A request to access memory."""

    agent_role: str
    operation: str  # "read", "write", "delete", "search"
    memory_type: str  # "session", "vector", "entity"
    target_agent_role: str | None = None  # For cross-agent access
    session_id: str | None = None
    patient_context_id: str | None = None
    resource_id: str | None = None


@dataclass
class AccessDecision:
    """Result of an access control decision."""

    allowed: bool
    reason: str
    scope: MemoryScope
    access_level: AccessLevel
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class RolePermissions:
    """Permissions configuration for an agent role."""

    role_name: str
    can_access_own: AccessLevel = AccessLevel.WRITE
    can_access_shared: AccessLevel = AccessLevel.READ
    can_access_other: AccessLevel = AccessLevel.NONE
    allowed_memory_types: list[str] = field(default_factory=lambda: ["session", "vector", "entity"])
    allowed_operations: list[str] = field(default_factory=lambda: ["read", "write", "search", "delete"])
    patient_isolation_required: bool = True


class MemoryAccessControl:
    """Role-based access control for memory operations.

    Enforces memory isolation between agents and patient contexts.
    Integrates with audit logging for compliance.
    """

    # Default permissions for known agent roles
    DEFAULT_ROLE_PERMISSIONS: dict[str, RolePermissions] = {
        "PreprocessingAgent": RolePermissions(
            role_name="PreprocessingAgent",
            can_access_shared=AccessLevel.WRITE,  # Can write to shared for downstream agents
        ),
        "LanguageAssessorAgent": RolePermissions(
            role_name="LanguageAssessorAgent",
            can_access_shared=AccessLevel.READ,
        ),
        "ClinicalExtractorAgent": RolePermissions(
            role_name="ClinicalExtractorAgent",
            can_access_shared=AccessLevel.WRITE,  # Extracts entities for others
        ),
        "SummarizationAgent": RolePermissions(
            role_name="SummarizationAgent",
            can_access_shared=AccessLevel.READ,
        ),
        "QualityControlAgent": RolePermissions(
            role_name="QualityControlAgent",
            can_access_shared=AccessLevel.READ,
            can_access_other=AccessLevel.READ,  # QC can read all agent outputs
        ),
    }

    def __init__(
        self,
        config: AccessControlConfig | None = None,
        entity_store: "EntityStore | None" = None,
    ):
        self.config = config or get_memory_config().access_control
        self._entity_store = entity_store
        self._role_permissions = dict(self.DEFAULT_ROLE_PERMISSIONS)
        self._patient_contexts: dict[str, set[str]] = {}  # session_id -> patient_context_ids

    def check_access(self, request: AccessRequest) -> AccessDecision:
        """Check if an access request should be allowed.

        Args:
            request: The access request to check

        Returns:
            AccessDecision with the result and reason
        """
        # Get role permissions
        permissions = self._get_role_permissions(request.agent_role)

        # Check if operation is allowed for this role
        if request.operation not in permissions.allowed_operations:
            return self._deny(f"Operation '{request.operation}' not allowed for role '{request.agent_role}'")

        # Check if memory type is allowed
        if request.memory_type not in permissions.allowed_memory_types:
            return self._deny(f"Memory type '{request.memory_type}' not allowed for role '{request.agent_role}'")

        # Determine scope
        scope = self._determine_scope(request, permissions)

        # Check access level for the scope
        access_level = self._get_access_level(permissions, scope)

        if access_level == AccessLevel.NONE:
            return self._deny(f"No access to {scope.value} memory for role '{request.agent_role}'")

        # Check if operation matches access level
        if not self._operation_allowed(request.operation, access_level):
            return self._deny(f"Operation '{request.operation}' requires higher access level than {access_level.value}")

        # Check patient isolation
        if self.config.role_isolation_enabled and permissions.patient_isolation_required:
            isolation_check = self._check_patient_isolation(request)
            if not isolation_check.allowed:
                return isolation_check

        # Access allowed
        decision = AccessDecision(
            allowed=True,
            reason="Access granted",
            scope=scope,
            access_level=access_level,
        )

        # Log the access decision
        self._log_access_decision(request, decision)

        return decision

    def register_patient_context(self, session_id: str, patient_context_id: str) -> None:
        """Register a patient context for a session.

        This ensures that the session can only access data for this patient.

        Args:
            session_id: The session ID
            patient_context_id: The patient context identifier
        """
        if session_id not in self._patient_contexts:
            self._patient_contexts[session_id] = set()
        self._patient_contexts[session_id].add(patient_context_id)
        logger.debug(f"Registered patient context {patient_context_id} for session {session_id}")

    def get_allowed_patient_contexts(self, session_id: str) -> set[str]:
        """Get the allowed patient contexts for a session.

        Args:
            session_id: The session ID

        Returns:
            Set of allowed patient context IDs
        """
        return self._patient_contexts.get(session_id, set())

    def set_role_permissions(self, role_name: str, permissions: RolePermissions) -> None:
        """Set custom permissions for a role.

        Args:
            role_name: The role name
            permissions: The permissions to set
        """
        self._role_permissions[role_name] = permissions

    def _get_role_permissions(self, role_name: str) -> RolePermissions:
        """Get permissions for a role, using defaults if not explicitly set."""
        if role_name in self._role_permissions:
            return self._role_permissions[role_name]

        # Return default permissions for unknown roles
        return RolePermissions(
            role_name=role_name,
            can_access_own=AccessLevel.WRITE,
            can_access_shared=AccessLevel.READ if role_name in self.config.shared_memory_roles else AccessLevel.NONE,
            can_access_other=AccessLevel.NONE,
        )

    def _determine_scope(self, request: AccessRequest, permissions: RolePermissions) -> MemoryScope:
        """Determine the scope of the access request."""
        if request.target_agent_role is None:
            return MemoryScope.OWN
        if request.target_agent_role == "shared":
            return MemoryScope.SHARED
        if request.target_agent_role == request.agent_role:
            return MemoryScope.OWN
        return MemoryScope.OTHER_AGENT

    def _get_access_level(self, permissions: RolePermissions, scope: MemoryScope) -> AccessLevel:
        """Get the access level for a scope."""
        if scope == MemoryScope.OWN:
            return permissions.can_access_own
        if scope == MemoryScope.SHARED:
            if not self.config.shared_memory_enabled:
                return AccessLevel.NONE
            return permissions.can_access_shared
        if scope == MemoryScope.OTHER_AGENT:
            return permissions.can_access_other
        return AccessLevel.NONE

    def _operation_allowed(self, operation: str, access_level: AccessLevel) -> bool:
        """Check if an operation is allowed at a given access level."""
        if access_level == AccessLevel.ADMIN:
            return True
        if access_level == AccessLevel.WRITE:
            return operation in ("read", "write", "search", "delete")  # Write includes delete
        if access_level == AccessLevel.READ:
            return operation in ("read", "search")
        return False

    def _check_patient_isolation(self, request: AccessRequest) -> AccessDecision:
        """Check patient context isolation.

        Ensures that agents can only access data for patients they're authorized for.
        """
        if request.session_id is None:
            # No session context - allow (non-patient-specific request)
            return AccessDecision(
                allowed=True,
                reason="No session context",
                scope=MemoryScope.OWN,
                access_level=AccessLevel.WRITE,
            )

        if request.patient_context_id is None:
            # No patient context specified - allow general access
            return AccessDecision(
                allowed=True,
                reason="No patient context specified",
                scope=MemoryScope.OWN,
                access_level=AccessLevel.WRITE,
            )

        # Check if session is authorized for this patient
        allowed_contexts = self.get_allowed_patient_contexts(request.session_id)

        if not allowed_contexts:
            # No restrictions registered - allow (first access)
            self.register_patient_context(request.session_id, request.patient_context_id)
            return AccessDecision(
                allowed=True,
                reason="First patient context for session",
                scope=MemoryScope.OWN,
                access_level=AccessLevel.WRITE,
            )

        if request.patient_context_id not in allowed_contexts:
            return self._deny(
                f"Session {request.session_id} not authorized for patient context {request.patient_context_id}. "
                f"Allowed contexts: {allowed_contexts}"
            )

        return AccessDecision(
            allowed=True,
            reason="Patient context authorized",
            scope=MemoryScope.OWN,
            access_level=AccessLevel.WRITE,
        )

    def _deny(self, reason: str) -> AccessDecision:
        """Create a denial decision."""
        logger.warning(f"Access denied: {reason}")
        return AccessDecision(
            allowed=False,
            reason=reason,
            scope=MemoryScope.NONE,
            access_level=AccessLevel.NONE,
        )

    def _log_access_decision(self, request: AccessRequest, decision: AccessDecision) -> None:
        """Log an access decision for audit."""
        if not self.config.audit_logging_enabled:
            return

        if self._entity_store is None:
            return

        try:
            self._entity_store.log_access(
                session_id=request.session_id or "unknown",
                agent_role=request.agent_role,
                operation=request.operation,
                memory_type=request.memory_type,
                target_id=request.resource_id,
                success=decision.allowed,
                error_message=None if decision.allowed else decision.reason,
                metadata={
                    "scope": decision.scope.value,
                    "access_level": decision.access_level.value,
                    "target_agent": request.target_agent_role,
                    "patient_context": request.patient_context_id,
                },
            )
        except Exception as e:
            logger.error(f"Failed to log access decision: {e}")


def create_access_control(
    config: AccessControlConfig | None = None,
    entity_store: "EntityStore | None" = None,
) -> MemoryAccessControl:
    """Factory function to create an access control instance.

    Args:
        config: Optional access control configuration
        entity_store: Optional entity store for audit logging

    Returns:
        Configured MemoryAccessControl instance
    """
    return MemoryAccessControl(config=config, entity_store=entity_store)
