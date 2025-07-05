"""Tests for query API routes in the RAG pipeline."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app

client = TestClient(app)


def test_process_conversation_endpoint():
    """Test the /api/query/process_conversation endpoint."""
    with patch("src.backend.rag_pipeline.api.query.process_medical_conversation") as mock_process:
        mock_process.return_value = {"result": "mocked_result"}
        response = client.post("/api/query/process_conversation", json={"text": "test conversation"})
        assert response.status_code == 200
        assert response.json() == {"result": {"result": "mocked_result"}}
        mock_process.assert_called_once_with("test conversation")


def test_process_conversation_endpoint_empty_text():
    """Test the /api/query/process_conversation endpoint with empty text."""
    response = client.post("/api/query/process_conversation", json={"text": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Text must not be empty"}
