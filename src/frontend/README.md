# Document Upload Frontend

This is the frontend application for the document upload feature. It provides a user-friendly interface for uploading and tracking document processing progress.

## Prerequisites

- Node.js 18 or higher
- npm 9 or higher
- Python 3.12 or higher
- uv package manager

## Installation

1. Install frontend dependencies:

   ```bash
   npm install
   ```

2. Install backend dependencies and scripts:
   ```bash
   uv pip install -e .
   ```

## Starting the Servers

You need to run both the backend and frontend servers. The project provides scripts to make this easy:

1. Start the backend server (in one terminal):

   ```bash
   uv run start-backend
   ```

   The backend will be available at http://localhost:8000

2. Start the frontend development server (in another terminal):
   ```bash
   uv run start-frontend
   ```
   The frontend will be available at http://localhost:5173

### Alternative: Manual Start

If you prefer to start the servers manually:

1. Backend:

   ```bash
   uvicorn rag_pipeline.file_ingestion:app --reload --host 0.0.0.0 --port 8000
   ```

2. Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Features

- Drag and drop file upload
- Support for PDF, DOCX, and TXT files
- Real-time upload progress tracking
- Material UI design
- Responsive layout
- Structured logging with timestamps and context

## Development

- The frontend is built with React, TypeScript, and Material UI
- The backend is built with FastAPI
- WebSocket is used for real-time progress updates
- Vite is used as the development server and build tool

## Logging

The application uses structured logging with:

- Timestamps (up to milliseconds)
- Log levels (info, warn, error, debug)
- File name, function name, and line number
- Additional context data in JSON format

Example log output:

```
[2024-02-14T10:30:45.123] INFO: WebSocket connection established (UploadPage.tsx:useEffect:20)
[2024-02-14T10:30:45.456] INFO: Starting file upload (UploadPage.tsx:handleFileSelect:55)
Data: {"filename": "example.pdf", "size": 1234567, "type": "application/pdf"}
```
