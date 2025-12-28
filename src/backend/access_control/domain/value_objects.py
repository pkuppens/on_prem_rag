"""Access Control Value Objects.

Defines the role-permission model for the theoretical proof-of-concept.

Design Principles:
- Separation of concerns: No role can both access data AND hide from audit
- Mutual accountability: GP actions visible to Auditor, Admin cannot see data
- Patient isolation: Patients can only access their own records
- Append-only audit: No role can delete audit logs

Reference: WBSO-AICM-2025-01 Knelpunt 1 (Bevoegd datatoegang)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import FrozenSet


class Role(Enum):
    """System roles with distinct, non-overlapping responsibilities.

    Each role has a specific purpose in the healthcare data access model:
    - GP: Healthcare provider with broad data access for patient care
    - PATIENT: Self-service access to own medical records only
    - ADMIN: System administration without access to patient data
    - AUDITOR: Compliance monitoring without access to PII content
    """

    GP = "gp"
    PATIENT = "patient"
    ADMIN = "admin"
    AUDITOR = "auditor"

    @property
    def display_name(self) -> str:
        """Human-readable name for the role."""
        names = {
            Role.GP: "General Practitioner",
            Role.PATIENT: "Patient",
            Role.ADMIN: "System Administrator",
            Role.AUDITOR: "Compliance Auditor",
        }
        return names[self]

    @property
    def can_access_patient_data(self) -> bool:
        """Returns True if this role can access patient medical data."""
        return self in (Role.GP, Role.PATIENT)

    @property
    def can_modify_system(self) -> bool:
        """Returns True if this role can modify system configuration."""
        return self == Role.ADMIN

    @property
    def can_view_audit_logs(self) -> bool:
        """Returns True if this role can view audit logs."""
        return self == Role.AUDITOR


class Permission(Enum):
    """Atomic permissions that can be assigned to roles.

    Permissions are grouped by domain:
    - Data access: READ_OWN_RECORDS, READ_ALL_RECORDS, WRITE_RECORDS
    - LLM operations: QUERY_LOCAL_LLM, QUERY_CLOUD_LLM
    - Administration: MANAGE_USERS, CONFIGURE_SYSTEM, MANAGE_GUARDRAILS
    - Audit: VIEW_AUDIT_LOGS, EXPORT_AUDIT_REPORTS
    """

    # Data access permissions
    READ_OWN_RECORDS = auto()
    READ_ALL_RECORDS = auto()
    WRITE_RECORDS = auto()

    # LLM query permissions
    QUERY_LOCAL_LLM = auto()
    QUERY_CLOUD_LLM = auto()

    # Administration permissions
    MANAGE_USERS = auto()
    CONFIGURE_SYSTEM = auto()
    MANAGE_GUARDRAILS = auto()

    # Audit permissions (cannot be combined with data access)
    VIEW_AUDIT_LOGS = auto()
    EXPORT_AUDIT_REPORTS = auto()

    @property
    def is_data_access(self) -> bool:
        """Returns True if this is a data access permission."""
        return self in (
            Permission.READ_OWN_RECORDS,
            Permission.READ_ALL_RECORDS,
            Permission.WRITE_RECORDS,
        )

    @property
    def is_audit_permission(self) -> bool:
        """Returns True if this is an audit-related permission."""
        return self in (
            Permission.VIEW_AUDIT_LOGS,
            Permission.EXPORT_AUDIT_REPORTS,
        )


@dataclass(frozen=True)
class RolePermissions:
    """Immutable permission set for a role.

    This is the "constitution" of the access control system - it defines
    what each role can do and enforces separation of concerns.
    """

    role: Role
    permissions: FrozenSet[Permission]

    def has_permission(self, permission: Permission) -> bool:
        """Check if this role has a specific permission."""
        return permission in self.permissions

    def can_read_patient_data(self) -> bool:
        """Check if this role can read any patient data."""
        return Permission.READ_OWN_RECORDS in self.permissions or Permission.READ_ALL_RECORDS in self.permissions

    def can_read_all_patients(self) -> bool:
        """Check if this role can read all patients' data (not just own)."""
        return Permission.READ_ALL_RECORDS in self.permissions

    def can_query_cloud(self) -> bool:
        """Check if this role can send queries to cloud LLM."""
        return Permission.QUERY_CLOUD_LLM in self.permissions

    def __str__(self) -> str:
        perms = ", ".join(p.name for p in sorted(self.permissions, key=lambda x: x.value))
        return f"{self.role.display_name}: [{perms}]"


# Role definitions - the "constitution" of the system
# These define the exact permissions for each role
ROLE_DEFINITIONS: dict[Role, RolePermissions] = {
    Role.GP: RolePermissions(
        role=Role.GP,
        permissions=frozenset(
            {
                Permission.READ_OWN_RECORDS,
                Permission.READ_ALL_RECORDS,
                Permission.WRITE_RECORDS,
                Permission.QUERY_LOCAL_LLM,
                Permission.QUERY_CLOUD_LLM,
            }
        ),
    ),
    Role.PATIENT: RolePermissions(
        role=Role.PATIENT,
        permissions=frozenset(
            {
                Permission.READ_OWN_RECORDS,
                Permission.QUERY_LOCAL_LLM,
                Permission.QUERY_CLOUD_LLM,  # Only for own data, anonymized
            }
        ),
    ),
    Role.ADMIN: RolePermissions(
        role=Role.ADMIN,
        permissions=frozenset(
            {
                Permission.MANAGE_USERS,
                Permission.CONFIGURE_SYSTEM,
                Permission.MANAGE_GUARDRAILS,
                # NOTE: Explicitly NO data access permissions
            }
        ),
    ),
    Role.AUDITOR: RolePermissions(
        role=Role.AUDITOR,
        permissions=frozenset(
            {
                Permission.VIEW_AUDIT_LOGS,
                Permission.EXPORT_AUDIT_REPORTS,
                # NOTE: Explicitly NO data access, NO system modification
            }
        ),
    ),
}


