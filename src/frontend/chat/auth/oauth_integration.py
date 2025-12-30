"""OAuth integration for Chainlit UI with the existing auth service."""

import logging
import os
from typing import Any

import httpx

from frontend.chat.utils.session import SessionManager, UserRole

logger = logging.getLogger(__name__)

# Configuration from environment
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
OAUTH_GOOGLE_ENABLED = os.getenv("OAUTH_GOOGLE_ENABLED", "true").lower() == "true"
OAUTH_OUTLOOK_ENABLED = os.getenv("OAUTH_OUTLOOK_ENABLED", "false").lower() == "true"


class OAuthIntegration:
    """Handles OAuth integration with the existing auth service."""

    def __init__(self, auth_service_url: str = AUTH_SERVICE_URL):
        self.auth_service_url = auth_service_url
        self._http_client: httpx.AsyncClient | None = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(base_url=self.auth_service_url, timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate a token with the auth service and get user info."""
        try:
            response = await self.http_client.get("/me", headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Token validation failed with status {response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Error validating token: {e}")
            return None

    async def get_oauth_providers(self) -> list[dict[str, str]]:
        """Get available OAuth providers from the auth service."""
        try:
            response = await self.http_client.get("/oauth/providers")
            if response.status_code == 200:
                return response.json()
            return []
        except httpx.RequestError as e:
            logger.error(f"Error fetching OAuth providers: {e}")
            return []


# Global OAuth integration instance
_oauth_integration: OAuthIntegration | None = None


def get_oauth_integration() -> OAuthIntegration:
    """Get the global OAuth integration instance."""
    global _oauth_integration
    if _oauth_integration is None:
        _oauth_integration = OAuthIntegration()
    return _oauth_integration


# Demo users for development/testing
DEMO_USERS = {
    ("gp", "gp123"): {"id": "gp-user-1", "role": "gp", "name": "Dr. Demo GP"},
    ("patient", "patient123"): {"id": "patient-user-1", "role": "patient", "name": "Demo Patient"},
    ("admin", "admin123"): {"id": "admin-user-1", "role": "admin", "name": "Admin User"},
}


def password_auth_callback(username: str, password: str) -> Any:
    """Handle password-based authentication.

    This callback is used for local development and testing.
    In production, OAuth is preferred.

    Note: This function should be decorated with @cl.password_auth_callback
    in the main app module where chainlit is properly initialized.
    """
    import chainlit as cl

    user_info = DEMO_USERS.get((username, password))
    if user_info:
        logger.info(f"Password auth successful for user: {username} with role: {user_info['role']}")
        return cl.User(
            identifier=user_info["id"],
            metadata={
                "role": user_info["role"],
                "name": user_info["name"],
                "auth_method": "password",
            },
        )

    logger.warning(f"Password auth failed for user: {username}")
    return None


def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: Any,
) -> Any:
    """Handle OAuth callback from providers.

    This callback processes the OAuth response and extracts role information.
    Role can be provided via:
    1. Custom claims in the OAuth token
    2. User's group membership
    3. Default to 'patient' if not specified

    Note: This function should be decorated with @cl.oauth_callback
    in the main app module where chainlit is properly initialized.
    """
    import chainlit as cl

    logger.info(f"OAuth callback from provider: {provider_id}")
    logger.debug(f"Raw user data: {raw_user_data}")

    # Extract user information
    user_id = raw_user_data.get("sub") or raw_user_data.get("id") or default_user.identifier
    email = raw_user_data.get("email", "")
    name = raw_user_data.get("name") or raw_user_data.get("given_name", "User")

    # Determine role from various sources
    role = _extract_role_from_oauth_data(raw_user_data)

    logger.info(f"OAuth user authenticated: {user_id} with role: {role}")

    return cl.User(
        identifier=user_id,
        metadata={
            "role": role,
            "name": name,
            "email": email,
            "provider": provider_id,
            "auth_method": "oauth",
            "token": token,  # Store for API calls
        },
    )


def _extract_role_from_oauth_data(raw_user_data: dict[str, Any]) -> str:
    """Extract user role from OAuth data.

    Checks multiple sources for role information:
    1. Explicit 'role' claim
    2. 'roles' array
    3. Group membership
    4. Email domain heuristics
    """
    # Check explicit role claim
    if "role" in raw_user_data:
        return raw_user_data["role"]

    # Check roles array
    roles = raw_user_data.get("roles", [])
    if roles:
        # Prioritize GP role if present
        if "gp" in roles or "doctor" in roles or "physician" in roles:
            return "gp"
        if "admin" in roles or "administrator" in roles:
            return "admin"
        return roles[0]

    # Check group membership
    groups = raw_user_data.get("groups", [])
    for group in groups:
        group_lower = group.lower()
        if "gp" in group_lower or "doctor" in group_lower or "physician" in group_lower:
            return "gp"
        if "admin" in group_lower:
            return "admin"

    # Default to patient
    return "patient"


async def setup_user_session(user: Any) -> None:
    """Set up the user session after authentication."""
    metadata = user.metadata or {}

    role = metadata.get("role", "patient")
    email = metadata.get("email")
    name = metadata.get("name", user.identifier)

    # Create session
    SessionManager.create_session(
        user_id=user.identifier,
        role=role,
        email=email,
        display_name=name,
        metadata=metadata,
    )

    # Determine which agent to use based on role
    user_role = UserRole.from_string(role)
    if user_role == UserRole.GP:
        SessionManager.set_current_agent("medical_analysis")
    else:
        SessionManager.set_current_agent("patient_assistant")


def get_role_badge_html(role: UserRole) -> str:
    """Generate HTML for the role badge displayed in the UI.

    Note: This requires unsafe_allow_html to be enabled in config.
    Returns plain text if HTML is disabled.
    """
    role_styles = {
        UserRole.GP: ("GP", "#1976d2", "#ffffff"),  # Blue
        UserRole.PATIENT: ("Patient", "#388e3c", "#ffffff"),  # Green
        UserRole.ADMIN: ("Admin", "#d32f2f", "#ffffff"),  # Red
    }

    label, bg_color, text_color = role_styles.get(role, ("Unknown", "#757575", "#ffffff"))

    return f"**Role: {label}**"
