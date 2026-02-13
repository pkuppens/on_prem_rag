"""Tests for document upload handling.

As a developer I want document uploads to be processed correctly,
so I can integrate with the RAG pipeline.
Technical: Test DocumentUploadHandler class and file validation.
"""

from unittest.mock import MagicMock

import pytest

from tests.frontend.chat.conftest import get_mock_chainlit

mock_cl = get_mock_chainlit()

from frontend.chat.handlers.document_upload import (
    MAX_FILE_SIZE,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MIME_TYPES,
    DocumentUploadHandler,
    get_document_handler,
)
from frontend.chat.utils.session import UserRole, UserSession


class TestDocumentUploadHandler:
    """Tests for DocumentUploadHandler class."""

    @pytest.fixture
    def upload_handler(self):
        """Create an upload handler instance for testing."""
        return DocumentUploadHandler()

    @pytest.fixture
    def mock_pdf_element(self, tmp_path):
        """Create a mock PDF file element."""
        # Create a temporary file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"PDF content")

        element = MagicMock()
        element.name = "test.pdf"
        element.path = str(pdf_file)
        element.mime = "application/pdf"
        return element

    @pytest.fixture
    def mock_docx_element(self, tmp_path):
        """Create a mock DOCX file element."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"DOCX content")

        element = MagicMock()
        element.name = "test.docx"
        element.path = str(docx_file)
        element.mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return element

    @pytest.fixture
    def mock_session(self):
        """Create a mock user session."""
        return UserSession(user_id="test-user", role=UserRole.GP)

    def test_initialization(self, upload_handler):
        """As a developer I want handler to initialize correctly,
        so I can configure upload settings.
        Technical: Test DocumentUploadHandler initialization.
        """
        assert upload_handler._document_processor is None
        assert upload_handler._upload_dir.exists()

    def test_set_document_processor(self, upload_handler):
        """As a developer I want to set the document processor,
        so I can integrate with the RAG pipeline.
        Technical: Test set_document_processor method.
        """
        mock_processor = MagicMock()
        upload_handler.set_document_processor(mock_processor)

        assert upload_handler._document_processor == mock_processor

    def test_validate_file_valid_pdf(self, upload_handler, mock_pdf_element):
        """As a developer I want PDF files to be validated,
        so I can process valid documents.
        Technical: Test validation passes for valid PDF.
        """
        result = upload_handler._validate_file(mock_pdf_element)
        assert result is None  # None means valid

    def test_validate_file_valid_docx(self, upload_handler, mock_docx_element):
        """As a developer I want DOCX files to be validated,
        so I can process Word documents.
        Technical: Test validation passes for valid DOCX.
        """
        result = upload_handler._validate_file(mock_docx_element)
        assert result is None

    def test_validate_file_unsupported_extension(self, upload_handler):
        """As a developer I want unsupported files to be rejected,
        so I can only process compatible documents.
        Technical: Test validation fails for unsupported extensions.
        """
        element = MagicMock()
        element.name = "test.exe"
        element.path = None

        result = upload_handler._validate_file(element)
        assert result is not None
        assert "Unsupported file type" in result

    def test_validate_file_no_name(self, upload_handler):
        """As a developer I want files without names to be rejected,
        so I can handle malformed uploads.
        Technical: Test validation fails for nameless files.
        """
        element = MagicMock()
        element.name = None

        result = upload_handler._validate_file(element)
        assert result is not None
        assert "no name" in result.lower()

    def test_validate_file_too_large(self, upload_handler, tmp_path):
        """As a developer I want large files to be rejected,
        so I can prevent resource exhaustion.
        Technical: Test validation fails for oversized files.
        """
        # Create a file larger than MAX_FILE_SIZE
        large_file = tmp_path / "large.pdf"
        large_file.write_bytes(b"x" * (MAX_FILE_SIZE + 1))

        element = MagicMock()
        element.name = "large.pdf"
        element.path = str(large_file)

        result = upload_handler._validate_file(element)
        assert result is not None
        assert "too large" in result.lower()


class TestSupportedTypes:
    """Tests for supported file type constants."""

    def test_supported_extensions(self):
        """As a developer I want expected extensions to be supported,
        so I can process common document types.
        Technical: Test SUPPORTED_EXTENSIONS contains expected values.
        """
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS
        assert ".doc" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".md" in SUPPORTED_EXTENSIONS

    def test_supported_mime_types(self):
        """As a developer I want expected MIME types to be supported,
        so I can validate file content types.
        Technical: Test SUPPORTED_MIME_TYPES contains expected values.
        """
        assert "application/pdf" in SUPPORTED_MIME_TYPES
        assert "text/plain" in SUPPORTED_MIME_TYPES

    def test_max_file_size(self):
        """As a developer I want reasonable file size limits,
        so I can prevent resource exhaustion.
        Technical: Test MAX_FILE_SIZE is reasonable.
        """
        assert MAX_FILE_SIZE == 10 * 1024 * 1024  # 10 MB


class TestGetDocumentHandler:
    """Tests for get_document_handler singleton."""

    def test_get_document_handler_returns_singleton(self):
        """As a developer I want a singleton document handler,
        so I can share state across the application.
        Technical: Test get_document_handler returns same instance.
        """
        import frontend.chat.handlers.document_upload as module

        module._document_handler = None

        handler1 = get_document_handler()
        handler2 = get_document_handler()

        assert handler1 is handler2
