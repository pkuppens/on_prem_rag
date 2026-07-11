"""Tests for Query Service health API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.query_service.api.app import app

client = TestClient(app)


def test_health_basic():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_v1_shallow():
    response = client.get("/api/v1/health?deep=false")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _mock_llm_config():
    cfg = MagicMock()
    cfg.backend_model_pair = "test-backend"
    return cfg


def test_health_v1_deep_all_ok():
    with (
        patch("backend.query_service.api.health.get_vector_store_manager"),
        patch("backend.query_service.api.health.get_llm_config", _mock_llm_config),
        patch("backend.query_service.api.health.get_llm_provider_from_env") as mock_provider,
    ):
        mock_llm = mock_provider.return_value
        mock_llm.health_check = AsyncMock(return_value=True)
        response = client.get("/api/v1/health?deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["llm"]["status"] == "ok"
    assert data["components"]["database"]["status"] == "ok"


def test_health_v1_deep_llm_error():
    with (
        patch("backend.query_service.api.health.get_vector_store_manager"),
        patch("backend.query_service.api.health.get_llm_config", _mock_llm_config),
        patch("backend.query_service.api.health.get_llm_provider_from_env") as mock_provider,
    ):
        mock_llm = mock_provider.return_value
        mock_llm.health_check = AsyncMock(return_value=False)
        response = client.get("/api/v1/health?deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["llm"]["status"] == "error"


def test_health_database_ok():
    with patch("backend.query_service.api.health.get_vector_store_manager"):
        response = client.get("/api/v1/health/database")
    assert response.status_code == 200


def test_health_database_error():
    with patch("backend.query_service.api.health.get_vector_store_manager", side_effect=RuntimeError("db down")):
        response = client.get("/api/v1/health/database")
    assert response.status_code == 503


def test_health_llm_ok():
    with (
        patch("backend.query_service.api.health.get_llm_config", _mock_llm_config),
        patch("backend.query_service.api.health.get_llm_provider_from_env") as mock_provider,
    ):
        mock_llm = mock_provider.return_value
        mock_llm.health_check = AsyncMock(return_value=True)
        response = client.get("/api/v1/health/llm")
    assert response.status_code == 200


def test_health_llm_unhealthy():
    with (
        patch("backend.query_service.api.health.get_llm_config", _mock_llm_config),
        patch("backend.query_service.api.health.get_llm_provider_from_env") as mock_provider,
    ):
        mock_llm = mock_provider.return_value
        mock_llm.health_check = AsyncMock(return_value=False)
        response = client.get("/api/v1/health/llm")
    assert response.status_code == 503


def test_health_vector_ok():
    with patch("backend.query_service.api.health.get_vector_store_manager"):
        response = client.get("/api/v1/health/vector")
    assert response.status_code == 200


def test_health_vector_error():
    with patch("backend.query_service.api.health.get_vector_store_manager", side_effect=RuntimeError("vector down")):
        response = client.get("/api/v1/health/vector")
    assert response.status_code == 503


def test_health_auth():
    response = client.get("/api/v1/health/auth")
    assert response.status_code == 200


def test_health_websocket():
    response = client.get("/api/v1/health/websocket")
    assert response.status_code == 200
