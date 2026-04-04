"""Document management API endpoints for the RAG pipeline.

This module provides endpoints for uploading, listing, and serving documents.
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

# request.form() yields starlette.datastructures.UploadFile, not fastapi.datastructures.UploadFile.
from starlette.datastructures import UploadFile as StarletteUploadFile

from backend.shared.utils.directory_utils import (
    _format_path_for_error,
    ensure_directory_exists,
    get_uploaded_files_dir,
)

from ..config.parameter_sets import DEFAULT_PARAM_SET_NAME, RAGParams, get_param_set
from ..core.document_loader import DocumentLoader
from ..core.vector_store import get_vector_store_manager
from ..models.document_models import ProcessingStatus, UploadResponse
from ..services.document_processing_service import DocumentProcessingService
from ..services.file_upload_service import FileUploadService
from ..utils.docx_utils import extract_and_clean_docx
from ..utils.logging import StructuredLogger
from ..utils.progress import ProgressEvent, progress_notifier
from .metrics import get_metrics

logger = StructuredLogger(__name__)
logger.debug("Starting document management API endpoints")

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Initialize directories and services
uploaded_files_dir = get_uploaded_files_dir()
ensure_directory_exists(uploaded_files_dir)
document_loader = DocumentLoader()
vector_store_manager = get_vector_store_manager()
document_processing_service = DocumentProcessingService()
file_upload_service = FileUploadService()


async def process_document_background(file_path, filename: str, params_name: str) -> None:
    """Delegate background document processing to DocumentProcessingService.

    Args:
        file_path: Path to the uploaded file
        filename: Name of the file being processed
        params_name: Name of the parameter set to use
    """
    await document_processing_service.process_document_background(file_path, filename, params_name)
    get_metrics().record_ingestion()


@router.get("")
async def list_documents() -> dict[str, list[str]]:
    """Return a list of uploaded document filenames.

    Returns:
        Dict containing a list of filenames
    """
    logger.info("GET /api/v1/documents")
    files = [f.name for f in uploaded_files_dir.iterdir() if f.is_file()]
    return {"files": files}


class DocumentFromUrlRequest(BaseModel):
    """Request to ingest a document from a URL."""

    url: HttpUrl = Field(..., description="URL of the document to download (http/https only)")
    params_name: str = Field(default=DEFAULT_PARAM_SET_NAME, description="Parameter set for processing")


@router.post("/ingest-from-url")
async def upload_document_from_url(payload: DocumentFromUrlRequest, background_tasks: BackgroundTasks) -> dict:
    """Download a document from a URL and process it for RAG.

    Supports PDF, TXT, MD, DOCX. The document is downloaded, saved to the upload
    directory, and processed in the background (chunking, embedding, storage).

    Args:
        payload: URL and optional params_name
        background_tasks: FastAPI background tasks manager

    Returns:
        Dict with status and filename

    Raises:
        HTTPException: 400 if URL invalid or download fails
        HTTPException: 415 if content type not supported
    """
    url_str = str(payload.url)
    logger.info("POST /api/v1/documents/ingest-from-url", url=url_str, params_name=payload.params_name)

    parsed = urlparse(url_str)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail=f"URL scheme must be http or https, got: {parsed.scheme}",
        )

    params = get_param_set(payload.params_name)
    if not isinstance(params, RAGParams):
        raise HTTPException(status_code=400, detail=f"Invalid parameter set: {payload.params_name}")

    supported_extensions = {".pdf", ".txt", ".md", ".docx", ".doc", ".csv", ".json"}
    path_from_url = Path(parsed.path)
    ext = path_from_url.suffix.lower() if path_from_url.suffix else ""
    if ext not in supported_extensions:
        ext = ".pdf"  # Default for unknown; loader will validate

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url_str)
            response.raise_for_status()

            content = response.content
            if len(content) > 50 * 1024 * 1024:  # 50MB limit
                raise HTTPException(status_code=400, detail="Document size exceeds 50MB limit")

            # Get filename from Content-Disposition or URL
            cd = response.headers.get("content-disposition")
            if cd and "filename=" in cd:
                match = re.search(r'filename[*]?=(?:"([^"]+)"|\'([^\']+)\'|([^;\s]+))', cd, re.I)
                if match:
                    filename = (match.group(1) or match.group(2) or match.group(3) or "").strip()
            else:
                filename = path_from_url.name or f"document{ext}"

            # Sanitize filename
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
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download: {e.response.status_code} - {str(e)}",
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Download request failed: {str(e)}") from e


async def sync_upload_single_file(file: UploadFile, background_tasks: BackgroundTasks, params_name: str) -> JSONResponse:
    """Handle single-file sync upload: save, dedupe, queue background processing."""

    logger.info(
        "POST /api/v1/documents",
        filename=file.filename,
        size=file.size,
        content_type=file.content_type,
        async_mode=False,
    )

    params = get_param_set(params_name)
    if not isinstance(params, RAGParams):
        logger.warning("Upload rejected: invalid parameter set", params_name=params_name)
        raise HTTPException(status_code=400, detail="Invalid parameter set name")

    if not (filename := file.filename):
        logger.warning("Upload rejected: missing filename")
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file.size or file.size == 0:
        logger.warning("Upload rejected: empty file", filename=filename)
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
        logger.warning("Upload rejected: unsupported content type", filename=filename, content_type=content_type)
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {content_type}. Supported types: {', '.join(supported_types)}"
        )

    try:
        await progress_notifier.notify(ProgressEvent(filename, 5, "Upload started"))

        logger.debug(
            "Preparing to save file",
            filename=filename,
            upload_dir=str(uploaded_files_dir),
            upload_dir_exists=uploaded_files_dir.exists(),
            upload_dir_is_dir=uploaded_files_dir.is_dir(),
        )

        file_path = uploaded_files_dir / filename
        logger.debug("File path resolved", file_path=str(file_path))

        file_content = await file.read()
        logger.debug("File content read", content_size=len(file_content))

        file_content_hash = hashlib.sha256(file_content).hexdigest()
        embedding_model = params.embedding.model_name
        if vector_store_manager.has_document_with_file_hash(file_content_hash, embedding_model=embedding_model):
            logger.info(
                "Upload skipped: duplicate content",
                filename=filename,
                file_content_hash=file_content_hash[:16],
            )
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

        if not file_path.exists():
            raise RuntimeError(f"File was not saved successfully to {file_path}")

        logger.debug("File saved successfully", filename=str(file_path), file_size=file_path.stat().st_size)

        await progress_notifier.notify(ProgressEvent(filename, 10, "File saved"))

        await asyncio.sleep(0.1)

        background_tasks.add_task(process_document_background, file_path, filename, params_name)

        logger.info("Document upload completed, background processing started", filename=filename)

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
        logger.error(
            "Upload directory not writable. Ensure backend process has write access.",
            error=str(e),
        )
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {str(e)}"))
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "remediation": (
                    "Docker: use uploaded-files-data volume and entrypoint that chowns the directory. "
                    "Local: ensure UPLOADED_FILES_DIR exists and is writable (e.g. chmod 755)."
                ),
            },
        ) from e
    except OSError as e:
        logger.error("File system error during upload", filename=filename, error=str(e))
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {str(e)}"))
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "remediation": "Check backend logs. Ensure upload directory exists and is writable.",
            },
        ) from e
    except Exception as e:
        logger.error("Error during file upload", filename=filename, error=str(e), error_type=type(e).__name__)
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {str(e)}"))
        detail: str | dict = str(e)
        if os.getenv("ENVIRONMENT") == "development":
            import traceback

            detail = {"error": str(e), "traceback": traceback.format_exc()}
        raise HTTPException(status_code=500, detail=detail) from e


async def process_async_task_documents(task_id: str, params_name: str) -> None:
    """Run multi-file processing for an async upload task (task-scoped directory)."""

    logger.info("Starting background document processing", task_id=task_id, params_name=params_name)

    try:
        file_upload_service.update_processing_status(task_id, "processing", 0.0, "Starting document processing")

        task_dir = file_upload_service.upload_dir / task_id
        if not task_dir.exists():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")

        file_paths = [f for f in task_dir.iterdir() if f.is_file()]
        if not file_paths:
            raise ValueError("No files found in task directory")

        logger.info("Found files for processing", task_id=task_id, file_count=len(file_paths))

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

        logger.info("Background processing completed", task_id=task_id, **results)

    except Exception as e:
        logger.error("Background processing failed", task_id=task_id, error=str(e))
        file_upload_service.update_processing_status(task_id, "error", -1.0, f"Processing failed: {str(e)}")


@router.post("", response_model=None)
async def create_document(
    request: Request,
    background_tasks: BackgroundTasks,
    async_q: Annotated[bool, Query(alias="async")] = False,
    params_name: Annotated[str, Query()] = DEFAULT_PARAM_SET_NAME,
) -> JSONResponse | UploadResponse:
    """Create document(s): sync multipart field `file`, or async with `async=true` and field `files`."""

    form = await request.form()

    if async_q:
        raw_files = form.getlist("files")
        files: List[UploadFile] = [f for f in raw_files if isinstance(f, StarletteUploadFile)]
        if not files:
            raise HTTPException(status_code=400, detail="Multipart field 'files' is required when async=true")
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")

        logger.info("POST /api/v1/documents", file_count=len(files), params_name=params_name, async_mode=True)

        try:
            upload_result = await file_upload_service.upload_multiple_files(files)
            if upload_result.accepted_count > 0:
                background_tasks.add_task(process_async_task_documents, upload_result.task_id, params_name)
                logger.info("Background processing started", task_id=upload_result.task_id)
            return upload_result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Upload failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e

    single = form.get("file")
    if not isinstance(single, StarletteUploadFile):
        raise HTTPException(status_code=400, detail="Multipart field 'file' is required when async=false (default)")

    return await sync_upload_single_file(single, background_tasks, params_name)


@router.get("/tasks/{task_id}", response_model=ProcessingStatus)
async def get_processing_status(task_id: str) -> ProcessingStatus:
    """Return async upload task status."""

    logger.info("GET /api/v1/documents/tasks/{task_id}", task_id=task_id)

    status = file_upload_service.get_processing_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return status


@router.delete("/tasks/{task_id}", status_code=204)
async def cleanup_task(task_id: str) -> Response:
    """Remove task workspace after completed or failed processing."""

    logger.info("DELETE /api/v1/documents/tasks/{task_id}", task_id=task_id)

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
    """Delete a document file and its vector chunks (document_id is the stored filename)."""

    filename = document_id
    if "/" in filename or "\\" in filename or ".." in filename:
        logger.warning("Delete rejected: invalid document_id", filename=filename)
        raise HTTPException(status_code=400, detail="document_id must not contain path separators")

    file_path = uploaded_files_dir / filename
    if not file_path.exists() or not file_path.is_file():
        logger.info("Delete: document not found", filename=filename)
        raise HTTPException(status_code=404, detail=f"Document not found: {filename}")

    try:
        chunks_deleted = vector_store_manager.delete_by_document_name(filename)
        logger.info("Deleted chunks from vector store", filename=filename, chunks_deleted=chunks_deleted)
    except Exception as e:
        logger.error("Failed to delete chunks from vector store", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document from vector store") from e

    try:
        file_path.unlink()
        logger.info("Deleted document file", filename=filename)
    except OSError as e:
        logger.error("Failed to delete file", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document file") from e


async def _serve_file(filename: str):
    """Internal function to serve a file with proper error handling and logging.

    Args:
        filename: Name of the file to serve

    Returns:
        FileResponse: The requested file

    Raises:
        HTTPException: 404 if file not found
        HTTPException: 400 if filename is invalid
        HTTPException: 500 if file access fails
    """
    try:
        logger.debug(
            "File request received",
            filename=filename,
            upload_dir=str(uploaded_files_dir),
            upload_dir_exists=uploaded_files_dir.exists(),
            upload_dir_is_dir=uploaded_files_dir.is_dir(),
        )

        # Input validation
        if not filename or ".." in filename or "/" in filename:
            logger.warning("Invalid filename requested", filename=filename, reason="Contains invalid characters or is empty")
            raise HTTPException(status_code=400, detail="Invalid filename: contains invalid characters or is empty")

        file_path = uploaded_files_dir / filename
        logger.debug(
            "Resolved file path",
            filename=filename,
            full_path=str(file_path),
            exists=file_path.exists(),
            is_file=file_path.is_file() if file_path.exists() else None,
            size=file_path.stat().st_size if file_path.exists() else None,
        )

        # Check if file exists
        if not file_path.exists():
            logger.warning(
                "File not found", filename=filename, path=str(file_path), upload_dir_contents=list(uploaded_files_dir.iterdir())
            )
            raise HTTPException(
                status_code=404, detail=f"File not found: {filename} (checked in {_format_path_for_error(uploaded_files_dir)})"
            )

        # Check if path is a file (not a directory)
        if not file_path.is_file():
            logger.warning(
                "Path is not a file",
                filename=filename,
                path=str(file_path),
                is_dir=file_path.is_dir(),
                is_symlink=file_path.is_symlink(),
            )
            raise HTTPException(status_code=400, detail=f"Invalid file path: {filename} is not a regular file")

        # Log successful file access
        logger.info(
            "Serving file",
            filename=filename,
            path=str(file_path),
            size=file_path.stat().st_size,
            media_type="application/pdf" if filename.lower().endswith(".pdf") else None,
        )

        # Set media type based on file extension
        media_type = "application/pdf" if filename.lower().endswith(".pdf") else None

        # Return file response
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

    except HTTPException:
        raise
    except Exception as e:
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "filename": filename,
            "file_path": str(file_path),
            "upload_dir": str(uploaded_files_dir),
            "upload_dir_exists": uploaded_files_dir.exists(),
            "upload_dir_contents": [str(p) for p in uploaded_files_dir.iterdir()],
        }
        logger.error("Error serving file", **error_info)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while serving file: {str(e)}. Error type: {type(e).__name__}. File: {filename}. Path: {str(file_path)}",
        ) from e


@router.get("/{document_id}/content", response_model=None)
async def get_document_content(
    document_id: str,
    request: Request,
    content_format: Annotated[str | None, Query(alias="format", description="format=text for plain-text extraction")] = None,
) -> FileResponse | PlainTextResponse:
    """Return document bytes or plain text (query format=text or Accept: text/plain)."""

    filename = document_id
    logger.info(
        "GET /api/v1/documents/{document_id}/content",
        document_id=document_id,
        content_format=content_format,
    )

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
                raise HTTPException(
                    status_code=400,
                    detail=f"Text extraction not supported for {ext}; omit format=text for binary download.",
                )
            return PlainTextResponse(content=text)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error extracting text", filename=filename, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}") from e

    return await _serve_file(filename)
