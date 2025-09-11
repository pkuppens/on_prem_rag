"""Enhanced document management API endpoints for the RAG pipeline.

This module implements the enhanced document upload and processing endpoints
as specified in the architecture design, including multiple file upload support,
comprehensive validation, and proper status tracking.

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and implementation requirements.
"""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..config.parameter_sets import DEFAULT_PARAM_SET_NAME
from ..models.document_models import (
    ProcessingStatus,
    UploadResponse,
)
from ..services.document_processing_service import DocumentProcessingService
from ..services.file_upload_service import FileUploadService
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)

# Create enhanced router with v1 prefix
router = APIRouter(prefix="/api/v1", tags=["documents-enhanced"])

# Initialize services
file_upload_service = FileUploadService()
document_processing_service = DocumentProcessingService()


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None, params_name: str = DEFAULT_PARAM_SET_NAME
) -> UploadResponse:
    """Upload multiple documents for processing.

    This endpoint implements the file upload system as specified in the architecture design.
    It supports multiple file uploads, comprehensive validation, and background processing.

    Args:
        files: List of uploaded files (PDF, DOCX, MD, TXT)
        background_tasks: FastAPI background tasks manager
        params_name: Name of the parameter set to use for processing

    Returns:
        UploadResponse with upload results and task tracking information

    Raises:
        HTTPException: If upload validation fails or processing cannot be started
    """
    logger.info("POST /api/v1/upload", file_count=len(files), params_name=params_name)

    # Validate input
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    if len(files) > 10:  # Reasonable limit for multiple file uploads
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")

    try:
        # Upload and validate files
        upload_result = await file_upload_service.upload_multiple_files(files)

        # Start background processing if files were accepted
        if upload_result.accepted_count > 0:
            background_tasks.add_task(process_documents_background, upload_result.task_id, params_name)
            logger.info("Background processing started", task_id=upload_result.task_id)

        return upload_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status/{task_id}", response_model=ProcessingStatus)
async def get_processing_status(task_id: str) -> ProcessingStatus:
    """Get processing status for a task.

    This endpoint provides real-time status information for document processing tasks.

    Args:
        task_id: Task identifier returned from upload endpoint

    Returns:
        ProcessingStatus with current task status and progress information

    Raises:
        HTTPException: If task not found
    """
    logger.info("GET /api/v1/status/{task_id}", task_id=task_id)

    status = file_upload_service.get_processing_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return status


@router.get("/list")
async def list_documents() -> dict:
    """List all processed documents.

    This endpoint provides a list of all documents that have been successfully
    processed and are available for querying.

    Returns:
        Dict containing list of document metadata
    """
    logger.info("GET /api/v1/list")

    # TODO: Implement document listing from vector store
    # For now, return empty list
    return {"documents": [], "total_count": 0, "message": "Document listing not yet implemented"}


async def process_documents_background(task_id: str, params_name: str):
    """Process uploaded documents in the background.

    This function runs in the background after file upload and handles the
    complete document processing workflow.

    Args:
        task_id: Task identifier for tracking
        params_name: Parameter set name for processing configuration
    """
    logger.info("Starting background document processing", task_id=task_id, params_name=params_name)

    try:
        # Update status to processing
        file_upload_service.update_processing_status(task_id, "processing", 0.0, "Starting document processing")

        # Get task directory and find uploaded files
        task_dir = file_upload_service.upload_dir / task_id
        if not task_dir.exists():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")

        # Find all files in task directory
        file_paths = [f for f in task_dir.iterdir() if f.is_file()]
        if not file_paths:
            raise ValueError("No files found in task directory")

        logger.info("Found files for processing", task_id=task_id, file_count=len(file_paths))

        # Process documents
        results = await document_processing_service.process_documents(task_id, file_paths, params_name)

        # Update final status
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


@router.delete("/task/{task_id}")
async def cleanup_task(task_id: str) -> dict:
    """Clean up files and data for a completed task.

    This endpoint removes temporary files and cleans up task data after processing
    is complete. This helps manage storage and prevents accumulation of temporary files.

    Args:
        task_id: Task identifier to clean up

    Returns:
        Dict with cleanup status

    Raises:
        HTTPException: If task not found or cleanup fails
    """
    logger.info("DELETE /api/v1/task/{task_id}", task_id=task_id)

    # Check if task exists
    status = file_upload_service.get_processing_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    # Only allow cleanup of completed or failed tasks
    if status.status not in ["completed", "completed_with_errors", "error"]:
        raise HTTPException(status_code=400, detail=f"Cannot cleanup task with status: {status.status}")

    # Perform cleanup
    success = file_upload_service.cleanup_task_files(task_id)
    if not success:
        raise HTTPException(status_code=500, detail="Cleanup failed")

    return {"message": "Task cleanup completed", "task_id": task_id, "status": "cleaned_up"}
