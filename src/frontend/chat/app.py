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
import subprocess
import sys
from pathlib import Path

import chainlit as cl

from frontend.chat.auth.oauth_integration import get_role_badge_html, setup_user_session
from frontend.chat.handlers.agent_callbacks import get_agent_handler
from frontend.chat.handlers.document_upload import get_document_handler
from frontend.chat.handlers.message_handler import get_message_handler
from frontend.chat.utils.session import SessionManager, UserRole

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
SHOW_ROLE_ON_START = os.getenv("SHOW_ROLE_ON_START", "true").lower() == "true"


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
    os.environ.setdefault("CHAINLIT_ROOT_PATH", str(app_dir))

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
        os.getenv("CHAINLIT_HOST", "0.0.0.0"),
        "--port",
        os.getenv("CHAINLIT_PORT", "8002"),
    ]

    logger.info(f"Starting Chainlit UI: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
