# Project Structure

## Overview

This document describes the complete project structure for better organization and maintainability, including data directories and their purposes.

## Directory Structure

```
.
├── src/                      # Source code root
│   ├── backend/             # Backend application code
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core business logic
│   │   ├── models/         # Data models
│   │   ├── services/       # Business services
│   │   └── rag_pipeline/   # RAG pipeline components
│   │       └── utils/      # Utilities including directory_utils.py
│   ├── frontend/           # Frontend application code (React)
│   │   ├── src/           # Frontend source code
│   │   ├── public/        # Static assets
│   │   ├── package.json   # Frontend dependencies
│   │   └── node_modules/  # Frontend node modules (gitignored)
│   ├── auth_service/       # Authentication microservice
├── data/ (gitignored)       # Main data directory - contains all runtime data
│   ├── chroma/             # ChromaDB vector database files
│   │   ├── chroma.sqlite3  # ChromaDB main database file
│   │   └── [collections]/  # Vector collection storage directories
│   ├── database/           # Application databases
│   │   └── auth.db         # Authentication database (SQLite)
│   ├── cache/              # System cache directory
│   │   └── huggingface/   # Hugging Face model cache (created dynamically)
│   ├── chunks/             # Document chunk storage (empty - planned feature)
│   └── uploads/            # User uploaded files for processing
├── tests/                   # Test files
│   ├── core/               # Core test modules
│   ├── test_data/          # Test data files (version controlled)
│   │   ├── *.pdf          # PDF test documents for RAG testing
│   │   └── learninglangchain.pdf  # Specific test file (gitignored for copyright)
│   ├── test_temp/ (gitignored)     # Temporary test files
├── docs/                    # Technical documentation
├── project/                 # Project management documentation (SAFe structure)
├── scripts/                 # Utility and deployment scripts
├── notebooks/               # Jupyter notebooks for experimentation
├── docker/                  # Docker-related files
│   ├── backend/            # Backend Dockerfile and configs
│   └── frontend/           # Frontend Dockerfile and configs
├── .devcontainer/           # VS Code development container configuration
├── .github/                 # GitHub workflows and templates
├── .vscode/ (partial gitignore)     # VS Code settings (some files tracked)
├── pyproject.toml           # Python project configuration
├── docker-compose.yml       # Docker Compose configuration
├── uv.lock                  # UV package manager lock file
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── env.example             # Environment variables template
├── CURRENT_WORK.md (gitignored)     # Active work tracking
├── NEXT_DEMO.md (gitignored)        # Demo preparation notes
└── SCRATCH.md (gitignored)          # Temporary development notes
```

## Data Directory Details

### `/data/` (gitignored)

Main data directory containing all runtime application data. This directory is completely ignored by git to prevent sensitive data from being committed.

- **`chroma/`**: ChromaDB vector database storage

  - Contains vector embeddings and metadata for document retrieval
  - Includes SQLite database files and collection directories
  - Created and managed by ChromaDB automatically

- **`database/`**: Application database files

  - `auth.db`: SQLite database for user authentication
  - Additional application databases as needed

- **`cache/`**: System-level cache directory

  - `huggingface/`: Downloaded model files and tokenizers
  - Subdirectories created automatically by embedding models
  - Helps avoid re-downloading large model files

- **`chunks/`**: Document chunk storage (planned feature)

  - Will contain processed document chunks for optimization
  - Currently empty - planned for future implementation

- **`uploads/`**: User uploaded files for processing
  - Temporary storage for files being processed through RAG pipeline
  - Files are processed and then can be safely removed

### `/tests/test_data/` (partially tracked)

Test data directory with specific git tracking rules:

- Directory structure is tracked
- Most PDF files are tracked for testing
- `learninglangchain.pdf` is gitignored due to copyright concerns
- Contains academic papers and test documents for RAG pipeline validation

### Directory Utilities Integration

The project includes `src/backend/rag_pipeline/utils/directory_utils.py` which provides:

- **`get_project_root()`**: Returns project root directory
- **`get_data_dir()`**: Returns main data directory path
- **`get_uploaded_files_dir()`**: Returns data/uploads directory
- **`get_chunks_dir()`**: Returns data/chunks directory
- **`get_database_dir()`**: Returns data/database directory
- **`get_cache_dir()`**: Returns data/cache directory
- **`get_test_data_dir()`**: Returns tests/test_data directory
- **Validation functions**: Ensure directories exist and are accessible

These utility functions align with the actual directory structure and provide a single source of truth for directory paths throughout the application.

## Benefits

1. **Clear Data Separation**: All runtime data is isolated in the `/data/` directory
2. **Privacy Protection**: Complete gitignore of sensitive data directories
3. **Development Safety**: Test data is managed separately with selective tracking
4. **Cache Management**: Organized cache structure prevents redundant downloads
5. **Maintainable Structure**: Directory utilities provide consistent path management
6. **Deployment Ready**: Clear separation between code and data for containerization

## Git Ignore Strategy

The project uses a comprehensive `.gitignore` strategy:

- **Complete Data Protection**: Entire `/data/` directory is ignored
- **Selective Test Data**: Test data directory structure is tracked, sensitive files ignored
- **Cache Management**: All cache directories are ignored
- **Development Files**: Working documentation files are ignored
- **Build Artifacts**: All build and dependency artifacts are ignored

## Development Workflow

1. **Backend Development**: Work in `src/backend/` with automatic data directory creation
2. **Frontend Development**: Use `src/frontend/` or `frontend/` depending on setup
3. **Data Management**: All data automatically stored in `/data/` via directory utilities
4. **Testing**: Use `tests/test_data/` for fixed test files, `tests/test_temp/` for dynamic tests
5. **Documentation**: Technical docs in `docs/`, project management in `project/`
6. **Deployment**: Docker configurations handle data volume mounting appropriately

## Directory Creation

Directories are created automatically by the application when needed:

- Data directories are created by `directory_utils.py` functions
- Cache directories are created by embedding model initialization
- Test temporary directories are created by pytest fixtures
- Upload directories are created when first file is uploaded
