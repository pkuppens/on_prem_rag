"""LlamaIndex compatibility shims for API changes across versions.

StorageContext and other symbols may move between llama_index.core and
submodules. This module provides stable imports for our usage.

Import from the storage submodule directly to avoid pulling in llama_index.core
__init__ (which loads core.llms and can fail on ChatMessage in some CI setups).
"""

from __future__ import annotations

# Prefer direct import to avoid core.llms/ChatMessage chain; fall back to core
try:
    from llama_index.core.storage.storage_context import StorageContext
except ImportError:
    from llama_index.core import StorageContext

__all__ = ["StorageContext"]
