"""Tests for query API routes in the RAG pipeline."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app

client = TestClient(app)


def test_query_documents_delegates_to_query_service():
    """As a user I want to query documents, so I can find relevant chunks.
    Technical: route delegates to QueryService, not core.embeddings directly.
    """
    mock_results = {"results": [{"text": "chunk1", "score": 0.9}]}
    with patch("src.backend.rag_pipeline.api.query.query_service") as mock_service:
        mock_service.query.return_value = mock_results
        response = client.post("/api/query", json={"query": "test query"})
    assert response.status_code == 200
    assert response.json() == mock_results
    mock_service.query.assert_called_once()


def test_query_documents_empty_query_returns_400():
    """As a user I want clear validation errors, so I know when my query is invalid.
    Technical: empty query string returns 400.
    """
    response = client.post("/api/query", json={"query": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Query must not be empty"


def test_query_service_error_returns_500():
    """As a user I want proper error responses, so I can handle failures gracefully.
    Technical: QueryService exception propagates as 500.
    """
    with patch("src.backend.rag_pipeline.api.query.query_service") as mock_service:
        mock_service.query.side_effect = RuntimeError("vector store unavailable")
        response = client.post("/api/query", json={"query": "test query"})
    assert response.status_code == 500


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
    data = response.json()
    assert data.get("detail") == "Text must not be empty"
    assert data.get("status") == 400


def test_query_route_has_no_core_imports():
    """As an architect I want routes to be free of core imports, so the layer boundary is enforced.
    Technical: api.query module must not import from core.embeddings.
    """
    import importlib
    import sys

    # Reload to get a fresh module reference
    module_name = "src.backend.rag_pipeline.api.query"
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        module = importlib.import_module(module_name)

    import inspect

    source = inspect.getsource(module)
    assert "from ..core.embeddings import" not in source, "query.py must not import directly from core.embeddings"
    assert "query_embeddings" not in source, "query.py must not reference query_embeddings directly"


def test_query_service_receives_correct_top_k():
    """As a user I want top_k to be respected, so I control the number of results.
    Technical: custom top_k in request is forwarded to QueryService.query.
    """
    mock_service = MagicMock()
    mock_service.query.return_value = {"results": []}
    with patch("src.backend.rag_pipeline.api.query.query_service", mock_service):
        response = client.post("/api/query", json={"query": "test", "top_k": 3})
    assert response.status_code == 200
    call_kwargs = mock_service.query.call_args
    # top_k is the third positional arg
    assert call_kwargs.args[2] == 3
