"""Document upload handling for Chainlit UI."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import chainlit as cl

from frontend.chat.utils.session import SessionManager, UserRole

logger = logging.getLogger(__name__)

# Supported file types
SUPPORTED_MIME_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "text/plain": "TXT",
    "text/markdown": "Markdown",
    "application/msword": "DOC",
}

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentUploadHandler:
    """Handles document uploads and integration with the RAG pipeline."""

    def __init__(self):
        self._document_processor = None
        self._upload_dir = Path(tempfile.gettempdir()) / "chainlit_uploads"
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def set_document_processor(self, processor: Any) -> None:
        """Set the document processor instance."""
        self._document_processor = processor

    async def handle_uploads(self, elements: list[Any], message_content: str) -> None:
        """Handle file uploads attached to a message.

        Validates files, processes them through the RAG pipeline,
        and provides feedback to the user.
        """
        session = SessionManager.get_session()
        if not session:
            await cl.Message(content="Session not found. Please log in again.").send()
            return

        # Separate valid and invalid files
        valid_files: list[Any] = []
        invalid_files: list[tuple[str, str]] = []

        for element in elements:
            validation_result = self._validate_file(element)
            if validation_result is None:
                valid_files.append(element)
            else:
                invalid_files.append((getattr(element, "name", "Unknown"), validation_result))

        # Report invalid files
        if invalid_files:
            invalid_msg = "The following files could not be processed:\n"
            for name, reason in invalid_files:
                invalid_msg += f"- {name}: {reason}\n"
            await cl.Message(content=invalid_msg).send()

        if not valid_files:
            return

        # Process valid files
        await self._process_files(valid_files, message_content, session.role)

    def _validate_file(self, element: Any) -> str | None:
        """Validate a file for upload.

        Returns None if valid, or an error message if invalid.
        """
        # Check file name and extension
        file_name = getattr(element, "name", None)
        if not file_name:
            return "File has no name"

        extension = Path(file_name).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return f"Unsupported file type '{extension}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"

        # Check MIME type if available
        mime_type = getattr(element, "mime", None)
        if mime_type and mime_type not in SUPPORTED_MIME_TYPES:
            # Allow if extension is valid (MIME type might not be set correctly)
            logger.warning(f"Unknown MIME type '{mime_type}' for file '{file_name}', allowing based on extension")

        # Check file size
        file_path = getattr(element, "path", None)
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                return f"File too large ({file_size / 1024 / 1024:.1f} MB). Maximum: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"

        return None

    async def _process_files(self, files: list[Any], query: str, role: UserRole) -> None:
        """Process uploaded files through the RAG pipeline."""
        # Create a step for file processing
        async with cl.Step(name="Document Processing", type="run") as parent_step:
            parent_step.input = f"Processing {len(files)} file(s)"

            processed_files: list[dict[str, Any]] = []
            failed_files: list[tuple[str, str]] = []

            for file_element in files:
                file_name = getattr(file_element, "name", "unknown")
                async with cl.Step(name=f"Processing: {file_name}", type="tool", parent_id=parent_step.id) as step:
                    step.input = file_name

                    try:
                        result = await self._process_single_file(file_element, role)
                        processed_files.append(result)
                        step.output = f"Successfully processed: {result.get('chunks', 0)} chunks created"
                    except Exception as e:
                        logger.exception(f"Error processing file {file_name}")
                        failed_files.append((file_name, str(e)))
                        step.output = f"Failed: {e}"

            # Report results
            await self._report_processing_results(processed_files, failed_files, query, parent_step)

    async def _process_single_file(self, file_element: Any, role: UserRole) -> dict[str, Any]:
        """Process a single file through the RAG pipeline."""
        file_name = getattr(file_element, "name", "unknown")
        file_path = getattr(file_element, "path", None)

        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"File path not found for {file_name}")

        result = {
            "name": file_name,
            "path": file_path,
            "chunks": 0,
            "status": "pending",
        }

        if self._document_processor:
            # Use the actual document processor
            try:
                # Process through RAG pipeline
                processing_result = await self._document_processor.process_document(
                    file_path, metadata={"role": role.value, "filename": file_name}
                )

                result["chunks"] = processing_result.get("chunk_count", 0)
                result["document_id"] = processing_result.get("document_id")
                result["status"] = "processed"
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                raise
        else:
            # Fallback - just record that we received the file
            result["status"] = "received"
            result["chunks"] = 0
            logger.warning(f"Document processor not configured, file {file_name} not processed")

        return result

    async def _report_processing_results(
        self, processed: list[dict[str, Any]], failed: list[tuple[str, str]], query: str, parent_step: Any
    ) -> None:
        """Report the results of file processing to the user."""
        # Build summary
        summary_parts = []

        if processed:
            total_chunks = sum(f.get("chunks", 0) for f in processed)
            file_names = [f["name"] for f in processed]
            summary_parts.append(f"Successfully processed {len(processed)} file(s): {', '.join(file_names)}")
            if total_chunks > 0:
                summary_parts.append(f"Created {total_chunks} document chunks for search.")

        if failed:
            summary_parts.append(f"\nFailed to process {len(failed)} file(s):")
            for name, error in failed:
                summary_parts.append(f"  - {name}: {error}")

        summary = "\n".join(summary_parts)
        parent_step.output = summary

        # Send summary message
        await cl.Message(content=summary).send()

        # If there was a query with the files, process it
        if query and processed:
            await cl.Message(content=f"\nNow processing your query about the uploaded documents: '{query}'").send()

            # Store uploaded file info in session for context
            session = SessionManager.get_session()
            if session:
                session.metadata["uploaded_files"] = processed


# Global document upload handler instance
_document_handler: DocumentUploadHandler | None = None


def get_document_handler() -> DocumentUploadHandler:
    """Get the global document upload handler instance."""
    global _document_handler
    if _document_handler is None:
        _document_handler = DocumentUploadHandler()
    return _document_handler
