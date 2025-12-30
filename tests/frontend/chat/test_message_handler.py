"""Tests for message handling.

As a developer I want message handling to route correctly,
so I can ensure users get appropriate responses based on their role.
Technical: Test MessageHandler class and routing logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.frontend.chat.conftest import get_mock_chainlit

mock_cl = get_mock_chainlit()

from frontend.chat.handlers.message_handler import MessageHandler, get_message_handler
from frontend.chat.utils.session import UserRole, UserSession


class TestMessageHandler:
    """Tests for MessageHandler class."""

    @pytest.fixture
    def message_handler(self):
        """Create a message handler instance for testing."""
        return MessageHandler()

    @pytest.fixture
    def mock_message(self):
        """Create a mock Chainlit message."""
        message = MagicMock()
        message.content = "Test message content"
        message.elements = []
        return message

    @pytest.fixture
    def mock_session(self):
        """Create a mock user session."""
        return UserSession(user_id="test-user", role=UserRole.GP, display_name="Dr. Test")

    def test_initialization(self, message_handler):
        """As a developer I want handler to initialize without dependencies,
        so I can set them up later during configuration.
        Technical: Test MessageHandler initialization.
        """
        assert message_handler._agent_handler is None
        assert message_handler._document_handler is None

    def test_set_agent_handler(self, message_handler):
        """As a developer I want to set the agent handler,
        so I can integrate with the agent framework.
        Technical: Test set_agent_handler method.
        """
        mock_agent_handler = MagicMock()
        message_handler.set_agent_handler(mock_agent_handler)

        assert message_handler._agent_handler == mock_agent_handler

    def test_set_document_handler(self, message_handler):
        """As a developer I want to set the document handler,
        so I can integrate with document processing.
        Technical: Test set_document_handler method.
        """
        mock_doc_handler = MagicMock()
        message_handler.set_document_handler(mock_doc_handler)

        assert message_handler._document_handler == mock_doc_handler

    @pytest.mark.asyncio
    @patch("frontend.chat.handlers.message_handler.SessionManager")
    async def test_handle_message_no_session(self, mock_session_manager, message_handler, mock_message):
        """As a developer I want missing sessions to be handled gracefully,
        so I can provide helpful error messages.
        Technical: Test handling when no session exists.
        """
        mock_session_manager.get_session.return_value = None
        mock_msg = AsyncMock()
        mock_cl.Message.return_value = mock_msg

        await message_handler.handle_message(mock_message)

        # Should send error message
        mock_cl.Message.assert_called()

    @pytest.mark.asyncio
    @patch("frontend.chat.handlers.message_handler.SessionManager")
    async def test_handle_message_with_files(self, mock_session_manager, message_handler, mock_message, mock_session):
        """As a developer I want file uploads to be handled,
        so I can process document attachments.
        Technical: Test message with file elements triggers document handler.
        """
        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.add_to_conversation = MagicMock()

        # Add mock file element
        mock_file = MagicMock()
        mock_file.name = "test.pdf"
        mock_message.elements = [mock_file]

        mock_doc_handler = AsyncMock()
        message_handler.set_document_handler(mock_doc_handler)

        await message_handler.handle_message(mock_message)

        mock_doc_handler.handle_uploads.assert_called_once()

    @pytest.mark.asyncio
    @patch("frontend.chat.handlers.message_handler.SessionManager")
    async def test_handle_message_routes_to_agent(self, mock_session_manager, message_handler, mock_message, mock_session):
        """As a developer I want messages to route to the agent handler,
        so I can process user queries through the AI agents.
        Technical: Test message routing to agent handler.
        """
        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.add_to_conversation = MagicMock()

        mock_agent_handler = AsyncMock()
        message_handler.set_agent_handler(mock_agent_handler)

        await message_handler.handle_message(mock_message)

        mock_agent_handler.process_message.assert_called_once_with(mock_message.content, mock_session.role)


class TestGetMessageHandler:
    """Tests for get_message_handler singleton."""

    def test_get_message_handler_returns_singleton(self):
        """As a developer I want a singleton message handler,
        so I can share state across the application.
        Technical: Test get_message_handler returns same instance.
        """
        # Reset global state
        import frontend.chat.handlers.message_handler as module

        module._message_handler = None

        handler1 = get_message_handler()
        handler2 = get_message_handler()

        assert handler1 is handler2
