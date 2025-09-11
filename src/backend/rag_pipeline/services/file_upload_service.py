"""File upload service for handling document uploads and validation.

This service implements the file upload functionality as specified in the
architecture design, including validation, temporary storage, and error handling.

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and implementation requirements.
"""

import asyncio
import hashlib
import mimetypes
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from ..models.document_models import (
    DocumentMetadata,
    FileValidationError,
    ProcessingStatus,
    UploadResponse,
)
from ..utils.directory_utils import ensure_directory_exists, get_uploaded_files_dir
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class FileUploadService:
    """Service for handling file uploads, validation, and temporary storage.

    Implements the file upload system as specified in the architecture design.
    """

    # Configuration constants
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
        "text/csv",
        "application/json",
    }

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc", ".csv", ".json"}

    def __init__(self, upload_dir: Optional[Path] = None):
        """Initialize the file upload service.

        Args:
            upload_dir: Directory for temporary file storage. If None, uses default.
        """
        self.upload_dir = upload_dir or get_uploaded_files_dir()
        ensure_directory_exists(self.upload_dir)

        # In-memory storage for processing status (in production, use database)
        self._processing_tasks: Dict[str, ProcessingStatus] = {}

        logger.info("FileUploadService initialized", upload_dir=str(self.upload_dir))

    async def upload_multiple_files(self, files: List[UploadFile], task_id: Optional[str] = None) -> UploadResponse:
        """Upload and validate multiple files.

        Args:
            files: List of uploaded files
            task_id: Optional task ID for tracking. If None, generates new ID.

        Returns:
            UploadResponse with upload results and validation information

        Raises:
            HTTPException: If upload fails or validation errors occur
        """
        if not task_id:
            task_id = str(uuid4())

        logger.info("Starting multiple file upload", task_id=task_id, file_count=len(files))

        accepted_files = []
        rejected_files = []

        # Initialize processing status
        self._processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="uploading",
            progress=0.0,
            total_files=len(files),
            processed_files=0,
            message="Starting file upload",
        )

        try:
            for i, file in enumerate(files):
                try:
                    # Validate individual file
                    validation_result = await self._validate_file(file)
                    if validation_result["valid"]:
                        # Save file
                        saved_path = await self._save_file(file, task_id)
                        accepted_files.append(
                            {
                                "filename": file.filename,
                                "saved_path": str(saved_path),
                                "size": file.size,
                                "content_type": file.content_type,
                            }
                        )
                        logger.info("File accepted", filename=file.filename, task_id=task_id)
                    else:
                        rejected_files.append({"filename": file.filename, "error": validation_result["error"]})
                        logger.warning("File rejected", filename=file.filename, error=validation_result["error"])

                except Exception as e:
                    error_msg = f"Unexpected error processing {file.filename}: {str(e)}"
                    rejected_files.append({"filename": file.filename, "error": error_msg})
                    logger.error("File processing error", filename=file.filename, error=str(e))

                # Update progress
                progress = (i + 1) / len(files)
                self._processing_tasks[task_id].progress = progress
                self._processing_tasks[task_id].processed_files = i + 1
                self._processing_tasks[task_id].message = f"Processed {i + 1}/{len(files)} files"

            # Update final status
            if accepted_files:
                self._processing_tasks[task_id].status = "uploaded"
                self._processing_tasks[task_id].message = f"Upload completed: {len(accepted_files)} files accepted"
            else:
                self._processing_tasks[task_id].status = "failed"
                self._processing_tasks[task_id].message = "No files were accepted"

            return UploadResponse(
                task_id=task_id,
                accepted_files=[f["filename"] for f in accepted_files],
                rejected_files=rejected_files,
                message=f"Upload completed: {len(accepted_files)}/{len(files)} files accepted",
                total_files=len(files),
                accepted_count=len(accepted_files),
                rejected_count=len(rejected_files),
            )

        except Exception as e:
            logger.error("Upload failed", task_id=task_id, error=str(e))
            self._processing_tasks[task_id].status = "error"
            self._processing_tasks[task_id].message = f"Upload failed: {str(e)}"
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def _validate_file(self, file: UploadFile) -> Dict:
        """Validate a single uploaded file.

        Args:
            file: Uploaded file to validate

        Returns:
            Dict with validation result and error details
        """
        # Check filename
        if not file.filename:
            return {"valid": False, "error": "Filename is required"}

        # Check file size
        if not file.size or file.size == 0:
            return {"valid": False, "error": "File cannot be empty"}

        if file.size > self.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"File size ({file.size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)",
            }

        # Check content type
        if file.content_type not in self.SUPPORTED_MIME_TYPES:
            return {
                "valid": False,
                "error": f"Unsupported file type: {file.content_type}. Supported types: {', '.join(self.SUPPORTED_MIME_TYPES)}",
            }

        # Check file extension
        file_path = Path(file.filename)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Unsupported file extension: {file_path.suffix}. Supported extensions: {', '.join(self.SUPPORTED_EXTENSIONS)}",
            }

        # Additional security checks
        if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
            return {"valid": False, "error": "Filename contains invalid characters"}

        return {"valid": True}

    async def _save_file(self, file: UploadFile, task_id: str) -> Path:
        """Save uploaded file to temporary storage.

        Args:
            file: Uploaded file
            task_id: Task ID for organizing files

        Returns:
            Path to saved file

        Raises:
            HTTPException: If file saving fails
        """
        try:
            # Create task-specific directory
            task_dir = self.upload_dir / task_id
            task_dir.mkdir(exist_ok=True)

            # Generate safe filename
            safe_filename = self._generate_safe_filename(file.filename)
            file_path = task_dir / safe_filename

            # Read and save file content
            content = await file.read()

            with open(file_path, "wb") as f:
                f.write(content)

            # Verify file was saved
            if not file_path.exists():
                raise RuntimeError(f"File was not saved successfully to {file_path}")

            logger.info("File saved successfully", filename=file.filename, path=str(file_path), size=len(content))
            return file_path

        except Exception as e:
            logger.error("File save failed", filename=file.filename, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    def _generate_safe_filename(self, filename: str) -> str:
        """Generate a safe filename for storage.

        Args:
            filename: Original filename

        Returns:
            Safe filename for storage
        """
        # Remove path components and normalize
        safe_name = Path(filename).name

        # Add timestamp to avoid conflicts
        import time

        timestamp = int(time.time())
        name_parts = safe_name.rsplit(".", 1)
        if len(name_parts) == 2:
            safe_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            safe_name = f"{safe_name}_{timestamp}"

        return safe_name

    def get_processing_status(self, task_id: str) -> Optional[ProcessingStatus]:
        """Get processing status for a task.

        Args:
            task_id: Task identifier

        Returns:
            ProcessingStatus if task exists, None otherwise
        """
        return self._processing_tasks.get(task_id)

    def update_processing_status(self, task_id: str, status: str, progress: float, message: Optional[str] = None) -> bool:
        """Update processing status for a task.

        Args:
            task_id: Task identifier
            status: New status
            progress: Progress percentage (0.0 to 1.0)
            message: Optional status message

        Returns:
            True if task was updated, False if task not found
        """
        if task_id not in self._processing_tasks:
            return False

        self._processing_tasks[task_id].status = status
        self._processing_tasks[task_id].progress = progress
        if message:
            self._processing_tasks[task_id].message = message
        self._processing_tasks[task_id].updated_at = datetime.now(timezone.utc)

        return True

    def cleanup_task_files(self, task_id: str) -> bool:
        """Clean up files for a completed task.

        Args:
            task_id: Task identifier

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            task_dir = self.upload_dir / task_id
            if task_dir.exists():
                import shutil

                shutil.rmtree(task_dir)
                logger.info("Task files cleaned up", task_id=task_id)

            # Remove from memory
            if task_id in self._processing_tasks:
                del self._processing_tasks[task_id]

            return True

        except Exception as e:
            logger.error("Cleanup failed", task_id=task_id, error=str(e))
            return False
