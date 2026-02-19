"""Document management API endpoints for the RAG pipeline.

This module provides endpoints for uploading, listing, and serving documents.
"""

import asyncio
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl

from backend.shared.utils.directory_utils import (
    _format_path_for_error,
    ensure_directory_exists,
    get_uploaded_files_dir,
)

from ..config.parameter_sets import DEFAULT_PARAM_SET_NAME, RAGParams, get_param_set
from ..core.document_loader import DocumentLoader
from ..core.vector_store import get_vector_store_manager_from_env
from ..services.document_processing_service import DocumentProcessingService
from ..utils.logging import StructuredLogger
from ..utils.progress import ProgressEvent, progress_notifier
from .metrics import get_metrics

logger = StructuredLogger(__name__)
logger.debug("Starting document management API endpoints")

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize directories and services
uploaded_files_dir = get_uploaded_files_dir()
ensure_directory_exists(uploaded_files_dir)
document_loader = DocumentLoader()
vector_store_manager = get_vector_store_manager_from_env()
document_processing_service = DocumentProcessingService()


async def process_document_background(file_path, filename: str, params_name: str) -> None:
    """Delegate background document processing to DocumentProcessingService.

    Args:
        file_path: Path to the uploaded file
        filename: Name of the file being processed
        params_name: Name of the parameter set to use
    """
    await document_processing_service.process_document_background(file_path, filename, params_name)
    get_metrics().record_ingestion()


@router.get("/list")
async def list_documents() -> dict[str, list[str]]:
    """Return a list of uploaded document filenames.

    Returns:
        Dict containing a list of filenames
    """
    logger.info("GET /api/documents/list")
    files = [f.name for f in uploaded_files_dir.iterdir() if f.is_file()]
    return {"files": files}


@router.delete("/{filename}", status_code=204)
async def delete_document(filename: str) -> None:
    """Delete a document and its vector store chunks.

    Removes the file from disk and all associated chunks from the vector store.

    Args:
        filename: Name of the document file (e.g. 'report.pdf').
            Must not contain path separators (security: path traversal prevention).

    Raises:
        HTTPException: 400 if filename contains path separators.
        HTTPException: 404 if document does not exist.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        logger.warning("Delete rejected: invalid filename", filename=filename)
        raise HTTPException(status_code=400, detail="Filename must not contain path separators")

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


class DocumentFromUrlRequest(BaseModel):
    """Request to ingest a document from a URL."""

    url: HttpUrl = Field(..., description="URL of the document to download (http/https only)")
    params_name: str = Field(default=DEFAULT_PARAM_SET_NAME, description="Parameter set for processing")


@router.post("/from-url")
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
    logger.info("POST /api/documents/from-url", url=url_str, params_name=payload.params_name)

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


@router.post("/upload")
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks, params_name: str = DEFAULT_PARAM_SET_NAME) -> dict:
    """Handle file upload and start background processing.

    Args:
        file: The uploaded file
        background_tasks: FastAPI background tasks manager
        params_name: Name of the parameter set to use (default: DEFAULT_PARAM_SET_NAME)

    Returns:
        Dict with upload status and file information

    Raises:
        HTTPException: If upload validation fails
    """
    logger.info("POST /api/documents/upload", filename=file.filename, size=file.size, content_type=file.content_type)

    # Validate request params_name
    params = get_param_set(params_name)
    if not isinstance(params, RAGParams):
        logger.warning("Upload rejected: invalid parameter set", params_name=params_name)
        raise HTTPException(status_code=400, detail="Invalid parameter set name")

    # Validate request
    if not (filename := file.filename):
        logger.warning("Upload rejected: missing filename")
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file.size or file.size == 0:
        logger.warning("Upload rejected: empty file", filename=filename)
        raise HTTPException(status_code=400, detail="File cannot be empty")

    # Check for supported content types
    supported_types = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
        "text/csv",
        "application/json",
    ]

    if (content_type := file.content_type) not in supported_types:
        logger.warning("Upload rejected: unsupported content type", filename=filename, content_type=content_type)
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {content_type}. Supported types: {', '.join(supported_types)}"
        )

    try:
        # Notify upload started
        await progress_notifier.notify(ProgressEvent(filename, 5, "Upload started"))

        # Ensure the upload directory exists
        logger.debug(
            "Preparing to save file",
            filename=filename,
            upload_dir=str(uploaded_files_dir),
            upload_dir_exists=uploaded_files_dir.exists(),
            upload_dir_is_dir=uploaded_files_dir.is_dir(),
        )

        # Save upload to the proper uploaded files directory
        file_path = uploaded_files_dir / filename
        logger.debug("File path resolved", file_path=str(file_path))

        # Read file content first
        file_content = await file.read()
        logger.debug("File content read", content_size=len(file_content))

        # Directory is already ensured to exist at module level

        # Write file content
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Verify file was saved
        if not file_path.exists():
            raise RuntimeError(f"File was not saved successfully to {file_path}")

        logger.debug("File saved successfully", filename=str(file_path), file_size=file_path.stat().st_size)

        await progress_notifier.notify(ProgressEvent(filename, 10, "File saved"))

        # Small delay to ensure file is fully written
        await asyncio.sleep(0.1)

        # Start background processing
        background_tasks.add_task(process_document_background, file_path, filename, params_name)

        logger.info("Document upload completed, background processing started", filename=filename)

        return {
            "message": "Document uploaded successfully, processing started",
            "file_id": filename,
            "status": "uploaded",
            "processing": "started",
        }

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
        detail = str(e)
        if os.getenv("ENVIRONMENT") == "development":
            import traceback

            detail = {"error": str(e), "traceback": traceback.format_exc()}
        raise HTTPException(status_code=500, detail=detail) from e


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


@router.get("/files/{filename}")
async def serve_document_file(filename: str) -> FileResponse:
    """Serve uploaded files with proper error handling and logging.

    Args:
        filename: Name of the file to serve

    Returns:
        FileResponse: The requested file

    Raises:
        HTTPException: 404 if file not found
        HTTPException: 400 if filename is invalid
        HTTPException: 500 if file access fails
    """
    logger.info("GET /api/documents/files/{filename}", filename=filename)
    return await _serve_file(filename)
