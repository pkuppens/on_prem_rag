"""Tests for agent callback handling.

As a developer I want agent callbacks to display correctly in the UI,
so I can provide visibility into agent operations.
Technical: Test AgentCallbackHandler class and callback methods.
"""

from unittest.mock import MagicMock

import pytest

from tests.frontend.chat.conftest import get_mock_chainlit

mock_cl = get_mock_chainlit()

from frontend.chat.handlers.agent_callbacks import AgentCallbackHandler, get_agent_handler
from frontend.chat.utils.session import UserRole


class TestAgentCallbackHandler:
    """Tests for AgentCallbackHandler class."""

    @pytest.fixture
    def agent_handler(self):
        """Create an agent handler instance for testing."""
        return AgentCallbackHandler()

    def test_initialization(self, agent_handler):
        """As a developer I want handler to initialize without dependencies,
        so I can configure it during startup.
        Technical: Test AgentCallbackHandler initialization.
        """
        assert agent_handler._orchestrator is None
        assert agent_handler._memory_manager is None
        assert agent_handler._guardrails is None

    def test_set_orchestrator(self, agent_handler):
        """As a developer I want to set the orchestrator,
        so I can integrate with CrewAI agents.
        Technical: Test set_orchestrator method.
        """
        mock_orchestrator = MagicMock()
        agent_handler.set_orchestrator(mock_orchestrator)

        assert agent_handler._orchestrator == mock_orchestrator

    def test_set_memory_manager(self, agent_handler):
        """As a developer I want to set the memory manager,
        so I can provide context to agents.
        Technical: Test set_memory_manager method.
        """
        mock_memory = MagicMock()
        agent_handler.set_memory_manager(mock_memory)

        assert agent_handler._memory_manager == mock_memory

    def test_set_guardrails(self, agent_handler):
        """As a developer I want to set guardrails,
        so I can validate input and output.
        Technical: Test set_guardrails method.
        """
        mock_guardrails = MagicMock()
        agent_handler.set_guardrails(mock_guardrails)

        assert agent_handler._guardrails == mock_guardrails

    def test_get_agent_for_role_gp(self, agent_handler):
        """As a developer I want GP users to get clinical agents,
        so I can provide appropriate medical analysis.
        Technical: Test agent selection for GP role.
        """
        agent = agent_handler._get_agent_for_role(UserRole.GP)
        assert agent == "clinical_extractor"

    def test_get_agent_for_role_patient(self, agent_handler):
        """As a developer I want patient users to get summarization agents,
        so I can provide accessible summaries.
        Technical: Test agent selection for patient role.
        """
        agent = agent_handler._get_agent_for_role(UserRole.PATIENT)
        assert agent == "summarizer"

    def test_get_agent_for_role_admin(self, agent_handler):
        """As a developer I want admin users to get orchestrator access,
        so I can provide full system capabilities.
        Technical: Test agent selection for admin role.
        """
        agent = agent_handler._get_agent_for_role(UserRole.ADMIN)
        assert agent == "quality_controller"

    @pytest.mark.asyncio
    async def test_apply_input_guardrails_no_guardrails(self, agent_handler):
        """As a developer I want input processing without guardrails,
        so I can work when guardrails aren't configured.
        Technical: Test input passes through when no guardrails.
        """
        result = await agent_handler._apply_input_guardrails("test input", MagicMock())
        assert result == "test input"


class TestGetAgentHandler:
    """Tests for get_agent_handler singleton."""

    def test_get_agent_handler_returns_singleton(self):
        """As a developer I want a singleton agent handler,
        so I can share state across the application.
        Technical: Test get_agent_handler returns same instance.
        """
        import frontend.chat.handlers.agent_callbacks as module

        module._agent_handler = None

        handler1 = get_agent_handler()
        handler2 = get_agent_handler()

        assert handler1 is handler2
