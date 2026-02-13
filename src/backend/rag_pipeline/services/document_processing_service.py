"""Document processing service for handling document processing workflows.

This service implements the document processing functionality as specified in the
architecture design, including LlamaIndex integration and processing coordination.

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and implementation requirements.
"""

import asyncio
from pathlib import Path
from typing import Dict, List

from ..config.parameter_sets import RAGParams, get_param_set
from ..core.embeddings import process_document
from ..core.vector_store import ChromaVectorStoreManager, get_vector_store_manager_from_env
from ..models.document_models import DocumentMetadata
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class DocumentProcessingService:
    """Service for coordinating document processing workflows.

    Implements the document processing pipeline as specified in the architecture design.
    """

    def __init__(self):
        """Initialize the document processing service."""
        self.vector_store_manager = get_vector_store_manager_from_env()
        self.chroma_manager = self.vector_store_manager if isinstance(self.vector_store_manager, ChromaVectorStoreManager) else None

        logger.info("DocumentProcessingService initialized")

    async def process_documents(self, task_id: str, file_paths: List[Path], params_name: str = "default") -> Dict:
        """Process multiple documents using LlamaIndex.

        Args:
            task_id: Task identifier for tracking
            file_paths: List of file paths to process
            params_name: Parameter set name for processing configuration

        Returns:
            Dict with processing results and statistics
        """
        logger.info("Starting document processing", task_id=task_id, file_count=len(file_paths))

        # Get parameter set
        params = get_param_set(params_name)
        if not isinstance(params, RAGParams):
            raise ValueError(f"Invalid parameter set: {params_name}")

        results = {
            "task_id": task_id,
            "total_files": len(file_paths),
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "total_records": 0,
            "errors": [],
        }

        try:
            for _i, file_path in enumerate(file_paths):
                try:
                    logger.info("Processing file", filename=file_path.name, task_id=task_id)

                    # Process individual document
                    chunks_processed, records_stored = await self._process_single_document(file_path, params, task_id)

                    results["processed_files"] += 1
                    results["total_chunks"] += chunks_processed
                    results["total_records"] += records_stored

                    logger.info(
                        "File processed successfully", filename=file_path.name, chunks=chunks_processed, records=records_stored
                    )

                except Exception as e:
                    results["failed_files"] += 1
                    error_info = {"filename": file_path.name, "error": str(e), "error_type": type(e).__name__}
                    results["errors"].append(error_info)

                    logger.error("File processing failed", **error_info)

            logger.info("Document processing completed", task_id=task_id, **results)
            return results

        except Exception as e:
            logger.error("Document processing failed", task_id=task_id, error=str(e))
            raise

    async def _process_single_document(self, file_path: Path, params: RAGParams, task_id: str) -> tuple[int, int]:
        """Process a single document using LlamaIndex.

        Args:
            file_path: Path to the document file
            params: Processing parameters
            task_id: Task identifier for tracking

        Returns:
            Tuple of (chunks_processed, records_stored)
        """
        # Verify file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get vector store configuration
        persist_dir = self.chroma_manager.config.persist_directory if self.chroma_manager else str(file_path.parent)
        collection_name = self.chroma_manager.config.collection_name if self.chroma_manager else "documents"

        # Process document in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        chunks_processed, records_stored = await loop.run_in_executor(
            None,
            lambda: process_document(
                file_path,
                params.embedding.model_name,
                persist_dir=persist_dir,
                collection_name=collection_name,
                chunk_size=params.chunking.chunk_size,
                chunk_overlap=params.chunking.chunk_overlap,
                max_pages=None,
                deduplicate=False,
                progress_callback=None,  # Progress handled by upload service
            ),
        )

        return chunks_processed, records_stored

    def create_document_metadata(self, filename: str, file_path: Path, processing_status: str = "pending") -> DocumentMetadata:
        """Create document metadata for a processed file.

        Args:
            filename: Original filename
            file_path: Path to the file
            processing_status: Current processing status

        Returns:
            DocumentMetadata instance
        """
        # Get file information
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Determine content type
        content_type = self._get_content_type(filename)

        return DocumentMetadata(filename=filename, file_type=content_type, size=file_size, processing_status=processing_status)

    def _get_content_type(self, filename: str) -> str:
        """Get content type for a filename.

        Args:
            filename: Name of the file

        Returns:
            MIME content type
        """
        import mimetypes

        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type

        # Fallback based on extension
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
