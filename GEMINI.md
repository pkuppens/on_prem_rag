# Gemini Workspace Context

This document provides comprehensive context for the Gemini AI assistant to understand the on-premises RAG system project, its architecture, development practices, and current implementation status.

## Project Overview

This project delivers an **on-premises Retrieval-Augmented Generation (RAG) system** that enables organizations to leverage Large Language Models (LLMs) for document analysis and database querying while maintaining complete data sovereignty and regulatory compliance. The system is designed to be fully operational in an offline environment, eliminating cloud dependencies and addressing enterprise privacy and security concerns.

### Core Business Value

- **Data Privacy & Compliance**: Zero cloud dependencies ensure sensitive information never leaves your infrastructure
- **Cost Control**: Eliminate per-query API costs and unpredictable cloud billing
- **Regulatory Compliance**: Meet GDPR, HIPAA, SOX, and other regulatory requirements
- **Operational Independence**: No internet dependency for core functionality

## Technology Stack

### Backend Architecture

- **Framework**: FastAPI (Python 3.12+) with async/await patterns
- **Vector Database**: ChromaDB for document embeddings and similarity search
- **Authentication**: Custom auth service with OAuth2 support (Google, Outlook)
- **Document Processing**: Support for PDF, DOCX, and text files
- **Embedding Models**: Sentence Transformers with Hugging Face integration
- **LLM Integration**: Ollama for local LLM inference, modular provider system

### Frontend Architecture

- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **UI Components**: Modern, responsive design with drag-and-drop file upload
- **Real-time Updates**: WebSocket integration for progress reporting
- **Testing**: Playwright for end-to-end testing

### Development & Deployment

- **Package Management**: `uv` for Python dependencies (CRITICAL: Always use `uv add`, never `pip install`)
- **Containerization**: Docker and Docker Compose for consistent environments
- **Code Quality**: `ruff` for linting and formatting, `pre-commit` hooks
- **Testing**: `pytest` with comprehensive test coverage
- **Documentation**: SAFe project structure with epics, features, stories, and tasks

## Project Structure

```
on_prem_rag/
├── src/
│   ├── backend/
│   │   ├── auth_service/          # Authentication microservice
│   │   ├── rag_pipeline/          # Core RAG implementation
│   │   │   ├── api/              # FastAPI endpoints and WebSocket
│   │   │   ├── config/           # Configuration management
│   │   │   ├── core/             # Core business logic
│   │   │   └── utils/            # Utility functions
│   │   └── security/             # Security management
│   └── frontend/                 # React TypeScript application
├── project/                      # SAFe project documentation
│   ├── portfolio/epics/          # Portfolio-level epics
│   ├── program/features/         # Program-level features
│   ├── team/stories/             # Team-level user stories
│   └── team/tasks/               # Development tasks
├── tests/                        # Comprehensive test suite
├── docs/                         # Technical documentation
├── scripts/                      # Utility and setup scripts
├── notebooks/                    # Jupyter notebooks for exploration
└── docker/                       # Docker configuration files
```

## Domain-Driven Design Architecture

The project follows a Domain-Driven Design (DDD) approach with five bounded contexts:

### 1. Ingestion Context

**Responsibility**: Document ingestion and processing

- **File Upload Component**: Web interface for file uploads
- **Document Processor**: Text extraction, chunking, and embedding generation
- **Supported Formats**: PDF, DOCX, TXT with extensible parser system

### 2. Knowledge Context

**Responsibility**: Knowledge base management

- **Vector Store Component**: ChromaDB integration for similarity search
- **Document Store**: Metadata management and document storage
- **Embedding Management**: Model configuration and vector operations

### 3. Interaction Context

**Responsibility**: User interactions and LLM integration

- **Q&A Component**: Natural language question processing and response generation
- **LLM Gateway**: Modular interface for multiple LLM providers
- **NL2SQL Component**: Natural language to SQL conversion (planned)

### 4. Orchestration Context

**Responsibility**: Workflow coordination

- **RAG Pipeline Orchestrator**: End-to-end document processing and Q&A
- **NL2SQL Pipeline Orchestrator**: Database query orchestration (planned)

### 5. Security Context

**Responsibility**: Authentication, authorization, and auditing

- **Authentication Component**: User login and session management
- **Authorization Component**: Role-based access control (RBAC)
- **Auditing Component**: Activity logging and compliance reporting

## Development Standards

### Coding Style & Function Design

**Core Principles**:

- **Readability First**: Code should be self-documenting and easy to understand
- **Single Responsibility**: Each function handles one logical operation
- **Testability**: Design functions for easy unit testing with dependency injection
- **Documentation**: Comprehensive docstrings for public APIs and core business logic

**Function Documentation Standards**:

```python
def process_document(file: UploadFile, params_name: str = DEFAULT_PARAM_SET_NAME):
    """Process uploaded document through the RAG pipeline.

    Args:
        file (UploadFile): The file to process. Supports .md, .docx, .pdf formats.
        params_name (str): Name of the parameter set for processing configuration.

    Returns:
        dict: Processing result containing:
            - message (str): Status message
            - filename (str): Name of processed file
            - chunks (int): Number of chunks created

    Raises:
        HTTPException: 400 if file format not supported
        HTTPException: 500 if processing fails

    Example:
        >>> result = process_document(file, "default_params")
        >>> print(result["chunks"])
        15
    """
```

### Error Handling

**Granular Error Handling**:

