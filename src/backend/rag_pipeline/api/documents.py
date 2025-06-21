"""Document management API endpoints for the RAG pipeline.

This module provides endpoints for uploading, listing, and serving documents.
"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
from ..core.document_loader import DocumentLoader
from ..core.embeddings import process_document
from ..core.vector_store import get_vector_store_manager_from_env
from ..utils.directory_utils import (
    _format_path_for_error,
    ensure_directory_exists,
    get_uploaded_files_dir,
)
from ..utils.logging import StructuredLogger
from ..utils.progress import ProgressEvent, progress_notifier

logger = StructuredLogger(__name__, level="DEBUG")
logger.debug("Starting document management API endpoints")

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize directories and services
uploaded_files_dir = get_uploaded_files_dir()
ensure_directory_exists(uploaded_files_dir)
document_loader = DocumentLoader()
vector_store_manager = get_vector_store_manager_from_env()


@router.get("/list")
async def list_documents() -> dict[str, list[str]]:
    """Return a list of uploaded document filenames.

    Returns:
        Dict containing a list of filenames
    """
    logger.info("GET /api/documents/list")
    files = [f.name for f in uploaded_files_dir.iterdir() if f.is_file()]
    return {"files": files}


@router.post("/upload")
async def upload_document(file: UploadFile, params_name: str = DEFAULT_PARAM_SET_NAME):
    """Handle file upload, chunking, and embedding.

    Args:
        file: The uploaded file
        params_name: Name of the parameter set to use (default: DEFAULT_PARAM_SET_NAME)

    Returns:
        Dict with success message

    Raises:
        HTTPException: If upload or processing fails
    """
    logger.info("POST /api/documents/upload", filename=file.filename, size=file.size, content_type=file.content_type)

    try:
        # Notify upload started
        await progress_notifier.notify(ProgressEvent(file.filename, 5, "Upload started"))

        # Save upload to the proper uploaded files directory
        file_path = uploaded_files_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
            logger.debug("File saved to", filename=str(file_path))

        await progress_notifier.notify(ProgressEvent(file.filename, 10, "File saved"))

        # Process the document
        try:
            logger.debug("Processing document", filename=file.filename, params_name=params_name)
            params = get_param_set(params_name)

            # Create a sync progress callback that can be called from the processing thread
            def progress_callback(progress: float) -> None:
                """Map processing progress (0.0-1.0) to upload progress (10-95%)."""
                # Map progress from 0.0-1.0 to 10-95% range
                upload_progress = 10 + int(progress * 85)
                logger.debug(
                    "Document processing progress",
                    filename=file.filename,
                    processing_progress=progress,
                    upload_progress=upload_progress,
                )
                # Schedule the async notification to run in the event loop
                asyncio.create_task(
                    progress_notifier.notify(
                        ProgressEvent(file.filename, upload_progress, f"Processing document ({int(progress * 100)}%)")
                    )
                )

            # Process document in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            chunks_processed, records_stored = await loop.run_in_executor(
                None,  # Use default executor
                process_document,
                file_path,
                params.embedding.model_name,
                persist_dir=vector_store_manager.config.persist_directory,
                collection_name=vector_store_manager.config.collection_name,
                chunk_size=params.chunking.chunk_size,
                chunk_overlap=params.chunking.chunk_overlap,
                max_pages=None,
                deduplicate=False,
                progress_callback=progress_callback,
            )

            logger.debug(
                "Document processing completed",
                filename=file.filename,
                chunks_processed=chunks_processed,
                records_stored=records_stored,
            )

            await progress_notifier.notify(ProgressEvent(file.filename, 95, "Processing completed"))

            # Notify final completion
            await progress_notifier.notify(ProgressEvent(file.filename, 100, "Upload completed successfully"))

            return {"message": "Document uploaded and processed successfully"}

        except Exception as e:
            logger.error("Error during document processing", filename=file.filename, error=str(e))
            await progress_notifier.notify(ProgressEvent(file.filename, -1, f"Processing failed: {str(e)}"))
            raise

    except Exception as e:
        logger.error("Error during file upload", filename=file.filename, error=str(e))
        await progress_notifier.notify(ProgressEvent(file.filename, -1, f"Upload failed: {str(e)}"))
        raise HTTPException(status_code=500, detail=str(e)) from e


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
                "Access-Control-Allow-Origin": "http://localhost:5173",  # TODO: make this configurable
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
async def serve_document_file(filename: str):
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
