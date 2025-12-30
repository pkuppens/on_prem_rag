"""Main Chainlit application for the On-Prem RAG Assistant.

This module provides the entry point for the Chainlit-based chat UI,
integrating authentication, agent callbacks, and document processing.

Usage:
    uv run start-chat
    # or directly:
    chainlit run src/frontend/chat/app.py
"""

import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path

import chainlit as cl
import engineio.payload

from frontend.chat.auth.oauth_integration import get_role_badge_html, setup_user_session
from frontend.chat.auth.oauth_integration import oauth_callback as _oauth_callback
from frontend.chat.auth.oauth_integration import password_auth_callback as _password_auth_callback
from frontend.chat.handlers.agent_callbacks import get_agent_handler
from frontend.chat.handlers.document_upload import get_document_handler
from frontend.chat.handlers.message_handler import get_message_handler
from frontend.chat.utils.session import SessionManager, UserRole

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
SHOW_ROLE_ON_START = os.getenv("SHOW_ROLE_ON_START", "true").lower() == "true"

# Engine.IO sometimes raises "Too many packets in payload" on startup when the browser
# sends a burst of polling packets. Keep the secure upstream default (16) unless we're
# in local-dev, where we can safely allow more to avoid noisy console errors.
#
# Security note: raising this limit can make the server more susceptible to DoS if exposed.
_configured_engineio_max_decode_packets = os.getenv("ENGINEIO_MAX_DECODE_PACKETS")
if _configured_engineio_max_decode_packets:
    engineio.payload.Payload.max_decode_packets = int(_configured_engineio_max_decode_packets)
else:
    # Local development heuristic: when binding to localhost only, allow more packets.
    if os.getenv("CHAINLIT_HOST") in (None, "", "127.0.0.1", "localhost"):
        engineio.payload.Payload.max_decode_packets = 128


@cl.password_auth_callback
def password_auth_callback(username: str, password: str):
    """Authenticate a user with username/password for local development.

    This enables a visible login form in the Chainlit UI during development.
    Demo credentials are defined in `frontend.chat.auth.oauth_integration.DEMO_USERS`.
    """
    return _password_auth_callback(username, password)


def oauth_callback(provider_id: str, token: str, raw_user_data: dict[str, str], default_user):
    """Authenticate a user via OAuth callback.

    Note: OAuth provider configuration is handled by the auth service.
    """
    return _oauth_callback(provider_id, token, raw_user_data, default_user)


# Register OAuth callback only when Chainlit OAuth providers are configured.
# Otherwise Chainlit raises at import time, preventing the app from starting.
try:
    cl.oauth_callback(oauth_callback)
except ValueError:
    logger.info("OAuth providers not configured; skipping Chainlit OAuth callback registration.")


def _initialize_handlers() -> None:
    """Initialize and wire up the handlers."""
    message_handler = get_message_handler()
    agent_handler = get_agent_handler()
    document_handler = get_document_handler()

    # Wire handlers together
    message_handler.set_agent_handler(agent_handler)
    message_handler.set_document_handler(document_handler)

    # Try to connect to backend services
    _try_connect_backend_services(agent_handler, document_handler)


def _try_connect_backend_services(agent_handler, document_handler) -> None:
    """Try to connect to backend services (orchestrator, document processor)."""
    try:
        # Try to import and connect to the orchestrator
        from backend.rag_pipeline.agents.orchestrator import create_medical_orchestrator

        orchestrator = create_medical_orchestrator()
        agent_handler.set_orchestrator(orchestrator)
        logger.info("Connected to CrewAI orchestrator")
    except ImportError:
        logger.warning("CrewAI orchestrator not available - using fallback responses")
    except Exception as e:
        logger.warning(f"Could not connect to orchestrator: {e}")

    try:
        # Try to connect to guardrails
        from backend.rag_pipeline.guardrails import get_guardrails

        guardrails = get_guardrails()
        agent_handler.set_guardrails(guardrails)
        logger.info("Connected to NeMo Guardrails")
    except ImportError:
        logger.info("NeMo Guardrails not configured")
    except Exception as e:
        logger.warning(f"Could not connect to guardrails: {e}")