- Use specific try-except blocks for different failure modes
- Raise appropriate HTTP status codes (400, 401, 403, 404, 500)
- Include actionable error messages with context
- Preserve exception details when re-raising (`raise ... from e`)
- Log errors with sufficient context for debugging

### Testing Standards

**Test Structure**:

- **1 test for expected use**: Happy path functionality
- **1 edge case test**: Boundary conditions and edge cases
- **1 failure case test**: Error handling and failure scenarios
- Mock external service calls (LLM, database, file system)
- Update tests when logic changes
- **Never delete test files** - they are valuable for regression testing

**Test Organization**:

```
tests/
├── conftest.py                   # Shared test fixtures
├── core/                         # Core business logic tests
├── test_auth_service.py          # Authentication tests
├── test_document_loader.py       # Document processing tests
├── test_embeddings.py            # Embedding model tests
└── test_vector_store.py          # Vector database tests
```

### Dependency Management

**CRITICAL RULES**:

- **Always use `uv add package-name`** for new dependencies - NEVER use `pip install`
- `pip install` only works locally and causes failures in fresh environments
- Before importing any package, verify it exists in `pyproject.toml` or add it with `uv add`
- Use `uv sync` to install dependencies in fresh environments (CI/CD, containers)

## SAFe Project Management

The project follows the Scaled Agile Framework (SAFe) methodology with a complete documentation hierarchy:

### Documentation Structure

- **Portfolio Level**: Strategic epics and business objectives (`project/portfolio/epics/`)
- **Program Level**: Features and capabilities (`project/program/features/`)
- **Team Level**: User stories and tasks (`project/team/stories/`, `project/team/tasks/`)
- **Working Documentation**: Active development notes (`CURRENT_WORK.md`, `SCRATCH.md`)

### Current Implementation Status

**Phase 1: Foundation (MVP)** ✅ In Progress

- Core RAG pipeline with document ingestion
- Document question-answering pipeline
- Basic web interface for proof-of-concept
- Docker-based deployment
- Authentication microservice

**Phase 2: Enterprise Features** 🔄 Planned

- Role-based access control (RBAC)
- Multi-user support
- Security hardening
- Advanced UI features

**Phase 3: Advanced Capabilities** 📋 Future

- Database natural language queries (NL2SQL)
- Multi-LLM support
- Performance optimization
- Production deployment

## Key Commands & Development Workflow

### Quick Start

```bash
# Start all services with Docker Compose
docker-compose up --build

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# ChromaDB: http://localhost:8001
```

### Local Development Setup

```bash
# Create virtual environment
uv venv --python 3.13.2
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
uv pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
uv run pytest

# Start backend development server
uv run start-backend

# Start authentication service
uv run start-auth
```

### Code Quality

```bash
# Run linter and formatter
uv run ruff check .
uv run ruff format .

# Run pre-commit hooks
pre-commit run --all-files

# Run tests with coverage
uv run pytest --cov=src/backend
```

## Security & Compliance

### Authentication & Authorization

- **Authentication Service**: Standalone microservice with username/password and OAuth2
- **Session Management**: Secure session handling with JWT tokens
- **Role-Based Access**: RBAC implementation for enterprise features
- **Audit Logging**: Comprehensive activity logging for compliance

### Data Privacy

- **Zero Cloud Dependencies**: All processing happens on-premises
- **Data Sovereignty**: Complete control over data location and processing
- **Regulatory Compliance**: Designed to meet GDPR, HIPAA, SOX requirements
- **Encryption**: Data encryption at rest and in transit

## Risk Assessment & Mitigation

| Risk Category                | Impact | Mitigation Strategy                               |
| ---------------------------- | ------ | ------------------------------------------------- |
| **Model Performance**        | Medium | Extensive testing with business-relevant datasets |
| **Security Vulnerabilities** | High   | Third-party security audit before production      |
| **Resource Requirements**    | Medium | Scalable deployment architecture                  |
| **User Adoption**            | Low    | Intuitive UI design and comprehensive training    |

## AI Assistant Guidelines

### When Working on This Project

1. **Follow SAFe Structure**: Reference appropriate epic/feature/story documentation
2. **Use Cursor Rules**: Apply coding style, function definitions, and testing standards
3. **Dependency Management**: Always use `uv add` for new packages
4. **Documentation First**: Update working files, then task/story documentation
5. **Test Coverage**: Write tests for all new functionality
6. **Security Mindset**: Consider security implications of all changes

### Common Patterns

**Adding New Dependencies**:

```bash
# 1. Add dependency to pyproject.toml
uv add package-name

# 2. Import and use in code
from package_name import module_name
```

**Creating New API Endpoints**:

```python
# 1. Add endpoint to appropriate router in src/backend/rag_pipeline/api/
# 2. Implement business logic in core/ modules
# 3. Add tests in tests/ directory
# 4. Update API documentation
```

**Adding New Document Types**:

```python
# 1. Extend document_loader.py in core/
# 2. Add parser in utils/ directory
# 3. Update supported extensions in configuration
# 4. Add tests for new format
```

## Next Steps for Development

1. **Complete MVP**: Finish core RAG pipeline implementation
2. **Enterprise Features**: Implement RBAC and multi-user support
3. **Security Audit**: Conduct third-party security assessment
4. **Performance Optimization**: Optimize for production workloads
5. **User Training**: Develop comprehensive user documentation and training

---

**Project Status**: Development Phase - MVP in progress  
**Last Updated**: 2025-01-27  
**Documentation**: Complete SAFe structure in `project/` directory  
**Architecture**: Domain-Driven Design with five bounded contexts
