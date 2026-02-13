# justfile — project task runner (cross-platform)
# Run `just` to list recipes, `just <recipe>` to run.
# Install: winget install Casey.Just | scoop install just | choco install just
# See: https://github.com/casey/just

# Use PowerShell on Windows (default sh is often unavailable)
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Lint and format checks (must pass before commit)
lint:
    uv run ruff check .
    uv run ruff format --check .

# Strict lint: also check F401 (unused imports) — pyproject ignores F* by default
lint-strict:
    uv run ruff check . --select F401

# Auto-fix lint and format
lint-fix:
    uv run ruff check . --fix
    uv run ruff format .

# Ruff only (when you need just one)
ruff-check:
    uv run ruff check .
ruff-format:
    uv run ruff format --check

# Run tests (excludes slow and internet by default)
test:
    uv run pytest

# Run all tests including slow
test-all:
    uv run pytest -m ""

# Run slow tests only
test-slow:
    uv run pytest -m slow

# Run tests with coverage report
test-cov:
    uv run pytest --cov=src/backend --cov-report=term

# Run backend API
run:
    uv run start-backend

# Run auth service
run-auth:
    uv run start-auth

# Run full stack with Docker
docker:
    docker compose up --build

# Run pre-commit hooks
pre-commit:
    pre-commit run --all-files

# Full quality gate (lint + test)
check: lint test

# Strict quality gate (includes F401 unused-import check)
check-strict: lint lint-strict test
