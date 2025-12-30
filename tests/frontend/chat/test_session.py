"""Tests for session management utilities.

As a developer I want session management to work correctly,
so I can ensure user roles and data are properly tracked.
Technical: Test UserSession, SessionManager, and UserRole classes.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from tests.frontend.chat.conftest import get_mock_chainlit

mock_cl = get_mock_chainlit()

from frontend.chat.utils.session import SessionManager, UserRole, UserSession


class TestUserRole:
    """Tests for UserRole enum."""

    def test_user_role_values(self):
        """As a developer I want role values to be lowercase strings,
        so I can use them consistently in the application.
        Technical: Verify enum values match expected lowercase strings.
        """
        assert UserRole.GP.value == "gp"
        assert UserRole.PATIENT.value == "patient"
        assert UserRole.ADMIN.value == "admin"

    def test_from_string_valid_role(self):
        """As a developer I want to convert strings to UserRole,
        so I can handle role data from various sources.
        Technical: Test from_string with valid role strings.
        """
        assert UserRole.from_string("gp") == UserRole.GP
        assert UserRole.from_string("GP") == UserRole.GP
        assert UserRole.from_string("patient") == UserRole.PATIENT
        assert UserRole.from_string("PATIENT") == UserRole.PATIENT
        assert UserRole.from_string("admin") == UserRole.ADMIN

    def test_from_string_invalid_role_defaults_to_patient(self):
        """As a developer I want invalid roles to default to PATIENT,
        so I can handle unexpected input gracefully.
        Technical: Test from_string with invalid role strings.
        """
        assert UserRole.from_string("invalid") == UserRole.PATIENT
        assert UserRole.from_string("") == UserRole.PATIENT
        assert UserRole.from_string("doctor") == UserRole.PATIENT


class TestUserSession:
    """Tests for UserSession dataclass."""

    def test_user_session_creation(self):
        """As a developer I want to create user sessions with required fields,
        so I can track user information throughout the session.
        Technical: Test UserSession instantiation with basic fields.
        """
        session = UserSession(user_id="test-user", role=UserRole.GP)

        assert session.user_id == "test-user"
        assert session.role == UserRole.GP
        assert session.email is None
        assert session.display_name is None
        assert isinstance(session.created_at, datetime)
        assert session.metadata == {}

    def test_user_session_with_all_fields(self):
        """As a developer I want to create sessions with all optional fields,
        so I can store complete user information.
        Technical: Test UserSession with all fields populated.
        """
        created = datetime(2024, 1, 1, 12, 0, 0)
        session = UserSession(
            user_id="user-123",
            role=UserRole.ADMIN,
            email="admin@example.com",
            display_name="Admin User",
            created_at=created,
            metadata={"key": "value"},
        )

        assert session.user_id == "user-123"
        assert session.role == UserRole.ADMIN
        assert session.email == "admin@example.com"
        assert session.display_name == "Admin User"
        assert session.created_at == created
        assert session.metadata == {"key": "value"}

    def test_role_check_properties(self):
        """As a developer I want convenient role check properties,
        so I can easily verify user permissions.
        Technical: Test is_gp, is_patient, is_admin properties.
        """
        gp_session = UserSession(user_id="gp", role=UserRole.GP)
        assert gp_session.is_gp is True
        assert gp_session.is_patient is False
        assert gp_session.is_admin is False

        patient_session = UserSession(user_id="patient", role=UserRole.PATIENT)
        assert patient_session.is_gp is False
        assert patient_session.is_patient is True
        assert patient_session.is_admin is False

        admin_session = UserSession(user_id="admin", role=UserRole.ADMIN)
        assert admin_session.is_gp is False
        assert admin_session.is_patient is False
        assert admin_session.is_admin is True


class TestSessionManager:
    """Tests for SessionManager class."""

    def setup_method(self):
        """Reset mock before each test."""
        mock_cl.user_session.reset_mock()

    def test_create_session(self):
        """As a developer I want to create and store user sessions,
        so I can manage user state during chat interactions.
        Technical: Test create_session stores session correctly.
        """
        mock_cl.user_session.set = MagicMock()

        session = SessionManager.create_session(
            user_id="test-user",
            role="gp",
            email="gp@example.com",
            display_name="Dr. Test",
        )

        assert session.user_id == "test-user"
        assert session.role == UserRole.GP
        assert session.email == "gp@example.com"
        assert session.display_name == "Dr. Test"

        # Verify session was stored
        assert mock_cl.user_session.set.called

    def test_get_session(self):
        """As a developer I want to retrieve the current session,
        so I can access user information during message handling.
        Technical: Test get_session returns stored session.
        """
        expected_session = UserSession(user_id="test", role=UserRole.PATIENT)
        mock_cl.user_session.get = MagicMock(return_value=expected_session)

        session = SessionManager.get_session()

        assert session == expected_session
        mock_cl.user_session.get.assert_called_with(SessionManager.SESSION_KEY)

    def test_get_role(self):
        """As a developer I want to get just the user's role,
        so I can make routing decisions efficiently.
        Technical: Test get_role returns role from session.
        """
        mock_cl.user_session.get = MagicMock(return_value=UserSession(user_id="test", role=UserRole.GP))

        role = SessionManager.get_role()

        assert role == UserRole.GP

    def test_get_role_no_session(self):
        """As a developer I want get_role to handle missing sessions,
        so I can handle unauthenticated states gracefully.
        Technical: Test get_role returns None when no session exists.
        """
        mock_cl.user_session.get = MagicMock(return_value=None)

        role = SessionManager.get_role()

        assert role is None

    def test_get_role_display(self):
        """As a developer I want user-friendly role display strings,
        so I can show role information in the UI.
        Technical: Test get_role_display returns formatted strings.
        """
        mock_cl.user_session.get = MagicMock(return_value=UserSession(user_id="test", role=UserRole.GP))

        display = SessionManager.get_role_display()

        assert display == "GP (General Practitioner)"

    def test_conversation_history_management(self):
        """As a developer I want to manage conversation history,
        so I can maintain context across messages.
        Technical: Test add_to_conversation and get_conversation_history.
        """
        history = []
        mock_cl.user_session.get = MagicMock(return_value=history)
        mock_cl.user_session.set = MagicMock()

        SessionManager.add_to_conversation("user", "Hello")

        # Verify set was called with updated history
        assert mock_cl.user_session.set.called
        call_args = mock_cl.user_session.set.call_args[0]
        assert call_args[0] == SessionManager.CONVERSATION_KEY
        assert len(call_args[1]) == 1
        assert call_args[1][0]["role"] == "user"
        assert call_args[1][0]["content"] == "Hello"

    def test_clear_conversation(self):
        """As a developer I want to clear conversation history,
        so I can reset context when needed.
        Technical: Test clear_conversation resets history to empty list.
        """
        mock_cl.user_session.set = MagicMock()

        SessionManager.clear_conversation()

        mock_cl.user_session.set.assert_called_with(SessionManager.CONVERSATION_KEY, [])

    def test_current_agent_management(self):
        """As a developer I want to track the current agent,
        so I can route messages appropriately.
        Technical: Test set_current_agent and get_current_agent.
        """
        mock_cl.user_session.set = MagicMock()
        mock_cl.user_session.get = MagicMock(return_value="clinical_extractor")

        SessionManager.set_current_agent("clinical_extractor")
        mock_cl.user_session.set.assert_called_with(SessionManager.AGENT_KEY, "clinical_extractor")

        agent = SessionManager.get_current_agent()
        assert agent == "clinical_extractor"
