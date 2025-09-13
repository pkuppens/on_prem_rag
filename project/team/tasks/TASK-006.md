# Task: Implement File Ingestion Module

**ID**: TASK-006  
**Story**: [STORY-002: Document Processing Pipeline](../stories/STORY-002.md)  
**Assignee**: Backend Engineer  
**Status**: In Progress
**Effort**: 8 hours  
**Created**: 2025-05-31  
**Updated**: 2025-09-11

## Description

Create a robust FastAPI module that handles file uploads and processes PDF, DOCX, MD, and TXT files.
The module should implement idempotent document processing with duplicate detection and tracking, including comprehensive
validation, preprocessing, error handling, and logging.

## Running the Servers

The project uses `uv` for Python package management and script execution. The backend server can be started using a project script, while the frontend needs to be started separately as it's a Node.js application.

### Backend Server

Start the backend server using the project script:

```bash
uv run start-backend
```

This starts the FastAPI server at http://localhost:8000

### Frontend Development Server

The frontend is a separate Node.js/TypeScript project. To start it:

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies (first time only):

   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   This starts the Vite development server at http://localhost:5173

### Adding New Backend Scripts

To add new scripts to the project:

1. Add them to the `[project.scripts]` section in `pyproject.toml`:

   ```toml
   [project.scripts]
   script-name = "command to run"
   ```

2. After adding new scripts, you need to reinstall the project in development mode:

   ```bash
   uv pip install -e .
   ```

3. The new scripts can then be run using:
   ```bash
   uv run script-name
   ```

Note: Scripts are installed in your Python environment, so they need to be reinstalled when modified.

## Implementation Hints

- [ ] Set up FastAPI with required packages
  ```bash
  uv add fastapi
  uv add python-multipart
  uv add llama-index[...]
  uv add pypdf
  uv add python-docx
  uv add markdown
  ```
- [ ] Create FastAPI endpoints:
  ```python
  @app.post("/api/documents/upload")
  async def upload_document(file: UploadFile):
      # Handle file upload
      # 1. Log the UploadFile metadata, like name, size, type
      # 2. Set processing status to processing
      # 3. 'work' placeholder of 5 second delay in initial version, optionally every second 20% progress increments
      # 4. Set processing status to complete
  ```
- [ ] Implement WebSocket endpoint for progress updates:
  ```python
  @app.websocket("/ws/upload-progress")
  async def upload_progress(websocket: WebSocket):
      # Send real-time progress updates
      # 1. Log the progress - status/percentage - does this need payload?!
  ```
- [ ] Implement document fingerprinting for duplicate detection
- [ ] Create a preprocessing pipeline for each file type
- [ ] Set up structured logging with appropriate log levels
- [ ] Create an exploratory notebook to validate the implementation

## Acceptance Criteria

- [ ] FastAPI endpoint successfully handles file uploads
- [ ] WebSocket connection provides real-time progress updates
- [ ] Function `load_document(path)` returns a list of `Document` objects for each supported format
- [x] Document loading is idempotent with duplicate detection per parameter set
- [ ] Comprehensive error handling for:
  - Unsupported formats
  - Corrupted files
  - Permission issues
  - File size limits
- [ ] Structured logging implemented for all operations
- [ ] File validation and preprocessing pipeline in place
- [ ] Unit tests covering all file types and error cases
- [ ] API documentation with OpenAPI/Swagger

## Dependencies

- **Blocked by**: TASK-001 (project scaffolding)
- **Blocks**: TASK-007, TASK-008

---

**Implementer**: Backend Engineer  
**Reviewer**: Lead Developer  
**Target Completion**: TBD
