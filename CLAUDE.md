# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

On-premises RAG (Retrieval-Augmented Generation) system enabling document analysis and database querying using LLMs while maintaining data sovereignty. Built with FastAPI backend, React frontend, and integrates with ChromaDB for vector storage and Ollama for local LLM inference.

## Build and Development Commands

```bash
# Environment setup (run once after clone)
uv sync --group dev
pre-commit install
uv run python scripts/setup_git_hooks.py  # Set up pre-push test enforcement

# Verify setup
uv run pytest
pre-commit run --all-files

# Run tests (default: excludes slow and internet tests)
uv run pytest                              # Quick tests only
uv run pytest -m ""                        # All tests including slow
uv run pytest --run-internet               # Include internet tests
uv run pytest tests/test_chunking.py       # Single file
uv run pytest -k test_specific_function    # Specific test

# Linting and formatting
uv run ruff check --fix .                  # Fix lint issues
uv run ruff format .                       # Format code
uv run ruff check . && uv run ruff format --check .  # Verify clean
# Or: just lint / just lint-fix (requires just: scoop install just)

# Run services
uv run start-backend                       # FastAPI RAG backend
uv run start-auth                          # Auth microservice
docker-compose up --build                  # Full stack with Docker

# WBSO pipeline commands
uv run wbso-pipeline                       # Full WBSO processing pipeline
uv run wbso-validate                       # Validate WBSO data
uv run wbso-report                         # Generate WBSO reports
uv run mcp-calendar-server                 # MCP Calendar Server
```

## Architecture

### Source Layout (src/)

- **backend/rag_pipeline/** - Core RAG functionality
  - `api/` - FastAPI endpoints and routes
  - `core/` - Document chunking, embedding, vector operations
  - `services/` - Business logic (document processing, QA)
  - `models/` - Pydantic models and data structures
  - `config/` - Configuration and parameter sets
- **backend/auth_service/** - Authentication microservice (OAuth2, JWT)
- **backend/security/** - Security utilities and validation
- **wbso/** - WBSO (Dutch R&D tax credit) pipeline for work session tracking
  - Calendar integration, session detection, activity assignment
  - SQLAlchemy ORM models for persistent storage
- **mcp/** - Model Context Protocol server for Google Calendar integration
- **frontend/** - React/TypeScript web interface

### Key Patterns

- **Absolute imports**: Use `from backend.rag_pipeline.core import chunking` not relative imports
- **src-layout**: Package installed in editable mode via `uv sync --group dev`
- **Entry points**: Defined in `pyproject.toml` `[project.scripts]`

## Critical Rules

### Dependency Management

**Always use `uv add` - NEVER use `pip install`**. Dependencies must be in `pyproject.toml` for CI/CD and containers to work.

```bash
uv add package-name        # Runtime dependency
uv add --dev package-name  # Dev dependency
uv sync                    # Install from pyproject.toml
```

### Testing

- Pre-push hooks enforce test passing on every push
- Tests marked `@pytest.mark.slow` or `@pytest.mark.internet` are skipped by default
- Use `git push --no-verify` only in emergencies
- Test docstrings should follow: "As a user I want [objective], so I can [benefit]. Technical: [requirement]."

### Git Workflow

- Feature branches: `feature/FEAT-XXX-description` or `feature/NNN-short-description`
- Task branches: `task/TASK-XXX-description`
- Use `gh issue view NNN` to fetch issues; follow [Issue Implementation Workflow](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
- Documentation/config changes can go directly to main
- All pytest tests must pass before PR creation

### Code Style

- Line length: 132 characters
- Python 3.13 target
- Ruff for linting and formatting
- Type hints required for function signatures
- Files should stay under 500 lines

## Project Structure Notes

- `project/` - SAFe methodology documentation (epics, features, stories, tasks)
- `docs/` - Technical documentation
- `tests/` - All test files (mirroring src structure in `tests/core/`)
- `.cursor/rules/` - AI assistant rules and guidelines
- `agents/` - AI agent configurations
- `tmp/` - **Scratch directory** (gitignored) — see below

## Scratch Directory (`tmp/`)

Use `tmp/` for all development scratch files that should NOT be committed. This directory is gitignored.

**When to use `tmp/`:**

- Drafting PR descriptions, issue comments, or issue bodies before posting via `gh`
- Storing workflow progress, like checklists that need marking completed items
- Storing intermediate analysis, exploration notes, or debug output
- Caching fetched issue descriptions for offline reference
- Any file you'd otherwise create at the repo root or in a random location

**Structure:**

```
tmp/
├── CLAUDE.md              # Instructions for this directory
├── github/                # GitHub-related drafts
│   ├── CLAUDE.md
│   ├── issue-descriptions/  # Cached issue bodies (issue-NNN.md)
│   ├── issue-comments/      # Draft comments before posting
│   └── pr-bodies/           # Draft PR descriptions
├── analysis/              # Exploration notes, coverage reports, profiling
├── debug/                 # Debug output, logs, test artifacts
└── progress/              # Any other work-in-progress text
```

**Rules:**

- Never commit files from `tmp/` — it is in `.gitignore`
- Prefer `tmp/` over creating files at the repo root or in `docs/`
- Clean up stale files periodically; nothing here is permanent
- If content in `tmp/` should persist across sessions, move it to Claude memory instead

## Test Markers

| Marker                  | Description          | Default  |
| ----------------------- | -------------------- | -------- |
| `@pytest.mark.slow`     | Tests >5 seconds     | Skipped  |
| `@pytest.mark.internet` | Network required     | Skipped  |
| `@pytest.mark.fts5`     | SQLite FTS5 required | Included |
