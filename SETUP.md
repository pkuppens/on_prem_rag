# Project Setup Guide

This guide provides instructions for setting up the development environment for the On-Prem RAG project.

## Prerequisites

- Python 3.12 or higher
- `uv` package manager. Can be installed via
    - `winget install astral-sh.uv`
    - `pip install uv`
    - or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Git

## Initial Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd on_prem_rag
    ```

2.  **Set up Python environment using `uv`:**

    If you have a `.python-version` file (which should be `3.12`), `uv` can automatically create a virtual environment with that Python version.
    ```bash
    uv venv
    ```
    This will create a `.venv` directory. Activate it using:
    - On macOS and Linux:
      ```bash
      source .venv/bin/activate
      ```
    - On Windows:
      ```bash
      .venv\Scripts\activate
      ```

3.  **Install dependencies:**

    Install both production and development dependencies using `uv`:
    ```bash
    uv pip install -e .[dev]
    ```
    The `-e .` installs the current project in editable mode. `[dev]` installs the optional development dependencies specified in `pyproject.toml`.

4.  **Locking Dependencies (Optional but Recommended for Production):**

    The `uv.lock` file is gitignored by default for library/proof-of-concept development to allow flexibility. For production releases or to ensure exact reproducible environments, you can generate and commit `uv.lock`:
    ```bash
    uv lock
    ```
    To install from the lock file:
    ```bash
    uv pip sync --locked
    ```
    **Decision on `uv.lock`**: During initial development and for this proof-of-concept, we will not commit `uv.lock` to the repository. This provides more flexibility with dependency versions. For production releases, a `uv.lock` file should be generated and used to ensure reproducible builds.

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency before committing changes.

1.  **Install pre-commit:**

    If you haven't already, install pre-commit (it's also in the dev dependencies):
    ```bash
    pip install pre-commit
    # or, if you installed dev dependencies with uv:
    # uv pip install pre-commit
    ```

2.  **Install the git hooks:**

    Run this command in the root of the project to install the hooks defined in `.pre-commit-config.yaml`:
    ```bash
    pre-commit install
    ```
    Now, the defined hooks will run automatically every time you commit changes.

3.  **Update hooks (Optional):**

    To update the hooks to their latest versions:
    ```bash
    pre-commit autoupdate
    ```

## Code Quality and Formatting

-   **Ruff**: Used for linting and formatting. Configuration is in `pyproject.toml`.
    -   To format code: `ruff format .`
    -   To check for linting issues: `ruff check .`
    -   These are also run by the pre-commit hooks.
-   **Pytest**: Used for running tests. Tests are located in the `tests/` directory.
    -   To run tests: `pytest`
    -   This is also run by the pre-commit hooks.

## Package Structure

The project follows a `src` layout:

```
src/
├── rag_pipeline/          # Main package directory
│   ├── __init__.py
│   ├── core/                # Core RAG functionalities
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── api/                 # FastAPI application
│   │   ├── __init__.py
│   │   └── routes.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── document_loader.py
tests/
├── __init__.py
├── test_embeddings.py
└── test_document_loader.py
```

-   `src/rag_pipeline`: Contains the main application code.
-   `tests/`: Contains all the tests.

## Running the Application (Example with Uvicorn)

Once a FastAPI application is set up in `src/rag_pipeline/api/main.py` (example path), you can run it using Uvicorn:

```bash
cd src
uvicorn rag_pipeline.api.main:app --reload
# (Assuming your FastAPI app instance is named 'app' in main.py)
```

## Troubleshooting

-   **`uv` command not found**: Ensure `uv` is installed and its installation directory is in your system's PATH. Refer to the official `uv` installation guide.
-   **Python version issues**: Make sure you have Python 3.12 installed and that `uv` is using it. You can specify the Python version for `uv venv` using `uv venv -p 3.12`.
-   **Pre-commit hook failures**: Address the issues reported by the hooks (e.g., formatting errors, linting violations) and re-commit.
