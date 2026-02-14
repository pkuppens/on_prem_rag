"""Tests for API routes in the RAG pipeline.

This module tests the various API endpoints and their functionality.
"""

from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test the health check endpoint."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_correlation_id_in_response() -> None:
    """As a user I want correlation IDs in responses for tracing.
    Technical: All responses include X-Correlation-ID header.
    """
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert "X-Correlation-ID" in resp.headers


def test_metrics_endpoint() -> None:
    """As a user I want metrics for observability, so I can monitor pipeline usage.
    Technical: GET /metrics returns documents_ingested, queries_total, index_chunks.
    """
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "documents_ingested" in data
    assert "queries_total" in data
    assert "index_chunks" in data
    assert "last_ingestion_timestamp_ms" in data
    assert isinstance(data["documents_ingested"], int)
    assert isinstance(data["queries_total"], int)


def test_documents_list(tmp_path, monkeypatch) -> None:
    """Test the document listing endpoint."""
    file_path = tmp_path / "example.txt"
    file_path.write_text("data")
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path)
    resp = client.get("/api/documents/list")
    assert resp.status_code == 200
    assert resp.json()["files"] == ["example.txt"]


def test_documents_delete_success(tmp_path, monkeypatch) -> None:
    """As a user I want to delete uploaded documents, so I can free storage and remove sensitive data.
    Technical: DELETE /api/documents/{filename} removes file and vector chunks.
    Validation: 204 on success, file gone from list.
    """
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path)
    file_path = tmp_path / "to_delete.txt"
    file_path.write_text("content")
    mock_vsm = type("MockVSM", (), {"delete_by_document_name": lambda self, n: 3})()
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.vector_store_manager", mock_vsm)

    resp = client.delete("/api/documents/to_delete.txt")
    assert resp.status_code == 204
    assert not file_path.exists()
    list_resp = client.get("/api/documents/list")
    assert "to_delete.txt" not in list_resp.json()["files"]


def test_documents_delete_not_found(tmp_path, monkeypatch) -> None:
    """As a user I want clear feedback when deleting non-existent documents.
    Technical: DELETE returns 404 when document does not exist.
    """
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path)
    resp = client.delete("/api/documents/nonexistent.pdf")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_error_responses_follow_rfc7807(tmp_path, monkeypatch) -> None:
    """As a user I want structured error responses, so I can handle failures programmatically.
    Technical: HTTPException and validation errors return application/problem+json.
    """
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path)
    resp = client.delete("/api/documents/nonexistent.pdf")
    assert resp.status_code == 404
    assert resp.headers.get("content-type", "").startswith("application/problem+json")
    data = resp.json()
    assert "type" in data
    assert "title" in data
    assert data["status"] == 404
    assert "detail" in data
    assert "instance" in data


def test_chat_endpoint_accepts_messages(monkeypatch) -> None:
    """As a user I want a chat endpoint with message history, so I can have multi-turn conversations.
    Technical: POST /api/chat accepts messages list and returns answer with sources.
    Validation: Mock QA system; verify request/response contract.
    """
    mock_chunks = [{"text": "Test content", "document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.9}]

    def mock_retrieve(*args, **kwargs):
        return mock_chunks

    def mock_generate(question, chunks, conversation_history=None):
        return "Mocked answer"

    monkeypatch.setattr("src.backend.rag_pipeline.api.chat.qa_system.retrieve_relevant_chunks", mock_retrieve)
    monkeypatch.setattr("src.backend.rag_pipeline.api.chat.qa_system.generate_answer", mock_generate)

    resp = client.post(
        "/api/chat",
        json={
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Follow-up question"},
            ],
            "top_k": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Mocked answer"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_name"] == "doc.pdf"


def test_chat_requires_last_message_from_user() -> None:
    """As a user I want validation that last message is from user.
    Technical: POST /api/chat returns 400 if last message is not from user.
    """
    resp = client.post(
        "/api/chat",
        json={"messages": [{"role": "assistant", "content": "Previous answer"}]},
    )
    assert resp.status_code == 400


def test_documents_delete_rejects_invalid_filename(tmp_path, monkeypatch) -> None:
    """As a user I want the API to reject invalid filenames with .. in the name.
    Technical: Filenames with .. return 400 for path traversal prevention.
    """
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path)
    resp = client.delete("/api/documents/bad..name.pdf")  # contains ..
    assert resp.status_code == 400
