"""Document management API endpoints for the RAG pipeline.

This module provides endpoints for uploading, listing, and serving documents.
"""

import asyncio
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config.parameter_sets import DEFAULT_PARAM_SET_NAME, RAGParams, get_param_set
from ..core.document_loader import DocumentLoader
from ..core.embeddings import process_document
from ..core.vector_store import ChromaVectorStoreManager, get_vector_store_manager_from_env
from ..utils.directory_utils import (
    _format_path_for_error,
    ensure_directory_exists,
    get_uploaded_files_dir,
)
from ..utils.logging import StructuredLogger
from ..utils.progress import ProgressEvent, progress_notifier

logger = StructuredLogger(__name__)
logger.debug("Starting document management API endpoints")

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize directories and services
uploaded_files_dir = get_uploaded_files_dir()
ensure_directory_exists(uploaded_files_dir)
document_loader = DocumentLoader()
vector_store_manager = get_vector_store_manager_from_env()

# Type cast to ChromaVectorStoreManager to access config
chroma_manager = vector_store_manager if isinstance(vector_store_manager, ChromaVectorStoreManager) else None


# Global variable to store progress events for the current processing task
_current_progress_events = []


def progress_callback(filename: str, progress: float) -> None:
    """Store progress events for document processing.

    This function is called from the sync process_document function.
    It stores progress events that will be processed by the async background task.

    Args:
        filename: The name of the file being processed
        progress: The current progress of the processing (0.0-1.0)
    """
    global _current_progress_events

    # Map processing progress (0.0-1.0) to upload progress (15-100%)
    # This ensures we start at 15% (after upload) and go to 100%
    upload_progress = int(15 + (progress * 85))  # 15% to 100%

    # Create appropriate progress messages based on the phase
    if progress <= 0.1:
        message = "Loading document..."
    elif progress <= 0.5:
        message = f"Chunking document ({int(progress * 100)}%)"
    elif progress <= 0.8:
        message = f"Generating embeddings ({int(progress * 100)}%)"
    elif progress < 1.0:
        message = "Storing in vector database..."
    else:
        message = "Processing completed"

    logger.debug(
        "Document processing progress callback called",
        filename=filename,
        processing_progress=progress,
        upload_progress=upload_progress,
        progress_message=message,
    )

    # Store the progress event for the async task to process
    _current_progress_events.append({"filename": filename, "progress": upload_progress, "message": message})


async def process_document_background(file_path, filename: str, params_name: str):
    """Process document in the background with progress updates.

    This function follows the same pattern as the working test.py example.
    It runs the sync process_document function and then processes any progress events.

    Args:
        file_path: Path to the uploaded file
        filename: Name of the file being processed
        params_name: Name of the parameter set to use
    """
    global _current_progress_events

    try:
        logger.info(f"Starting background processing for {filename}")

        # Clear any previous progress events
        _current_progress_events.clear()

        # Verify file exists before processing
        if not file_path.exists():
            logger.error("File not found for processing", filename=filename, file_path=str(file_path))
            await progress_notifier.notify(ProgressEvent(filename, -1, f"File not found: {filename}"))
            return

        logger.debug(
            "File verified for processing", filename=filename, file_path=str(file_path), file_size=file_path.stat().st_size
        )

        # Get parameter set
        params = get_param_set(params_name)
        if not isinstance(params, RAGParams):
            await progress_notifier.notify(ProgressEvent(filename, -1, f"Invalid parameter set: {params_name}"))
            return

        # Notify processing started
        await progress_notifier.notify(ProgressEvent(filename, 15, "Processing started"))

        # Small yield to allow other tasks to run
        await asyncio.sleep(0.01)

        logger.debug("Starting process_document call", filename=filename)

        # Run the sync process_document function in a thread pool
        # This will call progress_callback which stores events in _current_progress_events
        loop = asyncio.get_event_loop()

        # Start a task to monitor and send progress events in real-time
        progress_task = asyncio.create_task(_send_progress_events(filename))

        try:
            chunks_processed, records_stored = await loop.run_in_executor(
                None,  # Use default executor
                lambda: process_document(
                    file_path,
                    params.embedding.model_name,
                    persist_dir=chroma_manager.config.persist_directory if chroma_manager else uploaded_files_dir,
                    collection_name=chroma_manager.config.collection_name if chroma_manager else "documents",
                    chunk_size=params.chunking.chunk_size,
                    chunk_overlap=params.chunking.chunk_overlap,
                    max_pages=None,
                    deduplicate=True,
                    progress_callback=progress_callback,
                ),
            )

            logger.debug(
                "Document processing completed",
                filename=filename,
                chunks_processed=chunks_processed,
                records_stored=records_stored,
            )
        finally:
            # Cancel the progress task
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        # Process any remaining progress events
        for event_data in _current_progress_events:
            event = ProgressEvent(file_id=event_data["filename"], progress=event_data["progress"], message=event_data["message"])
            await progress_notifier.notify(event)
            logger.debug(f"Sent progress event: {event_data['progress']}% - {event_data['message']}")

        # Clear the events
        _current_progress_events.clear()

    except Exception as e:
        logger.error("Error during document processing", filename=filename, error=str(e), error_type=type(e).__name__)
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Processing failed: {str(e)}"))


async def _send_progress_events(filename: str):
    """Monitor and send progress events in real-time.

    This function runs concurrently with document processing and sends
    progress events as they are created by the progress_callback.

    Args:
        filename: The filename to monitor progress events for
    """
    global _current_progress_events

    try:
        while True:
            # Check for new progress events
            if _current_progress_events:
                # Get events for this file
                file_events = [e for e in _current_progress_events if e["filename"] == filename]

                # Remove processed events
                for event_data in file_events:
                    _current_progress_events.remove(event_data)

                    # Send the event
                    event = ProgressEvent(
                        file_id=event_data["filename"], progress=event_data["progress"], message=event_data["message"]
                    )
                    await progress_notifier.notify(event)
                    logger.debug(f"Sent real-time progress event: {event_data['progress']}% - {event_data['message']}")

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        logger.debug(f"Progress sender cancelled for {filename}")
        raise
    except Exception as e:
        logger.error(f"Error in progress sender for {filename}: {e}")


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
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks, params_name: str = DEFAULT_PARAM_SET_NAME):
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

    except Exception as e:
        logger.error("Error during file upload", filename=filename, error=str(e), error_type=type(e).__name__)
        await progress_notifier.notify(ProgressEvent(filename, -1, f"Upload failed: {str(e)}"))
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