def get_role_permissions(role: Role) -> RolePermissions:
    """Get the permission set for a role."""
    return ROLE_DEFINITIONS[role]


@dataclass(frozen=True)
class DataScope:
    """Defines the boundary of accessible data for a query.

    This value object is attached to every query to enforce data isolation.
    For Patient role, the patient_filter restricts all queries to only
    return data for that specific patient.
    """

    user_id: str
    role: Role
    patient_filter: str | None = None  # If Patient role: restricted to this ID

    def __post_init__(self) -> None:
        """Validate that Patient role has a patient filter."""
        if self.role == Role.PATIENT and self.patient_filter is None:
            # For Patient role, default patient_filter to user_id
            object.__setattr__(self, "patient_filter", self.user_id)

    @property
    def is_self_only(self) -> bool:
        """Returns True if user can only access their own data."""
        return self.role == Role.PATIENT

    @property
    def has_full_access(self) -> bool:
        """Returns True if user can access all patient data."""
        return self.role == Role.GP

    @property
    def has_no_data_access(self) -> bool:
        """Returns True if user cannot access patient data at all."""
        return self.role in (Role.ADMIN, Role.AUDITOR)

    def can_access_patient(self, patient_id: str) -> bool:
        """Check if this scope allows access to a specific patient's data.

        Args:
            patient_id: The patient whose data is being accessed

        Returns:
            True if access is allowed, False otherwise
        """
        if self.role == Role.GP:
            return True  # GP can access all patients
        if self.role == Role.PATIENT:
            return patient_id == self.patient_filter  # Only own records
        return False  # Admin/Auditor have no patient data access

    def apply_to_query(self, query_params: dict) -> dict:
        """Apply this scope's restrictions to query parameters.

        For Patient role, adds a filter to restrict results to own data.
        For Admin/Auditor, raises an error (they shouldn't query patient data).

        Args:
            query_params: The original query parameters

        Returns:
            Modified query parameters with scope restrictions applied

        Raises:
            PermissionError: If the role cannot access patient data
        """
        if self.has_no_data_access:
            raise PermissionError(f"Role {self.role.value} cannot access patient data")

        if self.is_self_only:
            # Add patient filter for self-only access
            return {**query_params, "patient_id": self.patient_filter}

        # Full access - no additional filters
        return query_params


@dataclass(frozen=True)
class AccessDecision:
    """Result of an access control evaluation.

    Captures whether access was granted or denied, along with the reason
    and any relevant metadata for audit logging.
    """

    granted: bool
    reason: str
    scope: DataScope | None = None
    permission_checked: Permission | None = None
    guardrail_triggered: str | None = None

    @classmethod
    def allow(cls, scope: DataScope, permission: Permission) -> AccessDecision:
        """Create an ALLOW decision."""
        return cls(
            granted=True,
            reason="Access granted",
            scope=scope,
            permission_checked=permission,
        )

    @classmethod
    def deny(cls, reason: str, permission: Permission | None = None) -> AccessDecision:
        """Create a DENY decision."""
        return cls(
            granted=False,
            reason=reason,
            permission_checked=permission,
        )

    @classmethod
    def deny_guardrail(cls, guardrail: str, reason: str) -> AccessDecision:
        """Create a DENY decision due to guardrail trigger."""
        return cls(
            granted=False,
            reason=reason,
            guardrail_triggered=guardrail,
        )


# Permission matrix for documentation/verification
PERMISSION_MATRIX = """
┌─────────────────────────────────────────────────────────────────────────┐
│                     ROLE PERMISSION MATRIX                              │
├─────────────┬──────────┬─────────┬─────────┬─────────────────────────────┤
│ Permission  │ GP       │ Patient │ Admin   │ Auditor                    │
├─────────────┼──────────┼─────────┼─────────┼─────────────────────────────┤
│ READ own    │ ✓        │ ✓       │ ✗       │ ✗ (sees hashes only)       │
│ READ others │ ✓ (all)  │ ✗       │ ✗       │ ✗                          │
│ WRITE data  │ ✓        │ ✗       │ ✗       │ ✗                          │
│ QUERY local │ ✓        │ ✓       │ ✗       │ ✗                          │
│ QUERY cloud │ ✓        │ ✓       │ ✗       │ ✗                          │
│ Config sys  │ ✗        │ ✗       │ ✓       │ ✗                          │
│ View audit  │ ✗        │ ✗       │ ✗       │ ✓ (no PII content)         │
│ Delete audit│ ✗        │ ✗       │ ✗       │ ✗ (append-only)            │
│ Manage users│ ✗        │ ✗       │ ✓       │ ✗                          │
├─────────────┴──────────┴─────────┴─────────┴─────────────────────────────┤
│ CONSTRAINTS (mutual accountability)                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ • GP cannot disable/bypass audit logging                                 │
│ • Admin cannot view patient data or audit content                       │
│ • Auditor sees action metadata but NOT PII content                      │
│ • Patient isolation: user_id filter on ALL queries                      │
│ • Audit log is append-only (no role can delete)                         │
└──────────────────────────────────────────────────────────────────────────┘
"""
