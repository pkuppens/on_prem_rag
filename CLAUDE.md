# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

On-premises RAG system for document analysis using LLMs while maintaining data sovereignty. FastAPI backend, React frontend, ChromaDB vector storage, Ollama for local LLM inference.

## Commands

```bash
# Environment setup (run once after clone)
uv sync --group dev
pre-commit install
uv run python scripts/setup_git_hooks.py  # Set up pre-push test enforcement

# Run tests
uv run pytest                              # Quick tests only (default)
uv run pytest -m ""                        # All tests including slow
uv run pytest --run-internet               # Include internet tests
uv run pytest -n 8 -m "" --run-internet   # Full PR simulation (parallel)
uv run pytest tests/test_chunking.py       # Single file
uv run pytest -k test_specific_function    # Specific test

# Lint and format
uv run ruff check --fix .
uv run ruff format .
uv run ruff check . && uv run ruff format --check .  # Verify clean

# Services
uv run start-backend                       # FastAPI RAG backend
uv run start-auth                          # Auth microservice
uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark.json
docker-compose up --build                  # Full stack (ports 9180-9182, see docs/PORTS.md)

# WBSO pipeline
uv run wbso-pipeline && uv run wbso-validate && uv run wbso-report
uv run mcp-calendar-server
```

## Architecture

### Source Layout (`src/`)

- **backend/rag_pipeline/** — Core RAG: `api/`, `core/`, `services/`, `models/`, `config/`, `agents/`, `evaluation/`
- **backend/auth_service/** — OAuth2/JWT authentication microservice
- **backend/security/** — Security utilities and validation
- **backend/access_control/** — Role-based access control
- **backend/audit_trail/** — Audit logging
- **backend/guardrails/** — NeMo Guardrails LLM safety
- **backend/memory/** — Agent memory (long-term, shared) with ChromaDB
- **backend/privacy_guard/** — PII detection
- **backend/stt/** — Whisper speech-to-text
- **wbso/** — R&D tax credit pipeline (calendar, session detection, SQLAlchemy ORM)
- **mcp/** — Model Context Protocol server for Google Calendar
- **frontend/** — React/TypeScript web interface

Other: `project/` (SAFe docs), `docs/` (technical docs), `tests/` (mirrors src structure), `.cursor/rules/` (AI rules), `agents/` (agent configs).

### Key Patterns

- **Absolute imports**: `from backend.rag_pipeline.core import chunking` — no relative imports
- **src-layout**: Package installed in editable mode via `uv sync --group dev`
- **Entry points**: Defined in `pyproject.toml` `[project.scripts]`

## Critical Rules

**Dependency management**: `uv add package-name` (runtime) / `uv add --dev package-name` — **NEVER `pip install`**.

**Code style**: Line length 132, Python 3.13, type hints required, files under 500 lines. See [coding-style.mdc](.cursor/rules/coding-style.mdc) and [function-definitions.mdc](.cursor/rules/function-definitions.mdc).

**Testing**: Pre-push hooks enforce test passing on every push. Use `git push --no-verify` only in emergencies. CI coverage: `gh run download <RUN_ID> --name coverage-reports --dir tmp/coverage-reports`.

## Test Markers

| Marker                  | Description                           | Default  |
| ----------------------- | ------------------------------------- | -------- |
| `@pytest.mark.slow`     | Tests >5 seconds                      | Skipped  |
| `@pytest.mark.internet` | Network required                      | Skipped  |
| `@pytest.mark.ollama`   | Requires Ollama (local LLM on 11434)  | Skipped  |
| `@pytest.mark.docker`   | Requires full Docker stack deployment | Skipped  |
| `@pytest.mark.fts5`     | SQLite FTS5 required                  | Included |

## Git Workflow

- Branches: `feature/NNN-description`, `task/TASK-XXX-description`
- Commits: `#NNN: type: description` (types: feat, fix, docs, test, refactor, chore)
- Doc/config changes can go directly to main; all other changes through PRs
- **Full workflow**: [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)

## Scratch Directory (`tmp/`)

Use `tmp/` for all scratch files that should NOT be committed (gitignored).

```
tmp/
├── github/issue-NNN/        # description.md, workflow.md, plan.md, comments/
├── coverage-reports/        # CI coverage (gh run download); open htmlcov/index.html
├── analysis/                # Exploration notes, profiling
├── debug/                   # Debug output, logs, test artifacts
└── drafts/                  # Any other WIP text
```

Rules: never commit from `tmp/`; prefer `tmp/` over repo root or `docs/`; move persistent content to Claude memory.

## References

| Topic | Location |
|---|---|
| Issue implementation workflow | [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md) |
| Architecture rules + SOLID patterns | [docs/technical/AGENTS.md](docs/technical/AGENTS.md), [.cursor/rules/modular-architecture.mdc](.cursor/rules/modular-architecture.mdc) |
| Code style rules | [.cursor/rules/coding-style.mdc](.cursor/rules/coding-style.mdc), [function-definitions.mdc](.cursor/rules/function-definitions.mdc) |
| Test documentation style | [.cursor/rules/test-documentation.mdc](.cursor/rules/test-documentation.mdc) |
| CI setup + coverage | [docs/technical/CI_SETUP.md](docs/technical/CI_SETUP.md) |
| Deployment | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| API usage | [docs/USAGE.md](docs/USAGE.md) |
| Docker development | [docs/TEST_DOCKER.md](docs/TEST_DOCKER.md) |
| Issue templates | [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/) |
