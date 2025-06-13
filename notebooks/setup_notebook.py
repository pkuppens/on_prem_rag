"""Setup script for Jupyter notebooks.

This script ensures that the package is properly installed and importable in notebooks.
It should be imported at the start of each notebook.

Example usage:
    from setup_notebook import setup_notebook
    setup_notebook()
"""

import subprocess
import sys
from pathlib import Path


def setup_notebook():
    """Ensure the package is installed in development mode."""
    # Get the project root directory (parent of notebooks directory)
    project_root = Path(__file__).parent.parent

    # Check if we're in a virtual environment
    if not hasattr(sys, "real_prefix") and not hasattr(sys, "base_prefix"):
        print("Warning: Not running in a virtual environment. Please activate your virtual environment first.")
        return

    # Add src/backend to Python path if not already there
    backend_path = str(project_root / "src" / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
        print(f"Added {backend_path} to Python path.")


SET_PATH_ON_IMPORT = True

if __name__ == "__main__" or SET_PATH_ON_IMPORT:
    setup_notebook()
