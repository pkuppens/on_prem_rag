"""Document processing service — COMPATIBILITY SHIM.

.. deprecated::
   Use ``backend.ingestion.application.ingest_service.IngestionService`` instead.
   This shim delegates to the Ingestion BC extraction (Phase 3).

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and implementation requirements.
"""

import asyncio
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.ingestion.application.ingest_service import IngestionService
from backend.ingestion.infrastructure.progress import ProgressEvent, progress_notifier
from backend.rag_pipeline.config.parameter_sets import RAGParams, get_param_set
from backend.rag_pipeline.core.vector_store import get_vector_store_manager
from backend.rag_pipeline.models.document_models import DocumentMetadata
from backend.rag_pipeline.utils.logging import StructuredLogger

logger = StructuredLogger(__name__)

# Global ingestion service instance (lazily initialized)
_ingestion_service: IngestionService | None = None


def _get_ingestion_service() -> IngestionService:
    """Get or create the shared IngestionService instance."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service


class DocumentProcessingService:
    """Compatibility shim — delegates to :class:`IngestionService`.

    Implements the document processing pipeline as specified in the architecture design.
    """

    def __init__(self) -> None:
        """Initialize the document processing service."""
        self._inner = _get_ingestion_service()
        self.vector_store_manager = get_vector_store_manager()
        logger.info("DocumentProcessingService initialized (shim → IngestionService)")

    async def process_documents(self, task_id: str, file_paths: list[Path], params_name: str = "default") -> dict[str, Any]:
        """Process multiple documents.

        Args:
            task_id: Task identifier for tracking.
            file_paths: List of file paths to process.
            params_name: Parameter set name for processing configuration.

        Returns:
            Dict with processing results and statistics.
        """
        logger.info("Starting document processing", task_id=task_id, file_count=len(file_paths))

        params = get_param_set(params_name)
        if not isinstance(params, RAGParams):
            raise ValueError(f"Invalid parameter set: {params_name}")

        results: dict[str, Any] = {
            "task_id": task_id,
            "total_files": len(file_paths),
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "total_records": 0,
            "errors": [],
        }

        try:
            for file_path in file_paths:
                try:
                    logger.info("Processing file", filename=file_path.name, task_id=task_id)
                    chunks_processed, records_stored = await self._process_single_document(
                        file_path, params, task_id
                    )
                    results["processed_files"] += 1
                    results["total_chunks"] += chunks_processed
                    results["total_records"] += records_stored
                    logger.info("File processed successfully", filename=file_path.name, chunks=chunks_processed, records=records_stored)
                except Exception as e:
                    results["failed_files"] += 1
                    error_info = {"filename": file_path.name, "error": str(e), "error_type": type(e).__name__}
                    results["errors"].append(error_info)
                    logger.error("File processing failed", **error_info)

            logger.info("Document processing completed", **results)
            return results

        except Exception as e:
            logger.error("Document processing failed", task_id=task_id, error=str(e))
            raise

    async def _process_single_document(
        self,
        file_path: Path,
        params: RAGParams,
        task_id: str,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> tuple[int, int]:
        """Process a single document.

        Args:
            file_path: Path to the document file.
            params: Processing parameters.
            task_id: Task identifier for tracking.
            progress_callback: Optional callback(filename, progress 0.0-1.0).

        Returns:
            Tuple of (chunks_processed, records_stored).
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        persist_dir = self.vector_store_manager.config.persist_directory
        collection_name = self.vector_store_manager.config.collection_name

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._inner.process_document_sync(
                file_path,
                embedding_model=params.embedding.model_name,
                persist_dir=persist_dir,
                collection_name=collection_name,
                chunk_size=params.chunking.chunk_size,
                chunk_overlap=params.chunking.chunk_overlap,
                progress_callback=progress_callback,
            ),
        )
        return result.chunks_processed, result.records_stored

    async def process_document_background(self, file_path: Path, filename: str, params_name: str) -> None:
        """Process a single document in the background, emitting real-time progress events.

        Args:
            file_path: Absolute path to the saved upload file.
            filename: Original filename (used as the progress event file_id).
            params_name: Name of the RAG parameter set to use.
        """
        await self._inner.process_document_background(file_path, filename, params_name)

    def create_document_metadata(self, filename: str, file_path: Path, processing_status: str = "pending") -> DocumentMetadata:
        """Create document metadata for a processed file.

        Args:
            filename: Original filename.
            file_path: Path to the file.
            processing_status: Current processing status.

        Returns:
            DocumentMetadata instance.
        """
        file_size = file_path.stat().st_size if file_path.exists() else 0
        content_type = self._get_content_type(filename)
        return DocumentMetadata(filename=filename, file_type=content_type, size=file_size, processing_status=processing_status)

    def _get_content_type(self, filename: str) -> str:
        import mimetypes

        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type
        ext = Path(filename).suffix.lower()
        type_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".csv": "text/csv",
            ".json": "application/json",
        }
        return type_map.get(ext, "application/octet-stream")
