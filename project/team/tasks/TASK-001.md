# Task: Configure Python Project with uv Package Manager

**ID**: TASK-001
**Story**: [STORY-001: Development Environment Setup](../stories/STORY-001.md)
**Assignee**: Backend Engineer
**Status**: Completed
**Effort**: 4 hours
**Created**: 2025-05-31
**Updated**: 2025-06-05

## Description

Set up the basic structure for this project:

- Create the foundational project files, including `pyproject.toml`, dependency specifications, and initial package structure.
- Python (3.12) for coding
  - coding style instructions for well-documented code with type hinting, extensive docstrings
  - using the `uv` package manager for fast, reliable dependency management
  - using minimum requirements (>=x.y.z) or no requirement over fixed requirements (==x.y.z) during library/proof of concept development
  - `uv.lock` is git ignored, or only linked to production releases.
  - using `ruff` over `flake`, `black`, for code formatting and linting, with a very permissive coding style
  - using `pytest` for testing over `unittest`
- Pre-commit hooks that run:
  - both ruff format and ruff check
  - pytest (coverage is out of scope for now)
  - secret detection
- Github actions folder with minimal example
- 'docs/SETUP.md' documentation for the set-up with explanations, and required steps, pre-commit autoupdate and install

## Acceptance Criteria

- [x] `pyproject.toml` configured with project metadata and dependencies
- [x] `uv.lock` consideration explained
- [x] Project structure follows Python packaging best practices for proof-of-concept library
- [x] All core dependencies for RAG pipeline specified with version constraints
- [x] Development dependencies separated from production requirements

## Implementation Details

### Required Files

- `pyproject.toml`: Project configuration and dependency specification
- `uv.lock`: Locked dependency versions for reproducible builds
- `src/rag_pipeline/`: Main package directory structure
- `.python-version`: Python version specification
- `README.md`: Basic project setup instructions link
  `docs/SETUP.md`: Setup descriptions and instructions

### Core Dependencies

```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "chromadb>=0.4.0",
    "sentence-transformers>=2.2.0",
    "ollama>=0.1.0",
    "pypdf>=3.17.0",
    "python-docx>=1.1.0",
    "uvicorn>=0.24.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "pre-commit>=3.5.0"
]
```

### Package Structure

```
src/
├── rag_pipeline/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── utils/
│       ├── __init__.py
│       └── document_loader.py
tests/
├── __init__.py
├── test_embeddings.py
└── test_document_loader.py
```

## Dependencies

- **Blocked by**: None (foundational task)
- **Blocks**: TASK-002 (Docker setup needs pyproject.toml), TASK-003 (code quality tools configuration)

## Time Tracking

- **Estimated**: 4 hours
- **Breakdown**:
  - Project configuration: 1.5 hours
  - Dependency research and specification: 1.5 hours
  - Package structure creation: 1 hour
- **Actual**: TBD
- **Remaining**: 4 hours

## Implementation Steps

1. **Initialize uv project** (30 min)

   - Run `uv init` to create basic project structure
   - Configure Python version constraint (3.12+)

2. **Configure pyproject.toml** (90 min)

   - Add project metadata (name, version, description)
   - Specify core dependencies with version constraints
   - Configure development dependencies
   - Set up project entry points

3. **Create package structure** (60 min)

   - Create `src/rag_pipeline/` directory structure
   - Add `__init__.py` files with proper imports
   - Create placeholder modules for core functionality

4. **Generate lock file** (30 min)

   - Run `uv lock` to generate `uv.lock` file
   - Verify all dependencies resolve correctly
   - Test installation in clean environment
   - Document the Version constraints decisions

5. **Documentation** (30 min)
   - Update README.md with setup instructions link to docs/SETUP.md

- Write docs/SETUP.md with setup instructions
  - Document package structure and purpose
  - Add troubleshooting notes for common issues

## Validation

- [x] `uv pip install -e .` completes successfully
- [x] `uv lock` generates valid lock file
- [x] Package imports work: `python -c "import rag_pipeline"`
- [x] All specified dependencies available in environment
- [x] Project structure follows Python packaging standards

## Notes

### Technology Rationale

- **uv**: Chosen over pip/poetry for significantly faster dependency resolution and installation
- **src layout**: Improves import behavior and testing isolation
- **Version constraints**: Be flexible during development, and pinned to stable versions while allowing patch updates when moving to production releases

### Future Considerations

- Integration with pre-commit hooks for dependency validation
- Automated dependency vulnerability scanning
- Consideration of dependency grouping for different deployment scenarios

---

**Implementer**: Backend Engineer
**Reviewer**: Lead Developer
**Target Completion**: TBD
