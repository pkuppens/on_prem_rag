"""Edge-case tests for query service modules to close coverage gaps."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.query_service.api.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health API — deep component exceptions
# ---------------------------------------------------------------------------


def _mock_llm_config():
    cfg = MagicMock()
    cfg.backend_model_pair = "test-backend"
    return cfg


def test_health_v1_deep_database_error():
    with patch("backend.query_service.api.health.get_vector_store_manager", side_effect=RuntimeError("db down")):
        response = client.get("/api/v1/health?deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["database"]["status"] == "error"
    assert data["status"] == "degraded"


def test_health_v1_deep_llm_exception():
    with (
        patch("backend.query_service.api.health.get_vector_store_manager"),
        patch("backend.query_service.api.health.get_llm_config", _mock_llm_config),
        patch("backend.query_service.api.health.get_llm_provider_from_env", side_effect=RuntimeError("llm down")),
    ):
        response = client.get("/api/v1/health?deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["llm"]["status"] == "error"


def test_health_v1_deep_vector_store_error():
    call_count = 0

    def vsm_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock()
        raise RuntimeError("vector down")

    with (
        patch("backend.query_service.api.health.get_vector_store_manager", side_effect=vsm_side_effect),
        patch("backend.query_service.api.health.get_llm_config", _mock_llm_config),
        patch("backend.query_service.api.health.get_llm_provider_from_env") as mock_provider,
    ):
        mock_llm = mock_provider.return_value
        mock_llm.health_check = AsyncMock(return_value=True)
        response = client.get("/api/v1/health?deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["vector"]["status"] == "error"


def test_health_llm_config_error():
    with patch("backend.query_service.api.health.get_llm_config", side_effect=ValueError("bad config")):
        response = client.get("/api/v1/health/llm")
    assert response.status_code == 503
    assert "config error" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Metrics — index chunk count failure
# ---------------------------------------------------------------------------


def test_metrics_index_chunk_failure():
    with patch("backend.retrieval.infrastructure.vector_store_config.VectorStoreConfig", side_effect=RuntimeError("fail")):
        response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["index_chunks"] == 0


# ---------------------------------------------------------------------------
# Query routes — conversation endpoint error
# ---------------------------------------------------------------------------


def test_process_conversation_endpoint_error():
    with patch("backend.rag_pipeline.main.process_medical_conversation", side_effect=RuntimeError("processing failed")):
        response = client.post("/api/v1/retrieval/conversations", json={"text": "test conversation"})
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Chat API — ValueError path
# ---------------------------------------------------------------------------


def test_chat_get_llm_config_value_error():
    with patch("backend.query_service.api.chat.get_llm_config", side_effect=ValueError("bad config")):
        response = client.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "test"}]})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Chat stream — direct with history, NotImplementedError fallback
# ---------------------------------------------------------------------------


def test_chat_stream_direct_implemented():
    with patch("backend.query_service.api.chat.orchestrator", autospec=False) as mock_orch:
        mock_orch.generate_answer_stream.return_value = iter(["token1", "token2"])
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [
                    {"role": "user", "content": "previous question"},
                    {"role": "assistant", "content": "previous answer"},
                    {"role": "user", "content": "direct test"},
                ],
                "direct": True,
            },
        )
    assert response.status_code == 200
    content = response.text
    assert "token1" in content
    assert "token2" in content


def test_chat_stream_direct_not_implemented():
    with (
        patch("backend.query_service.api.chat.orchestrator", autospec=False) as mock_orch,
        patch("backend.query_service.api.chat.get_llm_config", return_value=MagicMock(backend_model_pair="test")),
    ):
        mock_orch.generate_answer_stream.side_effect = NotImplementedError
        mock_orch._llm.generate.return_value = "fallback answer"
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "stream test"}],
                "direct": True,
            },
        )
    assert response.status_code == 200
    content = response.text
    assert "fallback answer" in content


# ---------------------------------------------------------------------------
# Chat stream — non-direct with chunks, NotImplementedError fallback
# ---------------------------------------------------------------------------


def test_chat_stream_no_chunks_non_direct():
    with patch("backend.query_service.api.chat.orchestrator", autospec=False) as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = []
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "no chunks test"}],
            },
        )
    assert response.status_code == 200
    content = response.text
    assert "couldn't find relevant information" in content


def test_chat_stream_with_chunks_and_streaming():
    mock_chunks = [
        {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.68, "text": "short text"},
    ]
    with patch("backend.query_service.api.chat.orchestrator", autospec=False) as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = mock_chunks
        mock_orch.generate_answer_stream.return_value = iter(["hello ", "world"])
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "test question"}],
            },
        )
    assert response.status_code == 200
    content = response.text
    assert "hello " in content
    assert "world" in content


def test_chat_stream_with_chunks_long_text():
    mock_chunks = [
        {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.95, "text": "A" * 300},
    ]
    with patch("backend.query_service.api.chat.orchestrator", autospec=False) as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = mock_chunks
        mock_orch.generate_answer_stream.return_value = iter(["answer"])
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "test question"}],
            },
        )
    assert response.status_code == 200
    content = response.text
    assert "answer" in content
    assert "..." in content


def test_chat_stream_not_implemented_non_direct():
    mock_chunks = [
        {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.85, "text": "content"},
    ]
    with patch("backend.query_service.api.chat.orchestrator", autospec=False) as mock_orch:
        mock_orch.retrieve_relevant_chunks.return_value = mock_chunks
        mock_orch.generate_answer_stream.side_effect = NotImplementedError
        mock_orch.generate_answer.return_value = "fallback answer"
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "test question"}],
            },
        )
    assert response.status_code == 200
    content = response.text
    assert "fallback answer" in content


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_websocket_string_ping():
    with (
        patch("backend.query_service.api.websocket.progress_notifier") as mock_notifier,
    ):
        mock_notifier.subscribe = AsyncMock()
        mock_notifier.unsubscribe = AsyncMock()
        with client.websocket_connect("/ws/upload-progress") as ws:
            ws.send_text("ping")
            response = ws.receive_text()
    assert response == "pong"


@pytest.mark.asyncio
async def test_websocket_json_ping():
    with (
        patch("backend.query_service.api.websocket.progress_notifier") as mock_notifier,
    ):
        mock_notifier.subscribe = AsyncMock()
        mock_notifier.unsubscribe = AsyncMock()
        with client.websocket_connect("/ws/upload-progress") as ws:
            ws.send_text(json.dumps({"type": "ping", "timestamp": 123456}))
            response = ws.receive_text()
    data = json.loads(response)
    assert data["type"] == "pong"
    assert data["timestamp"] == 123456


@pytest.mark.asyncio
async def test_websocket_pong_then_ping():
    with (
        patch("backend.query_service.api.websocket.progress_notifier") as mock_notifier,
    ):
        mock_notifier.subscribe = AsyncMock()
        mock_notifier.unsubscribe = AsyncMock()
        with client.websocket_connect("/ws/upload-progress") as ws:
            ws.send_text(json.dumps({"type": "pong"}))
            ws.send_text(json.dumps({"type": "ping"}))
            response = ws.receive_text()
    data = json.loads(response)
    assert data["type"] == "pong"


@pytest.mark.asyncio
async def test_websocket_unknown_json_message():
    with (
        patch("backend.query_service.api.websocket.progress_notifier") as mock_notifier,
    ):
        mock_notifier.subscribe = AsyncMock()
        mock_notifier.unsubscribe = AsyncMock()
        with client.websocket_connect("/ws/upload-progress") as ws:
            ws.send_text(json.dumps({"type": "unknown"}))
            ws.send_text(json.dumps({"type": "ping"}))
            response = ws.receive_text()
    assert json.loads(response)["type"] == "pong"


@pytest.mark.asyncio
async def test_websocket_non_json_message():
    with (
        patch("backend.query_service.api.websocket.progress_notifier") as mock_notifier,
    ):
        mock_notifier.subscribe = AsyncMock()
        mock_notifier.unsubscribe = AsyncMock()
        with client.websocket_connect("/ws/upload-progress") as ws:
            ws.send_text("not json")
            ws.send_text("ping")
            response = ws.receive_text()
    assert response == "pong"


@pytest.mark.asyncio
async def test_websocket_subscribe_error():
    with (
        patch("backend.query_service.api.websocket.progress_notifier") as mock_notifier,
    ):
        mock_notifier.subscribe = AsyncMock(side_effect=RuntimeError("subscribe failed"))
        mock_notifier.unsubscribe = AsyncMock()
        with client.websocket_connect("/ws/upload-progress") as ws:
            ws.send_text("ping")
    # Expect no exception — outer except catches the error and logs it


# Lines 60-61 (websocket close error handler) remain uncovered:
# they require the websocket's close() to raise, which is timing-dependent
# in the test client and not reliably reproducible.


# ---------------------------------------------------------------------------
# Chat stream — empty content
# ---------------------------------------------------------------------------


def test_chat_stream_empty_content():
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "messages": [{"role": "user", "content": ""}],
        },
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Main — start_server
# ---------------------------------------------------------------------------


def test_start_server():
    with patch("uvicorn.run") as mock_run:
        from backend.query_service.main import start_server

        start_server()
    mock_run.assert_called_once()
