"""File upload service for handling document uploads and validation.

Moved from ``rag_pipeline/services/file_upload_service.py`` as part of the
Ingestion BC extraction (Phase 3). Provides the same public API.
"""

from __future__ import annotations

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from backend.rag_pipeline.models.document_models import (
    ProcessingStatus,
    UploadResponse,
)
from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.shared.utils.directory_utils import ensure_directory_exists, get_uploaded_files_dir

logger = StructuredLogger(__name__)


class FileUploadService:
    """Service for handling file uploads, validation, and temporary storage."""

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/csv",
        "application/json",
    }
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm", ".docx", ".doc", ".csv", ".json"}

    def __init__(self, upload_dir: Path | None = None) -> None:
        self.upload_dir = upload_dir or get_uploaded_files_dir()
        ensure_directory_exists(self.upload_dir)
        self._processing_tasks: dict[str, ProcessingStatus] = {}
        logger.info("FileUploadService initialized", upload_dir=str(self.upload_dir))

    async def upload_multiple_files(self, files: list[UploadFile], task_id: str | None = None) -> UploadResponse:
        """Upload and validate multiple files.

        Args:
            files: List of uploaded files.
            task_id: Optional task ID for tracking.

        Returns:
            UploadResponse with upload results and validation information.

        Raises:
            HTTPException: If upload fails or validation errors occur.
        """
        if not task_id:
            task_id = str(uuid4())

        logger.info("Starting multiple file upload", task_id=task_id, file_count=len(files))

        accepted_files: list[dict[str, Any]] = []
        rejected_files: list[dict[str, str]] = []

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
                    validation_result = await self._validate_file(file)
                    if validation_result["valid"]:
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

                progress = (i + 1) / len(files)
                self._processing_tasks[task_id].progress = progress
                self._processing_tasks[task_id].processed_files = i + 1
                self._processing_tasks[task_id].message = f"Processed {i + 1}/{len(files)} files"

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
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e

    async def _validate_file(self, file: UploadFile) -> dict[str, Any]:
        """Validate a single uploaded file."""
        if not file.filename:
            return {"valid": False, "error": "Filename is required"}
        if not file.size or file.size == 0:
            return {"valid": False, "error": "File cannot be empty"}
        if file.size > self.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"File size ({file.size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)",
            }
        if file.content_type not in self.SUPPORTED_MIME_TYPES:
            return {
                "valid": False,
                "error": f"Unsupported file type: {file.content_type}. Supported types: {', '.join(self.SUPPORTED_MIME_TYPES)}",
            }

        file_path = Path(file.filename)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Unsupported file extension: {file_path.suffix}. Supported extensions: {', '.join(self.SUPPORTED_EXTENSIONS)}",
            }
        if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
            return {"valid": False, "error": "Filename contains invalid characters"}
        return {"valid": True}

    async def _save_file(self, file: UploadFile, task_id: str) -> Path:
        """Save uploaded file to temporary storage."""
        try:
            task_dir = self.upload_dir / task_id
            task_dir.mkdir(exist_ok=True)
            safe_filename = self._generate_safe_filename(file.filename)
            file_path = task_dir / safe_filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            if not file_path.exists():
                raise RuntimeError(f"File was not saved successfully to {file_path}")
            logger.info("File saved successfully", filename=file.filename, path=str(file_path), size=len(content))
            return file_path
        except Exception as e:
            logger.error("File save failed", filename=file.filename, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}") from e

    def _generate_safe_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        timestamp = int(time.time())
        name_parts = safe_name.rsplit(".", 1)
        if len(name_parts) == 2:
            safe_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            safe_name = f"{safe_name}_{timestamp}"
        return safe_name

    def get_processing_status(self, task_id: str) -> ProcessingStatus | None:
        return self._processing_tasks.get(task_id)

    def update_processing_status(self, task_id: str, status: str, progress: float, message: str | None = None) -> bool:
        if task_id not in self._processing_tasks:
            return False
        self._processing_tasks[task_id].status = status
        self._processing_tasks[task_id].progress = progress
        if message:
            self._processing_tasks[task_id].message = message
        self._processing_tasks[task_id].updated_at = datetime.now(timezone.utc)
        return True

    def cleanup_task_files(self, task_id: str) -> bool:
        try:
            task_dir = self.upload_dir / task_id
            if task_dir.exists():
                shutil.rmtree(task_dir)
                logger.info("Task files cleaned up", task_id=task_id)
            if task_id in self._processing_tasks:
                del self._processing_tasks[task_id]
            return True
        except Exception as e:
            logger.error("Cleanup failed", task_id=task_id, error=str(e))
            return False
