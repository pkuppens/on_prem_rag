# tests/backend/memory/test_access_control.py
"""Unit tests for role-based memory access control.

Tests cover:
- Role-based access decisions
- Patient context isolation
- Shared memory access
- Audit logging
"""

import pytest

from backend.memory.access_control import (
    AccessDecision,
    AccessLevel,
    AccessRequest,
    MemoryAccessControl,
    MemoryScope,
    RolePermissions,
)
from backend.memory.config import AccessControlConfig


class TestAccessLevel:
    """Tests for AccessLevel enum."""

    def test_access_levels_exist(self):
        """Should have all expected access levels."""
        assert AccessLevel.NONE.value == "none"
        assert AccessLevel.READ.value == "read"
        assert AccessLevel.WRITE.value == "write"
        assert AccessLevel.ADMIN.value == "admin"


class TestMemoryScope:
    """Tests for MemoryScope enum."""

    def test_memory_scopes_exist(self):
        """Should have all expected memory scopes."""
        assert MemoryScope.OWN.value == "own"
        assert MemoryScope.SHARED.value == "shared"
        assert MemoryScope.OTHER_AGENT.value == "other_agent"
        assert MemoryScope.ALL.value == "all"


class TestRolePermissions:
    """Tests for RolePermissions dataclass."""

    def test_default_permissions(self):
        """Should have sensible defaults."""
        perms = RolePermissions(role_name="TestAgent")
        assert perms.can_access_own == AccessLevel.WRITE
        assert perms.can_access_shared == AccessLevel.READ
        assert perms.can_access_other == AccessLevel.NONE
        assert perms.patient_isolation_required is True

    def test_custom_permissions(self):
        """Should accept custom permission settings."""
        perms = RolePermissions(
            role_name="SuperAgent",
            can_access_own=AccessLevel.ADMIN,
            can_access_shared=AccessLevel.WRITE,
            can_access_other=AccessLevel.READ,
            patient_isolation_required=False,
        )
        assert perms.can_access_own == AccessLevel.ADMIN
        assert perms.can_access_other == AccessLevel.READ


