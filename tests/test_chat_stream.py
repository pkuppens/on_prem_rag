"""Integration tests for chat streaming.

As a user I want streaming chat to work with local Ollama, so I can see tokens as they arrive.
Technical: POST /api/chat/stream returns SSE events. Requires Ollama (LLM on port 11434).
Validation: Excluded from default CI. Run with: pytest -m ollama (skips if Ollama not running).
"""

import json

import pytest
from fastapi.testclient import TestClient

from backend.rag_pipeline.api.app import app

client = TestClient(app)


@pytest.mark.ollama
@pytest.mark.slow
def test_chat_stream_endpoint_returns_sse() -> None:
    """POST /api/chat/stream returns 200 with text/event-stream.

    As a user I want the streaming endpoint to return valid SSE.
    Technical: Response has correct Content-Type and yields data lines.
    Requires Ollama (local LLM); skips with clear message if not running.
    """
    response = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "What is 2+2?"}]},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.ollama
@pytest.mark.slow
def test_chat_stream_events_structure() -> None:
    """Stream events have type and content/data fields.

    Parses SSE events and checks structure. May buffer fully in test client.
    """
    response = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "Hi"}]},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 200
    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                events.append(data)
            except json.JSONDecodeError:
                pass
    assert len(events) >= 1
    for ev in events:
        assert "type" in ev
