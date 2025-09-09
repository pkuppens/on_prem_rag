# User Story: Development Environment Setup

**ID**: STORY-001  
**Feature**: [FEAT-001: Technical Foundation & MVP](../../program/features/FEAT-001.md)  
**Team**: Platform Engineering  
**Status**: Completed  
**Priority**: P1  
**Points**: 5  
**Created**: 2025-05-31  
**Updated**: 2025-09-09

## User Story

As a **developer joining the On-Premises RAG project**  
I want **a consistent, reproducible development environment**  
So that **I can contribute effectively without environment-specific issues**

## Business Context

A standardized development environment eliminates "works on my machine" problems, reduces onboarding time for new team members, and ensures consistent behavior across development, testing, and production environments.

## Acceptance Criteria

- [x] **Given** a new developer with Python 3.11+ installed, **when** they follow the setup guide, **then** they can run the complete RAG pipeline locally within 30 minutes
- [x] **Given** the development environment is set up, **when** a developer runs tests, **then** all tests pass consistently across different machines
- [x] **Given** the project dependencies, **when** using the package manager, **then** all dependencies install with pinned versions for reproducibility
- [x] **Given** the containerized environment, **when** starting services, **then** all components start successfully and can communicate

## Tasks

- [x] **[TASK-001](../tasks/TASK-001.md)**: Configure Python project with uv package manager - Backend Engineer - 4h
- [x] **[TASK-002](../tasks/TASK-002.md)**: Create development Docker Compose setup - DevOps Engineer - 6h
- [x] **[TASK-003](../tasks/TASK-003.md)**: Set up code quality tools (ruff, pytest) - Backend Engineer - 4h
- [x] **[TASK-004](../tasks/TASK-004.md)**: Create comprehensive setup documentation - Technical Writer - 4h
- [x] **[TASK-005](../tasks/TASK-005.md)**: Validate setup across different operating systems - QA Engineer - 8h

## Definition of Done

- [x] **Environment Setup**: Complete development environment documentation with step-by-step instructions
- [x] **Package Management**: `uv` configured with locked dependencies in `uv.lock`
- [x] **Code Quality**: Ruff linting and formatting integrated with pre-commit hooks
- [x] **Testing Framework**: Pytest configured with coverage reporting and CI integration
- [x] **Containerization**: Docker Compose services for all development dependencies
- [x] **Documentation**: README updated with setup instructions and troubleshooting guide
- [x] **Validation**: Setup verified on Windows, macOS, and Linux environments

## Technical Requirements

### Core Tools

- **Python**: 3.11+ for modern async features and performance
- **Package Manager**: `uv` for fast, reliable dependency management
- **Linting**: `ruff` for fast Python linting and formatting
- **Testing**: `pytest` with coverage and fixtures for RAG components
- **Containerization**: Docker and Docker Compose for service orchestration

### Development Dependencies

- **ChromaDB**: Vector database for document embeddings
- **Ollama**: Local LLM inference platform
- **FastAPI**: Web framework for API development
- **Sentence Transformers**: Embedding model library

### Quality Gates

- All linting rules pass with zero warnings
- Test coverage >80% for core RAG functionality
- Documentation includes working code examples
- Setup time <30 minutes for new developers

## Risks & Mitigations

| Risk                       | Impact | Mitigation                                          |
| -------------------------- | ------ | --------------------------------------------------- |
| **Platform Compatibility** | Medium | Test setup on all major operating systems           |
| **Dependency Conflicts**   | High   | Use locked dependency versions with uv              |
| **Docker Resource Usage**  | Medium | Provide resource requirements and optimization tips |

## Notes

### Development Workflow

1. Clone repository and follow setup guide
2. Run `uv install` to install dependencies
3. Start Docker services with `docker-compose up`
4. Run tests to verify environment: `uv run pytest`
5. Begin development with live reload and hot reloading

### Future Considerations

- Integration with VS Code dev containers for even more consistency
- Automated environment validation in CI/CD pipeline
- Performance profiling tools for RAG pipeline optimization

---

**Story Owner**: Backend Engineer  
**Reviewer**: Lead Developer  
**Sprint**: TBD  
**Estimated Completion**: TBD
