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
    Validation: New documents return 201 with created: true; background processing started.
    """
    with (
        patch("src.backend.rag_pipeline.api.documents.document_processing_service") as mock_service,
        patch("src.backend.rag_pipeline.api.documents.vector_store_manager") as mock_vsm,
    ):
        mock_service.process_document_background = AsyncMock()
        mock_vsm.has_document_with_file_hash.return_value = False  # New document

        response = client.post(
            "/api/v1/documents",
            files=_make_pdf_upload(),
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["processing"] == "started"
    assert data["created"] is True


def test_list_documents_returns_files(tmp_path):
    """As a user I want to list uploaded documents, so I can see what's available.
    Technical: GET /api/v1/documents returns a list of filenames.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "report.pdf").write_bytes(b"%PDF test")
        response = client.get("/api/v1/documents")

    assert response.status_code == 200
    assert "files" in response.json()


@pytest.mark.asyncio
async def test_upload_duplicate_returns_200_created_false():
    """As a user I want duplicate uploads to be detected before processing,
    so I get an idempotent API and avoid redundant work.
    Technical: Content-hash deduplication returns 200 with created: false; no file saved, no processing.
    Validation: Mock has_document_with_file_hash=True; assert 200, created: false, no background task.
    """
    content = b"%PDF-1.4 duplicate-content"
    with (
        patch("src.backend.rag_pipeline.api.documents.vector_store_manager") as mock_vsm,
        patch("src.backend.rag_pipeline.api.documents.document_processing_service") as mock_service,
    ):
        mock_vsm.has_document_with_file_hash.return_value = True  # Duplicate
        mock_service.process_document_background = AsyncMock()

        response = client.post(
            "/api/v1/documents",
            files=_make_pdf_upload(content=content),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "duplicate"
    assert data["created"] is False
    mock_service.process_document_background.assert_not_called()


def test_delete_document_not_found_returns_404():
    """As a user I want clear 404 errors for missing documents,
    so I can distinguish not-found from server errors.
    """
    response = client.delete("/api/v1/documents/nonexistent_file_xyz.pdf")
    assert response.status_code == 404


def test_delete_document_rejects_path_traversal():
    """As a security engineer I want path traversal attempts rejected,
    so the server is not vulnerable to directory traversal attacks.
    """
    response = client.delete("/api/v1/documents/../secret.txt")
    # FastAPI will either return 400 (our validation) or 404 (path not found)
    assert response.status_code in (400, 404)


def test_serve_document_as_text_txt(tmp_path):
    """As a user I want TXT files rendered as text in the preview, so I can read full content.
    Technical: GET /api/v1/documents/{filename}/content?format=text returns UTF-8 text for .txt files.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "sample.txt").write_text("Hello, world.\nLine two.", encoding="utf-8")
        response = client.get("/api/v1/documents/sample.txt/content?format=text")
    assert response.status_code == 200
    assert response.text == "Hello, world.\nLine two."


def test_serve_document_as_text_md(tmp_path):
    """As a user I want MD files rendered as text in the preview, so I can read full content.
    Technical: GET /api/v1/documents/{filename}/content?format=text returns UTF-8 text for .md files.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "readme.md").write_text("# Title\n\nBody **bold**", encoding="utf-8")
        response = client.get("/api/v1/documents/readme.md/content?format=text")
    assert response.status_code == 200
    assert "# Title" in response.text and "**bold**" in response.text


def test_serve_document_as_text_docx(tmp_path, test_data_dir):
    """As a user I want DOCX files extracted as text in the preview, so I can read full content.
    Technical: GET /api/v1/documents/{filename}/content?format=text extracts text via python-docx for .docx.
    """
    docx_path = test_data_dir / "toolsfairy-com-sample-docx-files-sample4.docx"
    if not docx_path.exists():
        pytest.skip("DOCX test fixture not found")
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        import shutil

        shutil.copy(docx_path, tmp_path / "sample.docx")
        response = client.get("/api/v1/documents/sample.docx/content?format=text")
    assert response.status_code == 200
    assert len(response.text.strip()) > 0


def test_serve_document_as_text_unsupported_returns_400(tmp_path):
    """As a user I want clear feedback when text extraction is not supported.
    Technical: GET /api/v1/documents/{filename}/content?format=text returns 400 for unsupported formats.
    """
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        (tmp_path / "file.pdf").write_bytes(b"%PDF-1.4")
        response = client.get("/api/v1/documents/file.pdf/content?format=text")
    assert response.status_code == 400


def test_serve_document_as_text_not_found_returns_404(tmp_path):
    """As a user I want 404 when requesting as-text for a non-existent file."""
    with patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path):
        response = client.get("/api/v1/documents/nonexistent.txt/content?format=text")
    assert response.status_code == 404


def test_gdpr_article17_delete_cascades_filesystem_and_vector_store(tmp_path) -> None:
    """As a data subject, I want deletion to erase my document from all storage layers
    so that the right to erasure (GDPR Article 17) is honoured.

    Verifies:
    - File is removed from the filesystem (primary storage).
    - Vector store chunks are deleted (embedding storage).
    - Document no longer appears in the listing after deletion.
    """
    filename = "sensitive_report.pdf"
    (tmp_path / filename).write_bytes(b"%PDF-1.4 sensitive content")

    with (
        patch("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path),
        patch("src.backend.rag_pipeline.api.documents.vector_store_manager") as mock_vsm,
    ):
        mock_vsm.delete_by_document_name.return_value = 5  # 5 chunks deleted

        # File must be present before deletion
        list_before = client.get("/api/v1/documents").json()["files"]
        assert filename in list_before, "File must appear in listing before deletion"

        # Delete triggers cascade
        delete_resp = client.delete(f"/api/v1/documents/{filename}")
        assert delete_resp.status_code == 204, f"Expected 204 No Content, got {delete_resp.status_code}"

        # Vector store chunks must have been deleted
        mock_vsm.delete_by_document_name.assert_called_once_with(filename)

        # File must be gone from the filesystem
        assert not (tmp_path / filename).exists(), "File must be removed from filesystem on deletion"

        # File must be absent from the listing
        list_after = client.get("/api/v1/documents").json()["files"]
        assert filename not in list_after, "Deleted document must not appear in listing"
