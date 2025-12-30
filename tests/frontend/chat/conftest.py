"""Pytest configuration for Chainlit chat UI tests.

Sets up chainlit mocking to avoid import errors during testing.
"""

import sys
from unittest.mock import MagicMock

# Create a comprehensive mock for chainlit module
mock_chainlit = MagicMock()
mock_chainlit.user_session = MagicMock()
mock_chainlit.User = MagicMock()
mock_chainlit.Message = MagicMock()
mock_chainlit.Step = MagicMock()

# Set up Step as a context manager
mock_step_instance = MagicMock()
mock_step_instance.__aenter__ = MagicMock(return_value=mock_step_instance)
mock_step_instance.__aexit__ = MagicMock(return_value=None)
mock_chainlit.Step.return_value = mock_step_instance

# Install the mock before any frontend.chat imports
sys.modules["chainlit"] = mock_chainlit


def get_mock_chainlit():
    """Return the mocked chainlit module for test assertions."""
    return mock_chainlit
