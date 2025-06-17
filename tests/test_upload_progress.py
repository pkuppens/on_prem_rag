"""Integration tests for upload progress reporting.

This module previously contained tests for WebSocket functionality and progress reporting.
These tests have been moved to test_websocket.py for better maintainability and consistency.
The test_websocket.py module now contains all WebSocket-related tests, including:
- Progress updates during file uploads
- Ping/pong functionality
- Initial state reporting
- Edge cases and cleanup

This file is kept for historical reference and may be removed in the future.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_data_dir() -> Path:
    """Get the path to the test data directory."""
    return Path(__file__).parent / "test_data"
