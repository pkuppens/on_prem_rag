"""Tests for enhanced documents API endpoints.

This module tests the enhanced document upload and processing functionality
as specified in TASK-006B, including multiple file upload support, validation,
and status tracking.

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and test requirements.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app
from src.backend.rag_pipeline.services.file_upload_service import FileUploadService


class MockUploadFile:
    """Mock UploadFile class for testing file validation functionality.

    This class simulates the FastAPI UploadFile interface for testing purposes.
    """

    def __init__(self, filename: str, size: int, content_type: str):
        self.filename = filename
        self.size = size
        self.content_type = content_type


class TestEnhancedDocumentsAPI:
    """Test suite for enhanced documents API endpoints.

    Tests the file upload functionality, validation, and processing status
    as specified in the architecture design.
    """

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        return TestClient(app)

    @pytest.fixture
    def sample_files(self):
        """Create sample files for testing."""
        files = []

        # Create temporary files with different types
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test text file.")
            files.append(Path(f.name))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Markdown\n\nThis is a test markdown file.")
            files.append(Path(f.name))

        yield files

        # Cleanup
        for file_path in files:
            if file_path.exists():
                file_path.unlink()

    def test_upload_single_valid_file(self, client, sample_files):
        """Test uploading a single valid file.

        As a user I want to upload a single document file, so I can process it for querying.
        Technical: The API should accept valid file types and return proper response.
        Validation: Upload a text file and verify response format and status.
        """
        with open(sample_files[0], "rb") as f:
            response = client.post("/api/v1/upload", files={"files": (sample_files[0].name, f, "text/plain")})

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "task_id" in data
        assert "accepted_files" in data
        assert "rejected_files" in data
        assert "message" in data
        assert "total_files" in data
        assert "accepted_count" in data
        assert "rejected_count" in data

        # Verify upload was successful
        assert data["accepted_count"] == 1
        assert data["rejected_count"] == 0
        assert data["total_files"] == 1
        assert sample_files[0].name in data["accepted_files"]

    def test_upload_multiple_valid_files(self, client, sample_files):
        """Test uploading multiple valid files.

        As a user I want to upload multiple documents at once, so I can process them efficiently.
        Technical: The API should handle multiple file uploads and validate each file.
        Validation: Upload multiple files and verify all are accepted.
        """
        files_data = []
        for file_path in sample_files:
            # Read file content and create file-like object
            with open(file_path, "rb") as f:
                content = f.read()
            files_data.append(("files", (file_path.name, content, "text/plain")))

        response = client.post("/api/v1/upload", files=files_data)

        assert response.status_code == 200
        data = response.json()

        # Verify all files were accepted
        assert data["accepted_count"] == len(sample_files)
        assert data["rejected_count"] == 0
        assert data["total_files"] == len(sample_files)

        # Verify all filenames are in accepted files
        for file_path in sample_files:
            assert file_path.name in data["accepted_files"]

    def test_upload_unsupported_file_type(self, client):
        """Test uploading unsupported file type.

        As a user I want clear error messages when uploading unsupported files, so I know what to fix.
        Technical: The API should reject unsupported file types with clear error messages.
        Validation: Upload an unsupported file type and verify rejection with proper error.
        """
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write("This is an unsupported file type.")
            file_path = Path(f.name)

        try:
            with open(file_path, "rb") as f:
                response = client.post("/api/v1/upload", files={"files": (file_path.name, f, "application/octet-stream")})

            assert response.status_code == 200  # Upload endpoint returns 200 with rejection details
            data = response.json()

            # Verify file was rejected
            assert data["accepted_count"] == 0
            assert data["rejected_count"] == 1
            assert len(data["rejected_files"]) == 1

            # Verify error message
            rejected_file = data["rejected_files"][0]
            assert "error" in rejected_file
            assert "unsupported" in rejected_file["error"].lower()

        finally:
            if file_path.exists():
                file_path.unlink()

    def test_upload_empty_file(self, client):
        """Test uploading empty file.

        As a user I want clear error messages when uploading empty files, so I know what to fix.
        Technical: The API should reject empty files with appropriate error messages.
        Validation: Upload an empty file and verify rejection with proper error.
        """
        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            pass  # Empty file
            file_path = Path(f.name)

        try:
            with open(file_path, "rb") as f:
                response = client.post("/api/v1/upload", files={"files": (file_path.name, f, "text/plain")})

            assert response.status_code == 200
            data = response.json()

            # Verify file was rejected
            assert data["accepted_count"] == 0
            assert data["rejected_count"] == 1

            # Verify error message
            rejected_file = data["rejected_files"][0]
            assert "error" in rejected_file
            assert "empty" in rejected_file["error"].lower()

        finally:
            if file_path.exists():
                file_path.unlink()

    def test_upload_no_files(self, client):
        """Test uploading with no files.

        As a user I want clear error messages when not providing files, so I know what to fix.
        Technical: The API should reject requests with no files.
        Validation: Send request without files and verify proper error response.
        """
        response = client.post("/api/v1/upload", files={})

        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        data = response.json()
        assert "detail" in data
        # Check that the error is about missing files
        assert any("files" in str(error).lower() for error in data["detail"])

    def test_upload_too_many_files(self, client):
        """Test uploading too many files.

        As a user I want clear error messages when uploading too many files, so I know the limits.
        Technical: The API should enforce reasonable limits on number of files per upload.
        Validation: Upload more than the maximum allowed files and verify rejection.
        """
        # Create more than 10 files (the limit)
        files_data = []
        temp_files = []

        try:
            for i in range(11):  # 11 files, exceeding limit of 10
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write(f"This is test file {i}.")
                    temp_files.append(Path(f.name))

                # Read file content and create file-like object
                with open(temp_files[-1], "rb") as f:
                    content = f.read()
                files_data.append(("files", (temp_files[-1].name, content, "text/plain")))

            response = client.post("/api/v1/upload", files=files_data)

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "maximum" in data["detail"].lower()

        finally:
            # Cleanup
            for file_path in temp_files:
                if file_path.exists():
                    file_path.unlink()

    def test_get_processing_status(self, client, sample_files):
        """Test getting processing status for a task.

        As a user I want to check the status of my document processing, so I know when it's complete.
        Technical: The API should provide real-time status information for processing tasks.
        Validation: Upload a file, get task ID, and check status endpoint.
        """
        # First upload a file to get a task ID
        with open(sample_files[0], "rb") as f:
            upload_response = client.post("/api/v1/upload", files={"files": (sample_files[0].name, f, "text/plain")})

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        task_id = upload_data["task_id"]

        # Get processing status
        status_response = client.get(f"/api/v1/status/{task_id}")

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify status structure
        assert "task_id" in status_data
        assert "status" in status_data
        assert "progress" in status_data
        assert "total_files" in status_data
        assert "processed_files" in status_data
        assert "message" in status_data

        # Verify task ID matches
        assert status_data["task_id"] == task_id

    def test_get_processing_status_nonexistent_task(self, client):
        """Test getting status for non-existent task.

        As a user I want clear error messages when checking status of non-existent tasks, so I know what went wrong.
        Technical: The API should return 404 for non-existent task IDs.
        Validation: Request status for invalid task ID and verify 404 response.
        """
        response = client.get("/api/v1/status/nonexistent-task-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_list_documents(self, client):
        """Test listing processed documents.

        As a user I want to see all my processed documents, so I can manage them.
        Technical: The API should provide a list of processed documents.
        Validation: Call list endpoint and verify response structure.
        """
        response = client.get("/api/v1/list")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "documents" in data
        assert "total_count" in data
        assert "message" in data

        # Should be a list
        assert isinstance(data["documents"], list)
        assert isinstance(data["total_count"], int)


class TestFileUploadService:
    """Test suite for FileUploadService.

    Tests the file upload service functionality including validation,
    file handling, and status tracking.
    """

    @pytest.fixture
    def upload_service(self, tmp_path):
        """Create FileUploadService with temporary directory."""
        return FileUploadService(upload_dir=tmp_path)

    def test_file_validation_valid_file(self, upload_service):
        """Test validation of valid file.

        As a user I want valid files to be accepted, so I can process my documents.
        Technical: The service should validate file types, sizes, and names correctly.
        Validation: Create valid file and verify validation passes.
        """

        # Create a mock UploadFile
        mock_file = MockUploadFile("test.txt", 1024, "text/plain")

        # Test validation
        result = asyncio.run(upload_service._validate_file(mock_file))

        assert result["valid"] is True

    def test_file_validation_invalid_type(self, upload_service):
        """Test validation of invalid file type.

        As a user I want invalid file types to be rejected with clear messages, so I know what to fix.
        Technical: The service should reject unsupported file types.
        Validation: Create file with unsupported type and verify rejection.
        """

        mock_file = MockUploadFile("test.xyz", 1024, "application/octet-stream")

        result = asyncio.run(upload_service._validate_file(mock_file))

        assert result["valid"] is False
        assert "error" in result
        assert "unsupported" in result["error"].lower()

    def test_file_validation_oversized_file(self, upload_service):
        """Test validation of oversized file.

        As a user I want oversized files to be rejected with clear messages, so I know the limits.
        Technical: The service should enforce file size limits.
        Validation: Create oversized file and verify rejection.
        """

        # Create file larger than MAX_FILE_SIZE (100MB)
        mock_file = MockUploadFile("test.txt", 200 * 1024 * 1024, "text/plain")

        result = asyncio.run(upload_service._validate_file(mock_file))

        assert result["valid"] is False
        assert "error" in result
        assert "size" in result["error"].lower()

    def test_generate_safe_filename(self, upload_service):
        """Test safe filename generation.

        As a user I want filenames to be handled safely, so there are no security issues.
        Technical: The service should generate safe filenames for storage.
        Validation: Test filename generation with various inputs.
        """
        # Test normal filename
        safe_name = upload_service._generate_safe_filename("test.txt")
        assert safe_name.endswith(".txt")
        assert "test" in safe_name

        # Test filename with path components
        safe_name = upload_service._generate_safe_filename("../test.txt")
        assert ".." not in safe_name
        assert safe_name.endswith(".txt")

        # Test filename without extension
        safe_name = upload_service._generate_safe_filename("test")
        assert "test" in safe_name
