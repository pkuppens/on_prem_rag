"""Document management API endpoints for the Query Service.

Same URL paths as the original rag_pipeline/api/documents.py for backward compatibility.
"""

import asyncio
import hashlib
import os
import re
from pathlib import Path
from typing import Annotated, List
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field, HttpUrl
from starlette.datastructures import UploadFile as StarletteUploadFile

from backend.ingestion.infrastructure.vector_store import get_vector_store_write
from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME, RAGParams, get_param_set
from backend.rag_pipeline.models.document_models import ProcessingStatus, UploadResponse
from backend.rag_pipeline.services.document_processing_service import DocumentProcessingService
from backend.rag_pipeline.services.file_upload_service import FileUploadService
from backend.rag_pipeline.utils.docx_utils import extract_and_clean_docx
from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.rag_pipeline.utils.progress import ProgressEvent, progress_notifier
from backend.shared.utils.directory_utils import (
    _format_path_for_error,
    ensure_directory_exists,
    get_uploaded_files_dir,
)

from .metrics import get_metrics

logger = StructuredLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Initialize directories and services
uploaded_files_dir = get_uploaded_files_dir()
ensure_directory_exists(uploaded_files_dir)
vector_store_manager = get_vector_store_write()
document_processing_service = DocumentProcessingService()
file_upload_service = FileUploadService()


async def process_document_background(file_path, filename: str, params_name: str) -> None:
    """Delegate background document processing to DocumentProcessingService."""
    await document_processing_service.process_document_background(file_path, filename, params_name)
    get_metrics().record_ingestion()


@router.get("")
async def list_documents() -> dict[str, list[str]]:
    """Return a list of uploaded document filenames."""
    logger.info("GET /api/v1/documents")
    files = [f.name for f in uploaded_files_dir.iterdir() if f.is_file()]
    return {"files": files}


class DocumentFromUrlRequest(BaseModel):
    """Request to ingest a document from a URL."""

    url: HttpUrl = Field(..., description="URL of the document to download (http/https only)")
    params_name: str = Field(default=DEFAULT_PARAM_SET_NAME, description="Parameter set for processing")


@router.post("/ingest-from-url")
async def upload_document_from_url(payload: DocumentFromUrlRequest, background_tasks: BackgroundTasks) -> dict:
    """Download a document from a URL and process it for RAG."""
    url_str = str(payload.url)
    logger.info("POST /api/v1/documents/ingest-from-url", url=url_str, params_name=payload.params_name)

    parsed = urlparse(url_str)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail=f"URL scheme must be http or https, got: {parsed.scheme}")

    params = get_param_set(payload.params_name)
    if not isinstance(params, RAGParams):
        raise HTTPException(status_code=400, detail=f"Invalid parameter set: {payload.params_name}")

    supported_extensions = {".pdf", ".txt", ".md", ".docx", ".doc", ".csv", ".json"}
    path_from_url = Path(parsed.path)
    ext = path_from_url.suffix.lower() if path_from_url.suffix else ""

    if ext not in supported_extensions:
        ext = ".pdf"

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url_str)
            response.raise_for_status()
            content = response.content
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Document size exceeds 50MB limit")

            cd = response.headers.get("content-disposition")
            if cd and "filename=" in cd:
                match = re.search(r'filename[*]?=(?:"([^"]+)"|\'([^\']+)\'|([^;\s]+))', cd, re.I)
                if match:
                    filename = (match.group(1) or match.group(2) or match.group(3) or "").strip()
            else:
                filename = path_from_url.name or f"document{ext}"

            filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
            if not filename:
                filename = f"document{ext}"

            file_path = uploaded_files_dir / filename
            file_path.write_bytes(content)

        await progress_notifier.notify(ProgressEvent(filename, 10, "Download completed"))
        background_tasks.add_task(process_document_background, file_path, filename, payload.params_name)

        return {
            "message": "Document downloaded and processing started",
            "file_id": filename,
            "status": "downloaded",
            "processing": "started",
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Failed to download: {e.response.status_code} - {str(e)}") from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Download request failed: {str(e)}") from e


async def sync_upload_single_file(file: UploadFile, background_tasks: BackgroundTasks, params_name: str) -> JSONResponse:
    """Handle single-file sync upload: save, dedupe, queue background processing."""
    logger.info("POST /api/v1/documents", filename=file.filename, size=file.size, content_type=file.content_type, async_mode=False)

    params = get_param_set(params_name)
    if not isinstance(params, RAGParams):
        raise HTTPException(status_code=400, detail="Invalid parameter set name")

    if not (filename := file.filename):
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file.size or file.size == 0:
        raise HTTPException(status_code=400, detail="File cannot be empty")

    supported_types = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/csv",
        "application/json",
    ]

    if (content_type := file.content_type) not in supported_types:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {content_type}. Supported types: {', '.join(supported_types)}"
        )

    try:
        await progress_notifier.notify(ProgressEvent(filename, 5, "Upload started"))
        file_path = uploaded_files_dir / filename
        file_content = await file.read()
        file_content_hash = hashlib.sha256(file_content).hexdigest()
        embedding_model = params.embedding.model_name

        if vector_store_manager.has_document_with_file_hash(file_content_hash, embedding_model=embedding_model):
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Document already exists (duplicate content); not re-processed",
                    "file_id": filename,
                    "status": "duplicate",
                    "created": False,
                },
            )

        with open(file_path, "wb") as f:
            f.write(file_content)

        await progress_notifier.notify(ProgressEvent(filename, 10, "File saved"))
        await asyncio.sleep(0.1)
        background_tasks.add_task(process_document_background, file_path, filename, params_name)

        return JSONResponse(
            status_code=201,
            content={
                "message": "Document uploaded successfully, processing started",
                "file_id": filename,
                "status": "uploaded",
                "processing": "started",
                "created": True,
            },
        )

    except PermissionError as e:
        logger.error("Upload directory not writable.", error=str(e))
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {str(e)}"))
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "remediation": (
                    "Docker: use uploaded-files-data volume and entrypoint that chowns the directory. "
                    "Local: ensure UPLOADED_FILES_DIR exists and is writable."
                ),
            },
        ) from e
    except OSError as e:
        logger.error("File system error during upload", filename=filename, error=str(e))
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {str(e)}"))
        raise HTTPException(status_code=500, detail={"error": str(e), "remediation": "Check backend logs."}) from e
    except Exception as e:
        error_msg = str(e)
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {error_msg}"))
        detail: str | dict = error_msg
        if os.getenv("ENVIRONMENT") == "development":
            import traceback

            detail = {"error": error_msg, "traceback": traceback.format_exc()}
        raise HTTPException(status_code=500, detail=detail) from e


