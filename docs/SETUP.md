# Project Setup Guide

This guide provides instructions for setting up the development environment for the On-Prem RAG project.

## Prerequisites

- Python 3.12 or higher, I use 3.13.2 for development and 3.12 for implicit portability testing
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

2.  **Install dependencies using `uv`:**

    `uv sync` creates a virtual environment (`.venv`) and installs all dependencies in one step. No manual activation is needed—use `uv run` for all commands.

    ```bash
    uv sync --group dev
    ```

    This installs the project in editable mode with all development dependencies (pytest, ruff, pre-commit, etc.). `uv` automatically uses Python 3.13.2 if available, or falls back to the project's `requires-python` range (3.12–3.14).

    **CRITICAL DEPENDENCY MANAGEMENT RULE**:

    - **Always use `uv add package-name` for new dependencies - NEVER use `pip install`**
    - `pip install` only works locally but fails in fresh environments (CI/CD, containers)
    - Before importing any new package, always run `uv add package-name` first
    - This ensures the dependency is added to `pyproject.toml` and works in all environments

    Note: The project uses several llama-index packages for different functionalities:

    - `llama-index`: Core package
    - `llama-index-llms-ollama`: For Ollama LLM integration
    - `llama-index-llms-huggingface`: For HuggingFace LLM integration
    - `llama-index-embeddings-huggingface`: For HuggingFace embeddings
    - `llama-index-readers-file`: For file reading capabilities
    - `llama-index-vector-stores-chroma`: For ChromaDB vector store integration

    If you encounter any import errors related to llama-index modules, make sure all these packages are installed.

3.  **Install pre-commit hooks:**

    ```bash
    pre-commit install
    uv run python scripts/setup_git_hooks.py   # Pre-push test enforcement
    ```

4.  **Verify setup:**

    ```bash
    uv run pytest
    pre-commit run --all-files   # First run may auto-fix some files; run again to confirm pass
    ```

5.  **Local CUDA/GPU setup (optional):**

    The default install uses PyTorch CPU (required for CI). For local development with an NVIDIA GPU (e.g. RTX 4090):

    ```bash
    uv run is-cuda-available
    # Or if uv run fails (e.g. file lock): .venv\Scripts\python.exe scripts\is_cuda_available.py
    ```

    See [docs/technical/CUDA_SETUP.md](technical/CUDA_SETUP.md) for CUDA install steps.

6.  **Locking Dependencies (Optional but Recommended for Production):**

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

1.  **Pre-commit is included** when you run `uv sync --group dev`. No separate install is needed.

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

- **Ruff**: Used for linting and formatting. Configuration is in `pyproject.toml`.
  - To format code: `uv run ruff format .`
  - To check for linting issues: `uv run ruff check .`
  - These are also run by the pre-commit hooks.
- **Pytest**: Used for running tests. Tests are located in the `tests/` directory.
  - To run tests: `uv run pytest`
  - This is also run by the pre-commit hooks.

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

- `src/rag_pipeline`: Contains the main application code.
- `tests/`: Contains all the tests.

## Running the Application (Example with Uvicorn)

Once a FastAPI application is set up in `src/rag_pipeline/api/main.py` (example path), you can run it using Uvicorn:

```bash
cd src
uvicorn rag_pipeline.api.main:app --reload
# (Assuming your FastAPI app instance is named 'app' in main.py)
```

## Troubleshooting

- **`uv` command not found**: Ensure `uv` is installed and its installation directory is in your system's PATH. Refer to the official `uv` installation guide.
- **Python version issues**: Make sure you have Python 3.13.2 installed and that `uv` is using it. You can specify the Python version for `uv venv` using `uv venv -p 3.13.2`.
- **Pre-commit hook failures**: Address the issues reported by the hooks (e.g., formatting errors, linting violations) and re-commit.

## Offline model caching

The tests rely on the `sentence-transformers/all-MiniLM-L6-v2` model. If you are
working in an environment without internet access you must download this model
in advance and cache it locally:

```bash
python - <<'EOF'
from sentence_transformers import SentenceTransformer
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
EOF
```

The files are stored under `~/.cache/huggingface` by default. Afterwards you can
set the following environment variables to avoid network calls:

```bash
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
```
