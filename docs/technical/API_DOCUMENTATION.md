# API Documentation

This document provides comprehensive documentation for the RAG pipeline API endpoints.

## Document Management API

### Upload Document

**Endpoint**: `POST /api/documents/upload`

**Description**: Upload and process a document for the RAG pipeline.

**Parameters**:

- `file` (UploadFile, required): The document file to upload
- `params_name` (string, optional): Parameter set name (default: "default")

**Supported File Types**:

- PDF: `application/pdf`
- Text: `text/plain`
- Markdown: `text/markdown`
- Word Document: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Legacy Word: `application/msword`
- CSV: `text/csv`
- JSON: `application/json`

**File Size Limits**:

- Maximum file size: 100MB
- Minimum file size: 1 byte

**Request Validation**:

- Filename is required and cannot be empty
- Filename cannot contain path traversal characters (`..`, `/`, `\`)
- File content type must be supported
- File size must be within limits

**Response**:

```json
{
  "message": "Document uploaded successfully, processing started",
  "file_id": "filename.pdf",
  "status": "uploaded",
  "processing": "started"
}
```

**Error Responses**:

- `400 Bad Request`: Invalid file type, empty file, invalid filename
- `413 Payload Too Large`: File exceeds size limit
- `403 Forbidden`: Permission denied writing file
- `500 Internal Server Error`: Server error during processing

**Example**:

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@document.pdf" \
  -F "params_name=default"
```

### List Documents

**Endpoint**: `GET /api/documents/list`

**Description**: Get a list of uploaded document filenames.

**Response**:

```json
{
  "files": ["document1.pdf", "document2.docx", "document3.txt"]
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/documents/list"
```

### Serve Document File

**Endpoint**: `GET /api/documents/files/{filename}`

**Description**: Download or view an uploaded document file.

**Parameters**:

- `filename` (string, required): Name of the file to serve

**Response**: File content with appropriate content-type headers

**Error Responses**:

- `400 Bad Request`: Invalid filename
- `404 Not Found`: File not found
- `500 Internal Server Error`: Server error accessing file

**Example**:

```bash
curl -X GET "http://localhost:8000/api/documents/files/document.pdf" \
  -o downloaded_document.pdf
```

## Query API

### Ask Question

**Endpoint**: `POST /api/ask`

**Description**: Ask a question and get an answer using the RAG system.

**Request Body**:

```json
{
  "question": "What is the main topic of the document?",
  "params_name": "default",
  "top_k": 5
}
```

**Response**:

```json
{
  "answer": "The main topic is...",
  "sources": [
    {
      "content": "Relevant text excerpt...",
      "metadata": {
        "file_path": "document.pdf",
        "page_number": 1
      },
      "similarity": 0.85
    }
  ],
  "average_similarity": 0.82
}
```

### Query Documents

**Endpoint**: `POST /api/query`

**Description**: Search for relevant documents and text chunks.

**Request Body**:

```json
{
  "query": "search terms",
  "params_name": "default",
  "top_k": 10
}
```

**Response**:

```json
{
  "results": [
    {
      "content": "Matching text...",
      "metadata": {
        "file_path": "document.pdf",
        "page_number": 2
      },
      "similarity": 0.9
    }
  ]
}
```

## WebSocket Progress Updates

**Endpoint**: `WS /ws/upload-progress`

**Description**: Real-time progress updates for document processing.

**Message Format**:

```json
{
  "file_id": "document.pdf",
  "progress": 75,
  "message": "Generating embeddings (75%)"
}
```

**Progress Stages**:

- 5%: Upload started
- 10%: File saved
- 15-95%: Processing (loading, chunking, embedding, storing)
- 100%: Processing completed
- -1: Error occurred

## Error Handling

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File too large
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error description",
  "error_type": "ErrorClassName",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

## Authentication

Authentication is handled through JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

## CORS

CORS is configured to allow requests from `http://localhost:5173` (frontend development server).

## Health Check

**Endpoint**: `GET /health`

**Description**: Check API health status.

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0"
}
```

## Code Files

- [src/backend/rag_pipeline/api/documents.py](src/backend/rag_pipeline/api/documents.py) - Document management endpoints
- [src/backend/rag_pipeline/api/ask.py](src/backend/rag_pipeline/api/ask.py) - Question answering endpoints
- [src/backend/rag_pipeline/api/query.py](src/backend/rag_pipeline/api/query.py) - Document query endpoints
- [src/backend/rag_pipeline/api/app.py](src/backend/rag_pipeline/api/app.py) - FastAPI application setup
- [tests/test_upload_documents.py](tests/test_upload_documents.py) - API endpoint tests
- [tests/test_upload_progress.py](tests/test_upload_progress.py) - WebSocket progress tests
