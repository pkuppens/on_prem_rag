"""LlamaIndex compatibility shims for API changes across versions.

StorageContext and other symbols may move between llama_index.core and
submodules. This module provides stable imports for our usage.
"""

from __future__ import annotations

try:
    from llama_index.core import StorageContext
except ImportError:
    from llama_index.core.storage.storage_context import StorageContext

__all__ = ["StorageContext"]