class TestMemoryAccessControl:
    """Tests for MemoryAccessControl."""

    @pytest.fixture
    def access_control(self):
        """Create access control with default config."""
        config = AccessControlConfig(
            role_isolation_enabled=True,
            shared_memory_enabled=True,
            audit_logging_enabled=False,  # Disable for tests
        )
        return MemoryAccessControl(config=config)

    # === Own Memory Access ===

    def test_own_memory_read_allowed(self, access_control):
        """Agents should be able to read their own memory."""
        request = AccessRequest(
            agent_role="ClinicalExtractorAgent",
            operation="read",
            memory_type="vector",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True
        assert decision.scope == MemoryScope.OWN

    def test_own_memory_write_allowed(self, access_control):
        """Agents should be able to write to their own memory."""
        request = AccessRequest(
            agent_role="SummarizationAgent",
            operation="write",
            memory_type="entity",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True
        assert decision.access_level == AccessLevel.WRITE

    def test_own_memory_search_allowed(self, access_control):
        """Agents should be able to search their own memory."""
        request = AccessRequest(
            agent_role="PreprocessingAgent",
            operation="search",
            memory_type="session",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True

    # === Shared Memory Access ===

    def test_shared_memory_read_allowed(self, access_control):
        """Agents should be able to read shared memory."""
        request = AccessRequest(
            agent_role="LanguageAssessorAgent",
            operation="read",
            memory_type="vector",
            target_agent_role="shared",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True
        assert decision.scope == MemoryScope.SHARED

    def test_shared_memory_write_by_preprocessing(self, access_control):
        """PreprocessingAgent should be able to write to shared memory."""
        request = AccessRequest(
            agent_role="PreprocessingAgent",
            operation="write",
            memory_type="vector",
            target_agent_role="shared",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True

    def test_shared_memory_write_denied_for_read_only(self, access_control):
        """Agents with read-only shared access should not write."""
        request = AccessRequest(
            agent_role="SummarizationAgent",
            operation="write",
            memory_type="vector",
            target_agent_role="shared",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is False
        assert "higher access level" in decision.reason

    def test_shared_memory_disabled(self):
        """Shared memory access should be denied when disabled."""
        config = AccessControlConfig(shared_memory_enabled=False)
        ac = MemoryAccessControl(config=config)

        request = AccessRequest(
            agent_role="PreprocessingAgent",
            operation="read",
            memory_type="vector",
            target_agent_role="shared",
        )
        decision = ac.check_access(request)

        assert decision.allowed is False
        assert "No access" in decision.reason

    # === Other Agent Memory Access ===

    def test_other_agent_memory_denied(self, access_control):
        """Agents should not access other agents' memory by default."""
        request = AccessRequest(
            agent_role="SummarizationAgent",
            operation="read",
            memory_type="vector",
            target_agent_role="ClinicalExtractorAgent",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is False
        assert decision.scope == MemoryScope.NONE

    def test_qc_can_read_other_agents(self, access_control):
        """QualityControlAgent should be able to read other agents' memory."""
        request = AccessRequest(
            agent_role="QualityControlAgent",
            operation="read",
            memory_type="vector",
            target_agent_role="ClinicalExtractorAgent",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True

    # === Operation Restrictions ===

    def test_unsupported_operation_denied(self, access_control):
        """Should deny unsupported operations."""
        # Set up custom permissions with only read
        access_control.set_role_permissions(
            "RestrictedAgent",
            RolePermissions(
                role_name="RestrictedAgent",
                allowed_operations=["read"],  # Only read allowed
            ),
        )

        request = AccessRequest(
            agent_role="RestrictedAgent",
            operation="write",  # Trying write, which is not allowed
            memory_type="session",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is False
        assert "not allowed" in decision.reason

    def test_unsupported_memory_type_denied(self, access_control):
        """Should deny access to unsupported memory types."""
        access_control.set_role_permissions(
            "LimitedAgent",
            RolePermissions(
                role_name="LimitedAgent",
                allowed_memory_types=["session"],
            ),
        )

        request = AccessRequest(
            agent_role="LimitedAgent",
            operation="read",
            memory_type="vector",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is False
        assert "Memory type" in decision.reason

    # === Patient Context Isolation ===

    def test_patient_context_first_access(self, access_control):
        """First access to a patient context should register it."""
        request = AccessRequest(
            agent_role="ClinicalExtractorAgent",
            operation="read",
            memory_type="entity",
            session_id="session-123",
            patient_context_id="patient-456",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True
        assert "patient-456" in access_control.get_allowed_patient_contexts("session-123")

    def test_patient_context_same_patient_allowed(self, access_control):
        """Subsequent access to same patient should be allowed."""
        # First access registers the patient
        access_control.register_patient_context("session-123", "patient-456")

        request = AccessRequest(
            agent_role="SummarizationAgent",
            operation="read",
            memory_type="entity",
            session_id="session-123",
            patient_context_id="patient-456",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True

    def test_patient_context_different_patient_denied(self, access_control):
        """Access to different patient should be denied."""
        # Register one patient
        access_control.register_patient_context("session-123", "patient-456")

        # Try to access different patient
        request = AccessRequest(
            agent_role="ClinicalExtractorAgent",
            operation="read",
            memory_type="entity",
            session_id="session-123",
            patient_context_id="patient-789",  # Different patient
        )
        decision = access_control.check_access(request)

        assert decision.allowed is False
        assert "not authorized" in decision.reason

    def test_patient_context_isolation_disabled(self):
        """Patient isolation should be skipped when disabled."""
        config = AccessControlConfig(role_isolation_enabled=False)
        ac = MemoryAccessControl(config=config)

        # Register one patient
        ac.register_patient_context("session-123", "patient-456")

        # Access different patient - should be allowed when isolation disabled
        request = AccessRequest(
            agent_role="ClinicalExtractorAgent",
            operation="read",
            memory_type="entity",
            session_id="session-123",
            patient_context_id="patient-789",
        )
        decision = ac.check_access(request)

        assert decision.allowed is True

    # === Custom Role Configuration ===

    def test_set_custom_role_permissions(self, access_control):
        """Should allow setting custom role permissions."""
        access_control.set_role_permissions(
            "CustomAgent",
            RolePermissions(
                role_name="CustomAgent",
                can_access_own=AccessLevel.ADMIN,
                can_access_shared=AccessLevel.WRITE,
                can_access_other=AccessLevel.READ,
                allowed_operations=["read", "write", "search", "delete"],  # Include delete
            ),
        )

        # Test own access with delete operation
        request = AccessRequest(
            agent_role="CustomAgent",
            operation="delete",
            memory_type="vector",
        )
        decision = access_control.check_access(request)

        assert decision.allowed is True
        assert decision.access_level == AccessLevel.ADMIN

    def test_unknown_role_gets_defaults(self, access_control):
        """Unknown roles should get default permissions."""
        request = AccessRequest(
            agent_role="UnknownAgent",
            operation="read",
            memory_type="session",
        )
        decision = access_control.check_access(request)

        # Should have basic own access
        assert decision.allowed is True
        assert decision.scope == MemoryScope.OWN
