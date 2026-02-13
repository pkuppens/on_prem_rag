# justfile — project task runner (cross-platform)
# Run `just` to list recipes, `just <recipe>` to run.
# Install: scoop install just | choco install just | cargo install just
# See: https://github.com/casey/just

# Lint and format checks (must pass before commit)
lint:
    uv run ruff check . && uv run ruff format --check .

# Auto-fix lint and format
lint-fix:
    uv run ruff check . --fix && uv run ruff format .

# Run tests (excludes slow and internet by default)
test:
    uv run pytest

# Run all tests including slow
test-all:
    uv run pytest -m ""

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
