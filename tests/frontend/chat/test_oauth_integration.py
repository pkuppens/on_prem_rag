"""Tests for OAuth integration.

As a developer I want OAuth integration to work correctly,
so I can authenticate users through various providers.
Technical: Test OAuthIntegration, auth callbacks, and role extraction.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.frontend.chat.conftest import get_mock_chainlit

mock_cl = get_mock_chainlit()

from frontend.chat.auth.oauth_integration import (
    DEMO_USERS,
    OAuthIntegration,
    _extract_role_from_oauth_data,
    get_role_badge_html,
    password_auth_callback,
)
from frontend.chat.utils.session import UserRole


class TestExtractRoleFromOAuthData:
    """Tests for _extract_role_from_oauth_data function."""

    def test_explicit_role_claim(self):
        """As a developer I want explicit role claims to be used first,
        so I can support standard role-based OAuth configurations.
        Technical: Test role extraction from explicit 'role' claim.
        """
        data = {"role": "gp", "email": "user@example.com"}
        assert _extract_role_from_oauth_data(data) == "gp"

    def test_roles_array_with_gp(self):
        """As a developer I want GP role prioritized in roles array,
        so I can handle multi-role users appropriately.
        Technical: Test role extraction from 'roles' array.
        """
        data = {"roles": ["user", "gp", "viewer"]}
        assert _extract_role_from_oauth_data(data) == "gp"

    def test_roles_array_with_doctor(self):
        """As a developer I want 'doctor' mapped to GP role,
        so I can handle different terminology for medical professionals.
        Technical: Test doctor role is converted to gp.
        """
        data = {"roles": ["doctor"]}
        assert _extract_role_from_oauth_data(data) == "gp"

    def test_roles_array_with_admin(self):
        """As a developer I want admin roles recognized,
        so I can grant administrative access appropriately.
        Technical: Test admin role extraction.
        """
        data = {"roles": ["admin"]}
        assert _extract_role_from_oauth_data(data) == "admin"

    def test_group_membership_gp(self):
        """As a developer I want group membership to determine roles,
        so I can integrate with group-based access control.
        Technical: Test role extraction from groups.
        """
        data = {"groups": ["Medical-GPs", "AllStaff"]}
        assert _extract_role_from_oauth_data(data) == "gp"

    def test_group_membership_admin(self):
        """As a developer I want admin groups recognized,
        so I can grant admin access based on group membership.
        Technical: Test admin role from groups.
        """
        data = {"groups": ["Administrators"]}
        assert _extract_role_from_oauth_data(data) == "admin"

    def test_default_to_patient(self):
        """As a developer I want unknown roles to default to patient,
        so I can provide safe default access.
        Technical: Test fallback to patient role.
        """
        data = {"email": "user@example.com"}
        assert _extract_role_from_oauth_data(data) == "patient"

        data = {"roles": []}
        assert _extract_role_from_oauth_data(data) == "patient"

        data = {}
        assert _extract_role_from_oauth_data(data) == "patient"


class TestPasswordAuthCallback:
    """Tests for password_auth_callback function."""

    def test_valid_gp_credentials(self):
        """As a developer I want GP demo users to authenticate,
        so I can test GP functionality without OAuth.
        Technical: Test GP demo user authentication.
        """
        user = password_auth_callback("gp", "gp123")

        assert user is not None
        mock_cl.User.assert_called()
        call_kwargs = mock_cl.User.call_args[1]
        assert call_kwargs["identifier"] == "gp-user-1"
        assert call_kwargs["metadata"]["role"] == "gp"

    def test_valid_patient_credentials(self):
        """As a developer I want patient demo users to authenticate,
        so I can test patient functionality without OAuth.
        Technical: Test patient demo user authentication.
        """
        user = password_auth_callback("patient", "patient123")

        assert user is not None
        call_kwargs = mock_cl.User.call_args[1]
        assert call_kwargs["identifier"] == "patient-user-1"
        assert call_kwargs["metadata"]["role"] == "patient"

    def test_valid_admin_credentials(self):
        """As a developer I want admin demo users to authenticate,
        so I can test admin functionality without OAuth.
        Technical: Test admin demo user authentication.
        """
        user = password_auth_callback("admin", "admin123")

        assert user is not None
        call_kwargs = mock_cl.User.call_args[1]
        assert call_kwargs["identifier"] == "admin-user-1"
        assert call_kwargs["metadata"]["role"] == "admin"

    def test_invalid_credentials(self):
        """As a developer I want invalid credentials to fail,
        so I can prevent unauthorized access.
        Technical: Test authentication failure for wrong credentials.
        """
        user = password_auth_callback("invalid", "wrong")
        assert user is None

        user = password_auth_callback("gp", "wrong")
        assert user is None


class TestGetRoleBadgeHtml:
    """Tests for get_role_badge_html function."""

    def test_gp_badge(self):
        """As a developer I want GP role to have a clear badge,
        so I can display role in the UI.
        Technical: Test GP badge generation.
        """
        badge = get_role_badge_html(UserRole.GP)
        assert "GP" in badge

    def test_patient_badge(self):
        """As a developer I want patient role to have a clear badge,
        so I can display role in the UI.
        Technical: Test patient badge generation.
        """
        badge = get_role_badge_html(UserRole.PATIENT)
        assert "Patient" in badge

    def test_admin_badge(self):
        """As a developer I want admin role to have a clear badge,
        so I can display role in the UI.
        Technical: Test admin badge generation.
        """
        badge = get_role_badge_html(UserRole.ADMIN)
        assert "Admin" in badge


class TestOAuthIntegration:
    """Tests for OAuthIntegration class."""

    @pytest.fixture
    def oauth_integration(self):
        """Create an OAuth integration instance for testing."""
        return OAuthIntegration("http://localhost:8001")

    def test_initialization(self, oauth_integration):
        """As a developer I want OAuth integration to initialize properly,
        so I can connect to the auth service.
        Technical: Test OAuthIntegration initialization.
        """
        assert oauth_integration.auth_service_url == "http://localhost:8001"
        assert oauth_integration._http_client is None

    @pytest.mark.asyncio
    async def test_validate_token_success(self, oauth_integration):
        """As a developer I want successful token validation,
        so I can authenticate users with valid tokens.
        Technical: Test token validation with mock response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "user-1", "email": "user@example.com"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        oauth_integration._http_client = mock_client

        result = await oauth_integration.validate_token("valid-token")

        assert result == {"id": "user-1", "email": "user@example.com"}
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_token_failure(self, oauth_integration):
        """As a developer I want invalid tokens to fail validation,
        so I can reject unauthorized requests.
        Technical: Test token validation with failed response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        oauth_integration._http_client = mock_client

        result = await oauth_integration.validate_token("invalid-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_close_client(self, oauth_integration):
        """As a developer I want to properly close HTTP clients,
        so I can avoid resource leaks.
        Technical: Test client cleanup on close.
        """
        mock_client = AsyncMock()
        oauth_integration._http_client = mock_client

        await oauth_integration.close()

        mock_client.aclose.assert_called_once()
        assert oauth_integration._http_client is None


class TestDemoUsers:
    """Tests for demo user configuration."""

    def test_demo_users_defined(self):
        """As a developer I want demo users to be defined,
        so I can test without OAuth setup.
        Technical: Test DEMO_USERS dictionary exists.
        """
        assert ("gp", "gp123") in DEMO_USERS
        assert ("patient", "patient123") in DEMO_USERS
        assert ("admin", "admin123") in DEMO_USERS

    def test_demo_user_structure(self):
        """As a developer I want demo users to have required fields,
        so I can create valid user objects.
        Technical: Test demo user dictionary structure.
        """
        for credentials, user_info in DEMO_USERS.items():
            assert "id" in user_info
            assert "role" in user_info
            assert "name" in user_info