@cl.on_chat_start
async def on_chat_start():
    """Handle the start of a new chat session.

    Sets up the user session, displays role information,
    and initializes handlers.
    """
    # Initialize handlers
    _initialize_handlers()

    # Get authenticated user
    user = cl.user_session.get("user")

    if user:
        # Set up user session with role information
        await setup_user_session(user)

        session = SessionManager.get_session()
        if session and SHOW_ROLE_ON_START:
            # Display role badge
            role_badge = get_role_badge_html(session.role)
            welcome_msg = f"Welcome, {session.display_name or session.user_id}!\n\n{role_badge}\n\n"

            # Add role-specific guidance
            if session.is_gp:
                welcome_msg += (
                    "As a GP, you have access to:\n"
                    "- Clinical document analysis\n"
                    "- Medical entity extraction\n"
                    "- Patient record summarization\n\n"
                    "Upload documents or ask questions about medical topics."
                )
            elif session.is_patient:
                welcome_msg += (
                    "As a patient, you can:\n"
                    "- Ask questions about health topics\n"
                    "- Get summaries of medical documents\n"
                    "- Upload your health records for analysis\n\n"
                    "How can I help you today?"
                )
            else:
                welcome_msg += "You have full system access. How can I assist you?"

            await cl.Message(content=welcome_msg).send()
    else:
        # No authenticated user - this shouldn't happen with auth enabled
        await cl.Message(content="Welcome! Please ensure you are logged in to access all features.").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming chat messages.

    Routes messages through the message handler which manages
    agent routing and file uploads.
    """
    handler = get_message_handler()
    await handler.handle_message(message)


@cl.on_stop
async def on_stop():
    """Handle chat session stop/cleanup."""
    session = SessionManager.get_session()
    if session:
        logger.info(f"Chat session ended for user {session.user_id}")


@cl.set_chat_profiles
async def set_chat_profiles(current_user: cl.User):
    """Define available chat profiles based on user role.

    Chat profiles allow users to switch between different
    interaction modes or agent configurations.
    """
    if not current_user:
        return None

    role = current_user.metadata.get("role", "patient")

    # Base profiles available to all users
    profiles = [
        cl.ChatProfile(
            name="General Assistant",
            markdown_description="General-purpose assistant for health questions and document analysis.",
            icon="https://cdn-icons-png.flaticon.com/512/3774/3774299.png",
        ),
    ]

    # GP-specific profiles
    if role in ("gp", "admin"):
        profiles.extend(
            [
                cl.ChatProfile(
                    name="Clinical Analysis",
                    markdown_description="Deep clinical analysis with medical entity extraction and terminology.",
                    icon="https://cdn-icons-png.flaticon.com/512/2785/2785482.png",
                ),
                cl.ChatProfile(
                    name="Document Summary",
                    markdown_description="Quick summarization of medical documents and patient records.",
                    icon="https://cdn-icons-png.flaticon.com/512/2991/2991112.png",
                ),
            ]
        )

    # Admin-specific profiles
    if role == "admin":
        profiles.append(
            cl.ChatProfile(
                name="System Admin",
                markdown_description="Full system access with debugging and monitoring capabilities.",
                icon="https://cdn-icons-png.flaticon.com/512/2099/2099058.png",
            )
        )

    return profiles


@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Handle settings updates from the UI."""
    logger.info(f"Settings updated: {settings}")

    # Update session with new settings
    session = SessionManager.get_session()
    if session:
        session.metadata["settings"] = settings


def main():
    """Entry point for running the Chainlit application."""
    # Get the directory containing this file
    app_dir = Path(__file__).parent

    # Set up environment
    #
    # IMPORTANT:
    # `CHAINLIT_ROOT_PATH` is a URL path prefix (e.g. "/rag"), not a filesystem path.
    # Setting it to something like "C:\\Users\\..." breaks Starlette routing because mounted
    # paths must start with "/" (or be empty).
    root_path = os.getenv("CHAINLIT_ROOT_PATH")
    if root_path and not root_path.startswith("/"):
        os.environ["CHAINLIT_ROOT_PATH"] = f"/{root_path.lstrip('/')}"

    # Chainlit requires `CHAINLIT_AUTH_SECRET` when any login mechanism is enabled
    # (password auth, header auth, custom auth, or OAuth).
    #
    # For local development only, we auto-generate a secret if missing. In production,
    # set `CHAINLIT_AUTH_SECRET` explicitly (or disable auth callbacks).
    host = os.getenv("CHAINLIT_HOST", "localhost")
    if not os.getenv("CHAINLIT_AUTH_SECRET") and host in ("localhost", "127.0.0.1"):
        os.environ["CHAINLIT_AUTH_SECRET"] = secrets.token_urlsafe(32)

    # Run chainlit
    # Note: chainlit.run() is the proper way to start programmatically
    # but for the entry point, we use subprocess to ensure proper startup
    cmd = [
        sys.executable,
        "-m",
        "chainlit",
        "run",
        str(app_dir / "app.py"),
        "--host",
        host,
        "--port",
        os.getenv("CHAINLIT_PORT", "8002"),
    ]

    logger.info(f"Starting Chainlit UI: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