async def process_async_task_documents(task_id: str, params_name: str) -> None:
    """Run multi-file processing for an async upload task."""
    try:
        file_upload_service.update_processing_status(task_id, "processing", 0.0, "Starting document processing")
        task_dir = file_upload_service.upload_dir / task_id
        if not task_dir.exists():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")

        file_paths = [f for f in task_dir.iterdir() if f.is_file()]
        if not file_paths:
            raise ValueError("No files found in task directory")

        results = await document_processing_service.process_documents(task_id, file_paths, params_name)

        if results["failed_files"] == 0:
            file_upload_service.update_processing_status(
                task_id, "completed", 1.0, f"Processing completed: {results['processed_files']} files processed"
            )
        else:
            file_upload_service.update_processing_status(
                task_id,
                "completed_with_errors",
                1.0,
                f"Processing completed with errors: {results['processed_files']} successful, {results['failed_files']} failed",
            )
    except Exception as e:
        file_upload_service.update_processing_status(task_id, "error", -1.0, f"Processing failed: {str(e)}")


@router.post("", response_model=None)
async def create_document(
    request: Request,
    background_tasks: BackgroundTasks,
    async_q: Annotated[bool, Query(alias="async")] = False,
    params_name: Annotated[str, Query()] = DEFAULT_PARAM_SET_NAME,
) -> JSONResponse | UploadResponse:
    """Create document(s): sync multipart field `file`, or async with `async=true`."""
    form = await request.form()

    if async_q:
        raw_files = form.getlist("files")
        files: List[UploadFile] = [f for f in raw_files if isinstance(f, StarletteUploadFile)]
        if not files:
            raise HTTPException(status_code=400, detail="Multipart field 'files' is required when async=true")
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")

        try:
            upload_result = await file_upload_service.upload_multiple_files(files)
            if upload_result.accepted_count > 0:
                background_tasks.add_task(process_async_task_documents, upload_result.task_id, params_name)
            return upload_result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e

    single = form.get("file")
    if not isinstance(single, StarletteUploadFile):
        raise HTTPException(status_code=400, detail="Multipart field 'file' is required when async=false (default)")

    return await sync_upload_single_file(single, background_tasks, params_name)


@router.get("/tasks/{task_id}", response_model=ProcessingStatus)
async def get_processing_status(task_id: str) -> ProcessingStatus:
    """Return async upload task status."""
    status = file_upload_service.get_processing_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return status


@router.delete("/tasks/{task_id}", status_code=204)
async def cleanup_task(task_id: str) -> Response:
    """Remove task workspace after completed or failed processing."""
    status = file_upload_service.get_processing_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    if status.status not in ("completed", "completed_with_errors", "error"):
        raise HTTPException(status_code=400, detail=f"Cannot cleanup task with status: {status.status}")
    success = file_upload_service.cleanup_task_files(task_id)
    if not success:
        raise HTTPException(status_code=500, detail="Cleanup failed")
    return Response(status_code=204)


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str) -> None:
    """Delete a document file and its vector chunks."""
    filename = document_id
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="document_id must not contain path separators")

    file_path = uploaded_files_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")

    try:
        chunks_deleted = vector_store_manager.delete_by_document_name(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete document from vector store") from e

    try:
        file_path.unlink()
    except OSError as e:
        raise HTTPException(status_code=500, detail="Failed to delete document file") from e


@router.get("/{document_id}/content", response_model=None)
async def get_document_content(
    document_id: str,
    request: Request,
    content_format: Annotated[str | None, Query(alias="format", description="format=text for plain-text extraction")] = None,
) -> FileResponse | PlainTextResponse:
    """Return document bytes or plain text (query format=text or Accept: text/plain)."""
    filename = document_id
    accept = (request.headers.get("accept") or "").lower()
    wants_text = (content_format or "").lower() == "text" or "text/plain" in accept

    if not filename or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    file_path = uploaded_files_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    if wants_text:
        ext = Path(filename).suffix.lower()
        try:
            if ext in (".txt", ".md"):
                text = file_path.read_text(encoding="utf-8")
            elif ext in (".docx", ".doc"):
                paragraphs = extract_and_clean_docx(file_path)
                text = "\n\n".join(p for p in paragraphs if p.strip())
            else:
                raise HTTPException(status_code=400, detail=f"Text extraction not supported for {ext}")
            return PlainTextResponse(content=text)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}") from e

    if not filename or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = uploaded_files_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    media_type = "application/pdf" if filename.lower().endswith(".pdf") else None
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": os.getenv("ALLOW_ORIGINS", "http://localhost:5173").split(",")[0].strip(),
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
