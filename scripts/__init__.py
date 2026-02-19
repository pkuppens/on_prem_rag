"""Utility helpers for standalone scripts.

This package allows running scripts directly from the project repository without
first installing the package.  It provides :func:`configure_pythonpath` which
adds important project directories to ``sys.path`` at runtime so relative imports
work consistently.
"""

from __future__ import annotations

import sys
from pathlib import Path


def configure_pythonpath() -> None:
    """Ensure ``scripts`` and ``src`` directories are importable.

    This function is primarily used when executing tools directly via ``python
    scripts/<name>.py``.  It prepends the ``scripts``, ``src`` and
    ``src/backend`` directories to ``sys.path`` based on the detected project
    root using :func:`backend.shared.utils.directory_utils.get_project_root`.
    """

    try:
        from backend.shared.utils.directory_utils import get_project_root
    except Exception:  # pragma: no cover - fallback for early imports
        root = Path(__file__).resolve().parent.parent
    else:
        root = get_project_root()

    for rel in ("scripts", "src", "src/backend"):
        path = root / rel
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
