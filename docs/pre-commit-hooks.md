# Pre-commit Hooks

This document explains the pre-commit hooks used in this project to maintain code quality and consistency.

## Basic Code Quality Hooks

### pre-commit-hooks

These are basic hooks that help maintain code quality:

- `trailing-whitespace`: Removes trailing whitespace from files (excludes markdown files)
- `end-of-file-fixer`: Ensures files end with a newline
- `check-yaml`: Validates YAML syntax
- `check-added-large-files`: Prevents large files from being committed
- `check-json`: Validates JSON syntax
  - Excludes JSON5 files (`*.json5`) and VSCode settings (`.vscode/*`)
- `check-toml`: Validates TOML syntax
- `check-merge-conflict`: Detects merge conflict markers in files
- `debug-statements`: Catches debugger imports and py.test breakpoints

## Python-specific Hooks

### Ruff

Ruff is a fast Python linter and formatter:

- `ruff`: Runs linting checks and automatically fixes issues
- `ruff-format`: Formats Python code according to style guidelines

### Notebook Management

- `nbstripout`: Removes notebook output cells and empty cells from Jupyter notebooks

## Security Hooks

### Detect Secrets

- `detect-secrets`: Scans for accidentally committed secrets and credentials
  - Uses a baseline file (`.secrets.baseline`) to track known false positives
  - Helps prevent sensitive information from being committed

### Bandit

- `bandit`: Security linter for Python code
  - Scans for common security issues
  - Configured through `pyproject.toml`

## Type Checking

### MyPy

- `mypy`: Static type checker for Python
  - Helps catch type-related errors before runtime
  - Uses specific type stubs for common packages:
    - `types-requests`
    - `types-PyYAML`
    - `types-setuptools`
    - `types-urllib3`
    - `types-python-dateutil`

## Usage

To install the pre-commit hooks:

```bash
pre-commit install
```

To run the hooks manually:

```bash
pre-commit run --all-files
```

To update the secrets baseline (after first run):

```bash
pre-commit run detect-secrets --all-files
```
