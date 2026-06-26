"""Ingestion application service — orchestrates the document processing pipeline.

Replaces ``DocumentProcessingService`` from the legacy rag_pipeline.
Coordinates document loading, chunking, embedding, and vector store storage
while emitting progress events via the ``ProgressNotifier``.

Uses domain port interfaces for all external dependencies:
- ``IDocumentLoader`` → ``IngestionDocument`` objects
- ``IChunker`` → ``Chunk`` objects
- ``EmbeddingProvider`` → embedding vectors
- ``IVectorStoreWrite`` → persistent storage
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.ingestion.domain.value_objects import IngestionResult
from backend.ingestion.infrastructure.chunking import chunk_documents
from backend.ingestion.infrastructure.document_loader import DocumentLoader
from backend.ingestion.infrastructure.embedding import generate_embeddings
from backend.ingestion.infrastructure.progress import ProgressEvent, progress_notifier
from backend.ingestion.infrastructure.vector_store import get_vector_store_write
from backend.llm_gateway.domain.interfaces import EmbeddingProvider
from backend.rag_pipeline.config.parameter_sets import RAGParams, get_param_set
from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.retrieval.domain.interfaces import IVectorStoreWrite

logger = StructuredLogger(__name__)


class IngestionService:
    """Application service for document ingestion.

    Orchestrates the full pipeline: load → chunk → embed → store.
    Emits ``ProgressEvent`` objects via the global ``progress_notifier``.
    """

    def __init__(
        self,
        document_loader: DocumentLoader | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: IVectorStoreWrite | None = None,
    ) -> None:
        """Initialize the ingestion service.

        Args:
            document_loader: Document loader instance. Defaults to new instance.
            embedding_provider: Embedding provider from LLM Gateway.
                If None, some operations will not work until set.
            vector_store: Vector store write adapter.
                If None, defaults from environment.
        """
        self._document_loader = document_loader or DocumentLoader()
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    @property
    def vector_store(self) -> IVectorStoreWrite:
        """Return the vector store write adapter, creating one if needed."""
        if self._vector_store is None:
            self._vector_store = get_vector_store_write()
        return self._vector_store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_document_sync(
        self,
        file_path: str | Path,
        model_name: str | None = None,
        *,
        persist_dir: str | Path | None = None,
        collection_name: str = "documents",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        max_pages: int | None = None,
        deduplicate: bool = True,
        embedding_model: str | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> IngestionResult:
        """Process a single document synchronously.

        This is the synchronous workhorse. Calls are expected to run in a
        thread pool executor when used from async endpoints.

        Args:
            file_path: Path to the document file.
            model_name: Deprecated, use embedding_model instead.
            persist_dir: Directory to store the vector database.
            collection_name: Name of the ChromaDB collection.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            max_pages: Maximum number of pages to process (None for all).
            deduplicate: Whether to deduplicate based on content hash.
            embedding_model: The embedding model name.
            progress_callback: Optional callback(filename, progress 0.0-1.0).

        Returns:
            IngestionResult with processing counts and status.
        """
        file_path = Path(file_path)
        emb_model = embedding_model or model_name or ""

        t_start = time.perf_counter()

        # ---- Step 1: Duplicate check ----
        if deduplicate and emb_model:
            from backend.ingestion.infrastructure.document_loader import DocumentLoader as DL

            loader = DL()
            file_content_hash = loader._compute_file_hash(file_path)  # type: ignore[attr-defined]
            if self.vector_store.has_document_with_file_hash(file_content_hash, embedding_model=emb_model):
                logger.info("Skipping duplicate document", filename=file_path.name)
                return IngestionResult(
                    was_duplicate=True,
                    file_name=file_path.name,
                    success=True,
                )

        if progress_callback:
            progress_callback(file_path.name, 0.0)

        # ---- Step 2: Load ----
        t_load = time.perf_counter()
        logger.info("Loading document", filename=file_path.name)
        documents, metadata = self._document_loader.load_document(file_path)
        logger.info(
            "Document loaded",
            filename=file_path.name,
            pages=len(documents),
            elapsed_ms=int((time.perf_counter() - t_load) * 1000),
        )

        if max_pages is not None and len(documents) > max_pages:
            documents = documents[:max_pages]

        if progress_callback:
            progress_callback(file_path.name, 0.1)

        # ---- Step 3: Chunk ----
        t_chunk = time.perf_counter()

        def _chunk_progress(page_num: int, total_pages: int) -> None:
            if progress_callback:
                page_progress = page_num / total_pages if total_pages > 0 else 1.0
                overall_progress = 0.1 + (page_progress * 0.4)
                progress_callback(file_path.name, overall_progress)

        chunks = chunk_documents(
            documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            source_path=file_path,
            enable_text_cleaning=True,
            min_chunk_length=10,
            progress_callback=_chunk_progress,
        )

        logger.info(
            "Chunking completed",
            filename=file_path.name,
            chunks=len(chunks),
            elapsed_ms=int((time.perf_counter() - t_chunk) * 1000),
        )

        if progress_callback:
            progress_callback(file_path.name, 0.5)

        # ---- Step 4: Embed ----
        t_embed = time.perf_counter()

        def _embed_progress(embed_progress: float) -> None:
            if progress_callback:
                total_progress = 0.5 + (embed_progress * 0.4)
                progress_callback(file_path.name, total_progress)

        if self._embedding_provider:
            embeddings = generate_embeddings(
                chunks,
                self._embedding_provider,
                progress_callback=_embed_progress,
            )
        else:
            logger.warning("No embedding provider configured — skipping embedding generation")
            embeddings = []

        logger.info(
            "Embedding completed",
            filename=file_path.name,
            embeddings=len(embeddings),
            elapsed_ms=int((time.perf_counter() - t_embed) * 1000),
        )

        if progress_callback:
            progress_callback(file_path.name, 0.9)

        # ---- Step 5: Store ----
        if embeddings and chunks:
            file_content_hash = metadata.get("file_hash", "")
            ids: list[str] = []
            metadatas_list: list[dict[str, Any]] = []
            for i, chunk in enumerate(chunks):
                if i >= len(embeddings):
                    break
                doc_id = chunk.document_id or f"chunk_{i}"
                ids.append(doc_id)
                meta: dict[str, Any] = {
                    "text": chunk.text,
                    "document_name": chunk.document_name,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "source": chunk.source,
                    "page_number": chunk.page_number or "unknown",
                    "page_label": chunk.page_label or "unknown",
                    "content_hash": chunk.content_hash,
                }
                if file_content_hash:
                    meta["file_content_hash"] = file_content_hash
                if emb_model:
                    meta["embedding_model"] = emb_model
                metadatas_list.append(meta)
            self.vector_store.add_embeddings(ids, embeddings[:len(ids)], metadatas_list)
            records_stored = len(ids)
        else:
            records_stored = 0

        logger.info(
            "Ingestion completed",
            filename=file_path.name,
            chunks=len(chunks),
            records=records_stored,
            elapsed_ms=int((time.perf_counter() - t_start) * 1000),
        )

        if progress_callback:
            progress_callback(file_path.name, 1.0)

        return IngestionResult(
            chunks_processed=len(chunks),
            records_stored=records_stored,
            file_name=file_path.name,
            success=True,
        )

    # ------------------------------------------------------------------
    # Async workflow
    # ------------------------------------------------------------------

    async def process_document_background(
        self,
        file_path: Path,
        filename: str,
        params_name: str = "default",
    ) -> None:
        """Process a single document in the background, emitting real-time progress.

        Args:
            file_path: Absolute path to the saved upload file.
            filename: Original filename (used as the progress event file_id).
            params_name: Name of the RAG parameter set to use.
        """
        progress_events: list[dict] = []

        def _progress_callback(cb_filename: str, progress: float) -> None:
            upload_progress = int(15 + (progress * 85))
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
            progress_events.append({"filename": cb_filename, "progress": upload_progress, "message": message})

        async def _stream_progress() -> None:
            try:
                while True:
                    for event_data in list(progress_events):
                        progress_events.remove(event_data)
                        await progress_notifier.notify(
                            ProgressEvent(
                                file_id=event_data["filename"],
                                progress=event_data["progress"],
                                message=event_data["message"],
                            )
                        )
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                raise

        try:
            t_ingest = time.perf_counter()
            logger.info("Background ingestion started", filename=filename)

            if not file_path.exists():
                await progress_notifier.notify(ProgressEvent(filename, -1, f"File not found: {filename}"))
                return

            params = get_param_set(params_name)
            if not isinstance(params, RAGParams):
                await progress_notifier.notify(ProgressEvent(filename, -1, f"Invalid parameter set: {params_name}"))
                return

            await progress_notifier.notify(ProgressEvent(filename, 15, "Processing started"))
            await asyncio.sleep(0.01)

            # Delete existing chunks for this document before re-ingesting
            t_del = time.perf_counter()
            deleted = self.vector_store.delete_by_document_name(filename)
            logger.info(
                "Deleted existing chunks",
                filename=filename,
                deleted=deleted,
                elapsed_ms=int((time.perf_counter() - t_del) * 1000),
            )

            progress_task = asyncio.create_task(_stream_progress())
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.process_document_sync(
                        file_path,
                        embedding_model=params.embedding.model_name,
                        chunk_size=params.chunking.chunk_size,
                        chunk_overlap=params.chunking.chunk_overlap,
                        progress_callback=_progress_callback,
                    ),
                )
                logger.info(
                    "Background ingestion completed",
                    filename=filename,
                    elapsed_ms=int((time.perf_counter() - t_ingest) * 1000),
                    chunks_processed=result.chunks_processed,
                    records_stored=result.records_stored,
                )
            finally:
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass

            # Flush remaining events
            for event_data in progress_events:
                await progress_notifier.notify(
                    ProgressEvent(
                        file_id=event_data["filename"],
                        progress=event_data["progress"],
                        message=event_data["message"],
                    )
                )

        except Exception as e:
            logger.error("Error during background processing", filename=filename, error=str(e))
            await progress_notifier.notify(ProgressEvent(filename, -1, f"Processing failed: {str(e)}"))
