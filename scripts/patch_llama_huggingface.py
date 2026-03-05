#!/usr/bin/env python3
"""Patch llama_index.llms.huggingface to re-export HuggingFaceInferenceAPI.

HuggingFaceInferenceAPI was moved to llama-index-llms-huggingface-api but
llama_index.llms.__init__ still expects it in .huggingface. This script
patches the installed __init__.py to add the re-export.

Run after: uv sync --dev
Run before: pytest
"""

from __future__ import annotations

import site
import sys
from pathlib import Path


def main() -> int:
    """Patch the huggingface __init__.py if needed."""
    init_py = None
    for sp in site.getsitepackages():
        candidate = Path(sp) / "llama_index" / "llms" / "huggingface" / "__init__.py"
        if candidate.exists():
            init_py = candidate
            break
    if init_py is None:
        print(f"Warning: {init_py} not found, skipping patch", file=sys.stderr)
        return 0

    content = init_py.read_text()
    if "HuggingFaceInferenceAPI" in content:
        print("llama_index.llms.huggingface already has HuggingFaceInferenceAPI")
        return 0

    # Add re-export block after the existing imports, before __all__
    patch = '''
try:
    from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
except ImportError:
    HuggingFaceInferenceAPI = None  # type: ignore[misc,assignment]

'''
    # Replace __all__ to include HuggingFaceInferenceAPI
    if '__all__ = ["HuggingFaceLLM"]' in content:
        new_content = content.replace(
            '__all__ = ["HuggingFaceLLM"]',
            f'''{patch}__all__ = ["HuggingFaceLLM", "HuggingFaceInferenceAPI"]''',
        )
    else:
        print("Unexpected format, skipping patch", file=sys.stderr)
        return 1

    init_py.write_text(new_content)
    print("Patched llama_index.llms.huggingface to re-export HuggingFaceInferenceAPI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
