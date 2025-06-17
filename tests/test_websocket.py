"""Tests for WebSocket functionality in the RAG pipeline.

This module tests the WebSocket endpoints and progress notification system.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from src.backend.rag_pipeline.api.app import app
from src.backend.rag_pipeline.api.websocket import websocket_progress
from src.backend.rag_pipeline.utils.progress import ProgressEvent, progress_notifier


# Helper mock websocket for direct code testing
class MockWebSocket:
    def __init__(self):
        self.sent_texts = []
        self.sent_jsons = []
        self.received_texts = asyncio.Queue()
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, text):
        self.sent_texts.append(text)

    async def send_json(self, data):
        self.sent_jsons.append(data)

    async def receive_text(self):
        try:
            return await asyncio.wait_for(self.received_texts.get(), timeout=1)
        except TimeoutError as e:
            raise Exception("Timeout waiting for message") from e

    async def close(self):
        self.closed = True


# Test data
TEST_PDF = "2005.11401v4.pdf"
EXPECTED_PROGRESS_STEPS = [
    5,  # Initial upload complete
    10,  # File saved
    95,  # Processing complete
    100,  # Final completion
]


# --- Clean up pending asyncio tasks after each test (for test cleanliness) ---
@pytest.fixture(autouse=True)
def cancel_pending_asyncio_tasks():
    yield
    try:
        loop = asyncio.get_running_loop()
        for task in asyncio.all_tasks(loop):
            if not task.done() and task is not asyncio.current_task(loop):
                task.cancel()
    except RuntimeError:
        # No running event loop, nothing to clean up
        pass


# This prevents 'Task was destroyed but it is pending!' warnings in test output,
# and avoids errors if no event loop is running during teardown.


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_data_dir() -> Path:
    """Get the path to the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def progress_updates() -> list[dict[str, int]]:
    """Track progress updates during tests."""
    return []


@pytest.fixture
def websocket_client(test_client: TestClient) -> WebSocketTestSession:
    """Create a WebSocket client for testing progress updates."""
    with test_client.websocket_connect("/ws/upload-progress") as websocket:
        yield websocket


class TestWebSocket:
    """Test suite for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_websocket_progress_updates(self):
        """
        Functional requirement: The progress notifier must send progress updates to subscribers as document processing advances.
        This test simulates a websocket subscriber and verifies that all expected progress steps are sent as JSON messages.
        """
        progress_notifier._current_progress.clear()
        ws = MockWebSocket()
        # Simulate a subscriber
        subscribe_task = asyncio.create_task(websocket_progress(ws))
        await asyncio.sleep(0.05)  # Let the handler accept and subscribe
        # Simulate progress events
        for step in EXPECTED_PROGRESS_STEPS:
            event = ProgressEvent(TEST_PDF, step)
            await progress_notifier.notify(event)
            await asyncio.sleep(0.01)
        # Simulate client sending a message to trigger exit
        await ws.received_texts.put("exit")
        await asyncio.sleep(0.05)
        subscribe_task.cancel()
        # Check that all expected progress steps were sent
        sent_progress = [
            msg["progress"] for msg in ws.sent_jsons if msg.get("type") == "progress_update" and msg.get("file_id") == TEST_PDF
        ]
        for expected in EXPECTED_PROGRESS_STEPS:
            assert any(p >= expected for p in sent_progress), (
                f"Expected progress update for {expected}% not found in sent messages: {sent_progress}"
            )

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self):
        """
        Technical requirement: The websocket handler must respond with 'pong' when receiving a 'ping' message from the client.
        This test simulates a websocket client sending 'ping' and checks for the correct 'pong' response.
        """
        ws = MockWebSocket()
        task = asyncio.create_task(websocket_progress(ws))
        await asyncio.sleep(0.05)
        await ws.received_texts.put("ping")
        await asyncio.sleep(0.05)
        task.cancel()
        assert "pong" in ws.sent_texts, "WebSocket did not respond with 'pong' to 'ping'. Sent messages: " + str(ws.sent_texts)

    @pytest.mark.asyncio
    async def test_websocket_initial_state(self):
        """
        Functional requirement: When a new websocket subscriber connects, it must receive the current progress state for all active uploads.
        This test sets a progress state and verifies that the initial state is sent to the new subscriber.
        """
        progress_notifier._current_progress.clear()
        progress_notifier._current_progress["test.pdf"] = 50
        ws = MockWebSocket()
        task = asyncio.create_task(websocket_progress(ws))
        await asyncio.sleep(0.05)
        task.cancel()
        initial_state_msgs = [msg for msg in ws.sent_jsons if msg.get("type") == "initial_state"]
        assert initial_state_msgs, "No initial_state message sent to new subscriber. Sent messages: " + str(ws.sent_jsons)
        assert "test.pdf" in initial_state_msgs[0]["data"], "Expected 'test.pdf' not found in initial state data: " + str(
            initial_state_msgs[0]["data"]
        )
        assert initial_state_msgs[0]["data"]["test.pdf"] == 50, "Expected progress 50 not found for 'test.pdf'. Data: " + str(
            initial_state_msgs[0]["data"]
        )

    @pytest.mark.asyncio
    async def test_websocket_progress_edge_case_completion_cleanup(self):
        """
        Edge case: After a file reaches 100% progress, it should be cleaned up from the notifier's state after a delay.
        This test verifies that the cleanup occurs as expected.
        """
        progress_notifier._current_progress.clear()
        ws = MockWebSocket()
        task = asyncio.create_task(websocket_progress(ws))
        await asyncio.sleep(0.05)
        event = ProgressEvent("edgecase.pdf", 100)
        await progress_notifier.notify(event)
        await asyncio.sleep(0.1)
        assert "edgecase.pdf" in progress_notifier._current_progress, (
            "Expected 'edgecase.pdf' not found in current progress before cleanup"
        )
        await asyncio.sleep(5.1)  # Wait for cleanup delay
        assert "edgecase.pdf" not in progress_notifier._current_progress, (
            "Expected 'edgecase.pdf' to be cleaned up from current progress after delay"
        )
        task.cancel()
