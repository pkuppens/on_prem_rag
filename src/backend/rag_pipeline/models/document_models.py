"""Document-related data models for the RAG pipeline API.

This module contains Pydantic models for document processing, upload responses,
and query results as specified in the architecture design.

See docs/technical/STORY-002-document-processing-architecture.md for detailed
architecture specifications and data model requirements.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents.

    Tracks document information, processing status, and results.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    upload_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Upload timestamp")
    processing_status: str = Field(default="pending", description="Processing status: pending|processing|completed|error")
    chunk_count: Optional[int] = Field(None, description="Number of chunks created during processing")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class ProcessingProgress(BaseModel):
    """Progress tracking for document processing tasks.

    Provides real-time updates on processing status and progress.
    """

    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status: pending|processing|completed|error")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage (0.0 to 1.0)")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    total_files: int = Field(..., description="Total number of files in the task")
    processed_files: int = Field(..., description="Number of files processed so far")
    message: Optional[str] = Field(None, description="Current status message")
    error_details: Optional[Dict] = Field(None, description="Error details if status is error")


class UploadResponse(BaseModel):
    """Response model for file upload operations.

    Provides information about uploaded files and processing status.
    """

    task_id: str = Field(..., description="Unique task identifier for tracking progress")
    accepted_files: List[str] = Field(..., description="List of successfully uploaded files")
    rejected_files: List[Dict[str, str]] = Field(..., description="List of rejected files with reasons")
    message: str = Field(..., description="Overall upload status message")
    total_files: int = Field(..., description="Total number of files in the upload request")
    accepted_count: int = Field(..., description="Number of files successfully accepted")
    rejected_count: int = Field(..., description="Number of files rejected")


class DocumentResult(BaseModel):
    """Individual document result in query responses.

    Contains document information and relevance score.
    """

    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Document filename")
    content: str = Field(..., description="Relevant document content")
    score: float = Field(..., description="Relevance score")
    metadata: Optional[Dict] = Field(None, description="Additional document metadata")


class QueryResponse(BaseModel):
    """Response model for document queries.

    Contains query results and processing information.
    """

    query: str = Field(..., description="Original query string")
    results: List[DocumentResult] = Field(..., description="List of relevant documents")
    processing_time: float = Field(..., description="Query processing time in seconds")
    total_results: int = Field(..., description="Total number of results found")
    query_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique query identifier")


class FileValidationError(BaseModel):
    """Error details for file validation failures.

    Provides specific information about why a file was rejected.
    """

    filename: str = Field(..., description="Name of the rejected file")
    error_type: str = Field(..., description="Type of validation error")
    error_message: str = Field(..., description="Detailed error message")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="Detected content type")


class ProcessingStatus(BaseModel):
    """Status information for document processing tasks.

    Provides current status and progress information.
    """

    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    total_files: int = Field(..., description="Total files in task")
    processed_files: int = Field(..., description="Files processed so far")
    message: Optional[str] = Field(None, description="Status message")
    error_details: Optional[Dict] = Field(None, description="Error details if failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Task creation time")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update time")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
