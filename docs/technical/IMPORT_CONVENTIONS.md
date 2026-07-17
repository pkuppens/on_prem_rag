# Import Conventions

Code lives under `src/` (e.g. `src/backend/`, `src/wbso/`), but `src` is a **build root, not an importable package** — always import as `backend.rag_pipeline.core.chunking`, `wbso.pipeline`, etc., never `src.backend...` or `src.wbso...`.

## Why `src.*` is banned

`src.*` imports used to work too, because a stray `src/__init__.py` turned `src` into a real package and pytest/scripts running from the repo root put the project root on `sys.path`. That made two import spellings resolve to the same module — confusing, and easy to typo into inconsistently across files. `src/__init__.py` has been removed and `ruff`'s `TID251` banned-api rule now fails the build on any `src.*` import (see `[tool.ruff.lint.flake8-tidy-imports.banned-api]` in `pyproject.toml`).

## Standalone scripts

Standalone scripts (e.g. `docs/project/hours/scripts/*.py`, `scripts/*.py`) never need `sys.path` manipulation to import `backend.*`/`wbso.*` — `uv sync --group dev` installs the package in editable mode, so those imports resolve as long as the script runs via `uv run python <script>` (the documented invocation for every such script). If you see a `sys.path.insert`/`sys.path.append` before an import block, it's very likely leftover cruft from before the editable install existed — delete it rather than "fixing" it, and put the import at the top of the file like any other.
