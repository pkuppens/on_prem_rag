"""Message handling for Chainlit UI."""

from __future__ import annotations

import logging
from typing import Any, Sequence

import chainlit as cl  # pyright: ignore[reportMissingImports]

from frontend.chat.handlers.audio_handler import get_audio_handler, is_audio_file
from frontend.chat.utils.session import SessionManager, UserRole

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles incoming chat messages and routes them appropriately."""

    def __init__(self):
        self._agent_handler = None
        self._document_handler = None

    def set_agent_handler(self, handler: Any) -> None:
        """Set the agent callback handler."""
        self._agent_handler = handler

    def set_document_handler(self, handler: Any) -> None:
        """Set the document upload handler."""
        self._document_handler = handler

    async def handle_message(self, message: cl.Message) -> None:
        """Process an incoming message from the user.

        Routes the message to the appropriate agent based on user role
        and message content.
        """
        session = SessionManager.get_session()
        if not session:
            await cl.Message(content="Session not found. Please refresh and log in again.").send()
            return

        # Add to conversation history
        SessionManager.add_to_conversation("user", message.content)

        # Check for file uploads
        if message.elements:
            await self._handle_file_uploads(message.elements, message.content)
            return

        # Route to appropriate agent
        await self._route_to_agent(message.content, session.role)

    async def _handle_file_uploads(self, elements: Sequence[Any], message_content: str) -> None:
        """Handle file uploads attached to a message.

        Routes audio files to the audio handler for transcription,
        and document files to the document handler.
        """
        # Separate audio and document files
        audio_files = [el for el in elements if is_audio_file(el)]
        document_files = [el for el in elements if not is_audio_file(el)]

        # Process audio files first (they become text input)
        transcribed_texts = []
        if audio_files:
            audio_handler = get_audio_handler()
            for audio_el in audio_files:
                text = await audio_handler.handle_audio_upload(audio_el)
                if text:
                    transcribed_texts.append(text)

        # If we have transcribed text, add it to the message content
        if transcribed_texts:
            combined_text = " ".join(transcribed_texts)
            if message_content:
                full_content = f"{message_content} {combined_text}"
            else:
                full_content = combined_text

            # Route the transcribed text to the agent
            session = SessionManager.get_session()
            if session:
                await self._route_to_agent(full_content, session.role)
            return

        # Process document files
        if document_files:
            if self._document_handler:
                await self._document_handler.handle_uploads(document_files, message_content)
            else:
                # Fallback handling
                file_names = [el.name for el in document_files if hasattr(el, "name")]
                await cl.Message(
                    content=f"Received {len(document_files)} file(s): {', '.join(file_names)}. Document processing is being set up."
                ).send()

    async def _route_to_agent(self, content: str, role: UserRole) -> None:
        """Route the message to the appropriate agent based on role."""
        if self._agent_handler:
            await self._agent_handler.process_message(content, role)
        else:
            # Fallback response when agent handler not configured
            await self._send_fallback_response(content, role)

    async def _send_fallback_response(self, content: str, role: UserRole) -> None:
        """Send a fallback response when agents aren't configured."""
        role_context = {
            UserRole.GP: "As a GP, you have access to clinical analysis features.",
            UserRole.PATIENT: "As a patient, you can ask questions about your health documents.",
            UserRole.ADMIN: "As an administrator, you have full system access.",
        }

        context_msg = role_context.get(role, "")

        response = cl.Message(content="")
        await response.send()

        # Stream the response
        full_response = (
            f"I received your message: '{content[:100]}{'...' if len(content) > 100 else ''}'\n\n"
            f"{context_msg}\n\n"
            "The agent framework is initializing. Please ensure the backend services are running."
        )

        for char in full_response:
            await response.stream_token(char)

        await response.update()

        # Add to conversation history
        SessionManager.add_to_conversation("assistant", full_response)


# Global message handler instance
_message_handler: MessageHandler | None = None


def get_message_handler() -> MessageHandler:
    """Get the global message handler instance."""
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler()
    return _message_handler
