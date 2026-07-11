"""Tests for metrics and parameter API endpoints."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.query_service.api.app import app

client = TestClient(app)


class TestMetricsEndpoint:
    def test_get_metrics(self):
        with patch("backend.query_service.api.metrics._get_index_chunk_count", return_value=42):
            response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["documents_ingested"], int)
        assert isinstance(data["queries_total"], int)
        assert data["index_chunks"] == 42
        assert isinstance(data["last_ingestion_timestamp_ms"], (int, float))


class TestParametersEndpoint:
    def test_get_parameter_sets(self):
        response = client.get("/api/v1/parameter-sets")
        assert response.status_code == 200
        data = response.json()
        assert "default" in data
        assert "sets" in data
        assert isinstance(data["sets"], dict)
