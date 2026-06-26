"""File upload service — COMPATIBILITY SHIM.

.. deprecated::
   Use ``backend.ingestion.application.file_upload_service.FileUploadService`` instead.
   This shim delegates to the Ingestion BC extraction (Phase 3).

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and implementation requirements.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from backend.ingestion.application.file_upload_service import (
    FileUploadService as NewFileUploadService,
)
from backend.rag_pipeline.models.document_models import (
    ProcessingStatus,
    UploadResponse,
)
from backend.rag_pipeline.utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class FileUploadService:
    """Compatibility shim — delegates to :class:`NewFileUploadService` (Ingestion BC).

    Implements the file upload system as specified in the architecture design.
    """

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self, upload_dir: Path | None = None) -> None:
        """Initialize with optional upload directory."""
        self._inner = NewFileUploadService(upload_dir)
        self.upload_dir = self._inner.upload_dir

    # Core upload operations — delegates to inner service
    async def upload_multiple_files(self, files: list[UploadFile], task_id: str | None = None) -> UploadResponse:
        return await self._inner.upload_multiple_files(files, task_id)

    def get_processing_status(self, task_id: str) -> ProcessingStatus | None:
        return self._inner.get_processing_status(task_id)

    def update_processing_status(self, task_id: str, status: str, progress: float, message: str | None = None) -> bool:
        return self._inner.update_processing_status(task_id, status, progress, message)

    def cleanup_task_files(self, task_id: str) -> bool:
        return self._inner.cleanup_task_files(task_id)

    async def _validate_file(self, file: UploadFile) -> dict[str, Any]:
        return await self._inner._validate_file(file)

    def _generate_safe_filename(self, filename: str) -> str:
        return self._inner._generate_safe_filename(filename)
