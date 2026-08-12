# CLAUDE.md

## Project Overview

On-premises RAG system for document analysis using LLMs while maintaining data sovereignty. FastAPI backend, React frontend, ChromaDB vector storage, Ollama for local LLM inference.

## Commands

```bash
# Environment setup (run once after clone)
uv sync --group dev
pre-commit install
uv run python scripts/setup_git_hooks.py  # Set up pre-push test enforcement
# Canonical AI skills (sibling clone pkuppens/pkuppens required): see docs/technical/SKILLS_SETUP.md
#   PowerShell: .\scripts\link_cursor_skills.ps1

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

### Import Conventions

Always import as `backend.rag_pipeline.core.chunking`, `wbso.pipeline`, etc. — never `src.backend...`/`src.wbso...` (banned by ruff `TID251`). Details/history: [docs/technical/IMPORT_CONVENTIONS.md](docs/technical/IMPORT_CONVENTIONS.md).

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

- **Always work from a branch by default.** Before making any edits, create/switch to a feature branch — never commit or push directly on `main` unless the user explicitly instructs otherwise (e.g. a CI/CD fix that only reproduces on `main`).
- Branches: `feature/NNN-description`, `task/TASK-XXX-description`, `chore/…`, `docs/…`
- Commits: `#NNN: type: description` (types: feat, fix, docs, test, refactor, chore)
- **Merge to `main` only via pull request** (including docs, rules, and skills); enable protection per [docs/technical/BRANCH_PROTECTION.md](docs/technical/BRANCH_PROTECTION.md)
- **Full workflow**: [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)

## Project Board

Open issues are tracked on a GitHub Project (Kanban board): https://github.com/users/pkuppens/projects/1

- **Status** column (Todo / In Progress / Done) is the Kanban view.
- **Rank** field (number, lower = higher priority) orders issues by value-vs-effort — most value for least effort first. Set/updated by whoever last did a priority pass; not auto-maintained.
- **When picking what to work on next, or when priority is ambiguous, check this board before asking the user** — it reflects the user's last stated ordering.
- A Roadmap (timeline) view can be added manually in the web UI; `gh project` CLI cannot create custom views.

## Scratch Directory (`tmp/`)

Use `tmp/` (gitignored) for all scratch files — never the repo root or `docs/`. See [tmp/CLAUDE.md](tmp/CLAUDE.md) for subdirectory layout and conventions.

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
