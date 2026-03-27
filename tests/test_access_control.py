"""Unit tests for the Access Control domain model.

Validates that the RBAC permission matrix matches the documented design:
- Role GP: full data access, no admin/audit
- Role PATIENT: self-only data access
- Role ADMIN: system config only, no patient data
- Role AUDITOR: audit logs only, no data access

NOTE: These tests cover domain logic only. Route-level enforcement (wiring
require_permission to FastAPI endpoints) is tracked as a follow-up task —
the domain model is sound but not yet wired to HTTP endpoints.
"""

import pytest

from backend.access_control.domain.value_objects import (
    ROLE_DEFINITIONS,
    DataScope,
    Permission,
    Role,
)


class TestRolePermissionMatrix:
    """As a compliance officer, I want the permission matrix enforced in code so access decisions are auditable."""

    def test_gp_has_full_data_access(self) -> None:
        """GP role must be able to read all records and write records."""
        gp = ROLE_DEFINITIONS[Role.GP]
        assert gp.has_permission(Permission.READ_OWN_RECORDS)
        assert gp.has_permission(Permission.READ_ALL_RECORDS)
        assert gp.has_permission(Permission.WRITE_RECORDS)

    def test_gp_cannot_access_audit_logs(self) -> None:
        """GP must not be able to view audit logs — separation of concerns."""
        gp = ROLE_DEFINITIONS[Role.GP]
        assert not gp.has_permission(Permission.VIEW_AUDIT_LOGS)
        assert not gp.has_permission(Permission.EXPORT_AUDIT_REPORTS)

    def test_patient_has_self_only_access(self) -> None:
        """Patient role must only have own-record access, not all-records access."""
        patient = ROLE_DEFINITIONS[Role.PATIENT]
        assert patient.has_permission(Permission.READ_OWN_RECORDS)
        assert not patient.has_permission(Permission.READ_ALL_RECORDS)
        assert not patient.has_permission(Permission.WRITE_RECORDS)

    def test_admin_has_no_patient_data_access(self) -> None:
        """Admin must have zero patient data permissions — mutual accountability."""
        admin = ROLE_DEFINITIONS[Role.ADMIN]
        assert not admin.has_permission(Permission.READ_OWN_RECORDS)
        assert not admin.has_permission(Permission.READ_ALL_RECORDS)
        assert not admin.has_permission(Permission.WRITE_RECORDS)
        assert not admin.has_permission(Permission.VIEW_AUDIT_LOGS)

    def test_auditor_has_no_data_access(self) -> None:
        """Auditor must not be able to access patient data — sees metadata only."""
        auditor = ROLE_DEFINITIONS[Role.AUDITOR]
        assert not auditor.has_permission(Permission.READ_OWN_RECORDS)
        assert not auditor.has_permission(Permission.READ_ALL_RECORDS)
        assert not auditor.has_permission(Permission.WRITE_RECORDS)
        assert auditor.has_permission(Permission.VIEW_AUDIT_LOGS)

    def test_no_role_can_delete_audit_logs(self) -> None:
        """No role must have the ability to delete audit logs — append-only guarantee."""
        # The Permission enum has no DELETE_AUDIT_LOGS value: verify it doesn't exist
        permission_names = {p.name for p in Permission}
        assert "DELETE_AUDIT_LOGS" not in permission_names, (
            "DELETE_AUDIT_LOGS permission must not exist — audit trail is append-only"
        )


class TestDataScopeIsolation:
    """As a security control, I want DataScope to enforce per-user query filtering."""

    def test_patient_scope_defaults_filter_to_own_user_id(self) -> None:
        """Patient DataScope must default patient_filter to user_id when not specified."""
        scope = DataScope(user_id="patient-123", role=Role.PATIENT)
        assert scope.patient_filter == "patient-123"

    def test_patient_can_only_access_own_records(self) -> None:
        """Patient scope must allow own patient_id and deny all others."""
        scope = DataScope(user_id="patient-123", role=Role.PATIENT)
        assert scope.can_access_patient("patient-123")
        assert not scope.can_access_patient("patient-456")

    def test_gp_can_access_all_patients(self) -> None:
        """GP scope must allow access to any patient_id."""
        scope = DataScope(user_id="gp-001", role=Role.GP)
        assert scope.can_access_patient("patient-123")
        assert scope.can_access_patient("patient-456")

    def test_admin_cannot_access_any_patient(self) -> None:
        """Admin scope must deny access to all patient data."""
        scope = DataScope(user_id="admin-001", role=Role.ADMIN)
        assert not scope.can_access_patient("patient-123")

    def test_patient_scope_apply_to_query_adds_filter(self) -> None:
        """apply_to_query for Patient role must inject patient_id filter."""
        scope = DataScope(user_id="patient-123", role=Role.PATIENT)
        result = scope.apply_to_query({"query": "blood pressure"})
        assert result["patient_id"] == "patient-123"
        assert result["query"] == "blood pressure"

    def test_admin_scope_apply_to_query_raises_permission_error(self) -> None:
        """apply_to_query for Admin role must raise PermissionError."""
        scope = DataScope(user_id="admin-001", role=Role.ADMIN)
        with pytest.raises(PermissionError):
            scope.apply_to_query({"query": "blood pressure"})
