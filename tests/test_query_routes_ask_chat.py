"""Tests for Query Service ask and chat API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.query_service.api.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /api/v1/qa — ask endpoint
# ---------------------------------------------------------------------------


def test_ask_question_empty_question():
    response = client.post("/api/v1/qa", json={"question": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.parametrize("strategy", ["dense", "sparse", "hybrid", "bm25", None])
def test_ask_question_valid_strategies(strategy):
    payload = {"question": "test question"}
    if strategy is not None:
        payload["strategy"] = strategy
    with patch.object(client.app, "state", create=True), \
         patch("backend.query_service.api.ask.orchestrator") as mock_orch:
        mock_orch.ask_question.return_value = {
            "answer": "test answer",
            "sources": [],
            "confidence": "high",
            "chunks_retrieved": 3,
            "average_similarity": 0.85,
        }
        response = client.post("/api/v1/qa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "test answer"
    assert data["confidence"] == "high"


def test_ask_question_invalid_strategy():
    response = client.post("/api/v1/qa", json={"question": "test", "strategy": "invalid"})
    assert response.status_code == 422


def test_ask_question_orchestrator_value_error():
    with patch("backend.query_service.api.ask.orchestrator") as mock_orch:
        mock_orch.ask_question.side_effect = ValueError("bad request")
        response = client.post("/api/v1/qa", json={"question": "test question"})
    assert response.status_code == 400


def test_ask_question_orchestrator_runtime_error():
    with patch("backend.query_service.api.ask.orchestrator") as mock_orch:
        mock_orch.ask_question.side_effect = RuntimeError("something broke")
        response = client.post("/api/v1/qa", json={"question": "test question"})
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# /api/v1/chat — chat endpoint
# ---------------------------------------------------------------------------


def test_chat_empty_messages():
    response = client.post("/api/v1/chat", json={"messages": []})
    assert response.status_code == 422


def test_chat_last_message_not_user():
    response = client.post("/api/v1/chat", json={"messages": [{"role": "assistant", "content": "hello"}]})
    assert response.status_code == 400


def test_chat_empty_last_message():
    response = client.post("/api/v1/chat", json={"messages": [{"role": "user", "content": ""}]})
    assert response.status_code == 400


def test_chat_success():
    with patch("backend.query_service.api.chat.orchestrator") as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = [
            {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.85, "text": "relevant content"}
        ]
        mock_orch.generate_answer.return_value = "Here is the answer"
        response = client.post("/api/v1/chat", json={
            "messages": [{"role": "user", "content": "test question"}],
        })
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Here is the answer"
    assert data["confidence"] == "high"


def test_chat_no_chunks():
    with patch("backend.query_service.api.chat.orchestrator") as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = []
        response = client.post("/api/v1/chat", json={
            "messages": [{"role": "user", "content": "test question"}],
        })
    assert response.status_code == 200
    assert "couldn't find relevant information" in response.json()["answer"].lower()


def test_chat_high_confidence():
    with patch("backend.query_service.api.chat.orchestrator") as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = [
            {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.95, "text": "content"},
            {"document_name": "doc2.pdf", "page_number": 2, "similarity_score": 0.90, "text": "more content"},
        ]
        mock_orch.generate_answer.return_value = "High confidence answer"
        response = client.post("/api/v1/chat", json={
            "messages": [{"role": "user", "content": "test question"}],
        })
    data = response.json()
    assert data["confidence"] == "high"


def test_chat_error():
    with patch("backend.query_service.api.chat.orchestrator") as mock_orch:
        mock_orch.retrieve_relevant_chunks.side_effect = RuntimeError("retrieval failed")
        response = client.post("/api/v1/chat", json={
            "messages": [{"role": "user", "content": "test question"}],
        })
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# /api/v1/chat/stream — streaming chat endpoint
# ---------------------------------------------------------------------------


def test_chat_stream_empty_messages():
    response = client.post("/api/v1/chat/stream", json={"messages": []})
    assert response.status_code == 422


def test_chat_stream_last_message_not_user():
    response = client.post("/api/v1/chat/stream", json={"messages": [{"role": "assistant", "content": "hello"}]})
    assert response.status_code == 400


def test_chat_stream_direct():
    with patch("backend.query_service.api.chat.orchestrator.retrieve_relevant_chunks") as mock_ret:
        mock_ret.return_value = [{"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.85, "text": "content"}]
        response = client.post("/api/v1/chat/stream", json={
            "messages": [{"role": "user", "content": "stream test"}],
            "direct": True,
        })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
