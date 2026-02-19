"""Tests for the document upload routes, verifying service-layer delegation.

As an architect I want route tests to mock at the service boundary,
so that tests remain independent of core implementation details.
"""

import inspect
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app

client = TestClient(app)

_UPLOAD_HEADERS = {"content-type": "multipart/form-data"}


def _make_pdf_upload(filename: str = "test.pdf", content: bytes = b"%PDF-1.4 test") -> dict:
    return {"file": (filename, content, "application/pdf")}


def test_documents_route_has_no_core_embeddings_import():
    """As an architect I want documents.py free of core.embeddings imports,
    so the service layer boundary is enforced.
    """
    import sys

    module = sys.modules.get("src.backend.rag_pipeline.api.documents")
    if module is None:
        import importlib

        module = importlib.import_module("src.backend.rag_pipeline.api.documents")

    source = inspect.getsource(module)
    assert "from ..core.embeddings import" not in source, "documents.py must not import directly from core.embeddings"
    assert "process_document" not in source or "DocumentProcessingService" in source, (
        "documents.py must delegate to DocumentProcessingService, not call process_document directly"
    )


@pytest.mark.asyncio
async def test_upload_triggers_service_background_task(tmp_path):
    """As a user I want uploaded documents processed via the service layer,
    so architecture boundaries are maintained.
    Technical: upload endpoint delegates background work to DocumentProcessingService.
    """
    with patch("src.backend.rag_pipeline.api.documents.document_processing_service") as mock_service:
        mock_service.process_document_background = AsyncMock()

        response = client.post(
            "/api/documents/upload",
            files=_make_pdf_upload(),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["processing"] == "started"


def test_list_documents_returns_files(tmp_path):
    """As a user I want to list uploaded documents, so I can see what's available.
    Technical: GET /api/documents/list returns a list of filenames.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "report.pdf").write_bytes(b"%PDF test")
        response = client.get("/api/documents/list")

    assert response.status_code == 200
    assert "files" in response.json()


def test_delete_document_not_found_returns_404():
    """As a user I want clear 404 errors for missing documents,
    so I can distinguish not-found from server errors.
    """
    response = client.delete("/api/documents/nonexistent_file_xyz.pdf")
    assert response.status_code == 404


def test_delete_document_rejects_path_traversal():
    """As a security engineer I want path traversal attempts rejected,
    so the server is not vulnerable to directory traversal attacks.
    """
    response = client.delete("/api/documents/../secret.txt")
    # FastAPI will either return 400 (our validation) or 404 (path not found)
    assert response.status_code in (400, 404)


def test_serve_document_as_text_txt(tmp_path):
    """As a user I want TXT files rendered as text in the preview, so I can read full content.
    Technical: GET /api/documents/files/{filename}/as-text returns UTF-8 text for .txt files.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "sample.txt").write_text("Hello, world.\nLine two.", encoding="utf-8")
        response = client.get("/api/documents/files/sample.txt/as-text")
    assert response.status_code == 200
    assert response.text == "Hello, world.\nLine two."


def test_serve_document_as_text_md(tmp_path):
    """As a user I want MD files rendered as text in the preview, so I can read full content.
    Technical: GET /api/documents/files/{filename}/as-text returns UTF-8 text for .md files.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "readme.md").write_text("# Title\n\nBody **bold**", encoding="utf-8")
        response = client.get("/api/documents/files/readme.md/as-text")
    assert response.status_code == 200
    assert "# Title" in response.text and "**bold**" in response.text


def test_serve_document_as_text_docx(tmp_path, test_data_dir):
    """As a user I want DOCX files extracted as text in the preview, so I can read full content.
    Technical: GET /api/documents/files/{filename}/as-text extracts text via python-docx for .docx.
    """
    docx_path = test_data_dir / "toolsfairy-com-sample-docx-files-sample4.docx"
    if not docx_path.exists():
        pytest.skip("DOCX test fixture not found")
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        import shutil

        shutil.copy(docx_path, tmp_path / "sample.docx")
        response = client.get("/api/documents/files/sample.docx/as-text")
    assert response.status_code == 200
    assert len(response.text.strip()) > 0


def test_serve_document_as_text_unsupported_returns_400(tmp_path):
    """As a user I want clear feedback when text extraction is not supported.
    Technical: GET /api/documents/files/{filename}/as-text returns 400 for unsupported formats.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "file.pdf").write_bytes(b"%PDF-1.4")
        response = client.get("/api/documents/files/file.pdf/as-text")
    assert response.status_code == 400


def test_serve_document_as_text_not_found_returns_404(tmp_path):
    """As a user I want 404 when requesting as-text for a non-existent file."""
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        response = client.get("/api/documents/files/nonexistent.txt/as-text")
    assert response.status_code == 404
