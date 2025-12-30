"""Session management utilities for Chainlit UI."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import chainlit as cl

logger = logging.getLogger(__name__)


def _get_user_session() -> Any:
    """Get the chainlit user_session, importing lazily."""
    import chainlit as cl

    return cl.user_session


class UserRole(str, Enum):
    """User roles for role-based access control."""

    GP = "gp"
    PATIENT = "patient"
    ADMIN = "admin"

    @classmethod
    def from_string(cls, value: str) -> "UserRole":
        """Convert string to UserRole, defaulting to PATIENT."""
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"Unknown role '{value}', defaulting to PATIENT")
            return cls.PATIENT


@dataclass
class UserSession:
    """Represents a user session with role information."""

    user_id: str
    role: UserRole
    email: str | None = None
    display_name: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_gp(self) -> bool:
        """Check if user has GP role."""
        return self.role == UserRole.GP

    @property
    def is_patient(self) -> bool:
        """Check if user has Patient role."""
        return self.role == UserRole.PATIENT

    @property
    def is_admin(self) -> bool:
        """Check if user has Admin role."""
        return self.role == UserRole.ADMIN


class SessionManager:
    """Manages user sessions for the Chainlit application."""

    SESSION_KEY = "user_session"
    CONVERSATION_KEY = "conversation_history"
    AGENT_KEY = "current_agent"

    @classmethod
    def create_session(
        cls,
        user_id: str,
        role: str | UserRole,
        email: str | None = None,
        display_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UserSession:
        """Create and store a new user session."""
        if isinstance(role, str):
            role = UserRole.from_string(role)

        session = UserSession(
            user_id=user_id,
            role=role,
            email=email,
            display_name=display_name,
            metadata=metadata or {},
        )

        user_session = _get_user_session()
        user_session.set(cls.SESSION_KEY, session)
        user_session.set(cls.CONVERSATION_KEY, [])

        logger.info(f"Created session for user {user_id} with role {role.value}")
        return session

    @classmethod
    def get_session(cls) -> UserSession | None:
        """Get the current user session."""
        return _get_user_session().get(cls.SESSION_KEY)

    @classmethod
    def get_role(cls) -> UserRole | None:
        """Get the current user's role."""
        session = cls.get_session()
        return session.role if session else None

    @classmethod
    def get_role_display(cls) -> str:
        """Get a display-friendly role string."""
        session = cls.get_session()
        if not session:
            return "Unknown"

        role_display_map = {
            UserRole.GP: "GP (General Practitioner)",
            UserRole.PATIENT: "Patient",
            UserRole.ADMIN: "Administrator",
        }
        return role_display_map.get(session.role, session.role.value.title())

    @classmethod
    def add_to_conversation(cls, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        user_session = _get_user_session()
        history = user_session.get(cls.CONVERSATION_KEY) or []
        history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        user_session.set(cls.CONVERSATION_KEY, history)

    @classmethod
    def get_conversation_history(cls) -> list[dict[str, Any]]:
        """Get the conversation history."""
        return _get_user_session().get(cls.CONVERSATION_KEY) or []

    @classmethod
    def clear_conversation(cls) -> None:
        """Clear the conversation history."""
        _get_user_session().set(cls.CONVERSATION_KEY, [])

    @classmethod
    def set_current_agent(cls, agent_name: str) -> None:
        """Set the current agent being used."""
        _get_user_session().set(cls.AGENT_KEY, agent_name)

    @classmethod
    def get_current_agent(cls) -> str | None:
        """Get the current agent name."""
        return _get_user_session().get(cls.AGENT_KEY)
