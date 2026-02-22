from __future__ import annotations

"""Utilities for retrieving embedding models with in-process caching.

The embedding model is loaded once per (model_name, cache_dir) and reused for
all subsequent calls. This keeps the model hot in memory and avoids the
~20-30s cold-start on each document in a batch.

See docs/technical/EMBEDDING.md for usage examples and caching strategy.
"""

import logging
import os
from pathlib import Path
from threading import Lock

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# In-process cache: (model_name, cache_dir) -> HuggingFaceEmbedding
_model_cache: dict[tuple[str, str], HuggingFaceEmbedding] = {}
_cache_lock = Lock()
_logger = logging.getLogger(__name__)


def get_embedding_model(model_name: str, cache_dir: str | None = None) -> HuggingFaceEmbedding:
    """Return a HuggingFaceEmbedding, reusing a cached instance when available.

    The model is loaded once per (model_name, cache_dir) and kept in memory.
    Subsequent calls return the cached instance, avoiding ~20-30s cold-start
    per document in a batch.

    The function first checks if ``model_name`` refers to an existing path.
    If so, it is loaded from disk using ``local_files_only=True``. Otherwise
    the model is loaded from Hugging Face, falling back to offline mode when
    ``TRANSFORMERS_OFFLINE=1`` is set.
    """
    cache_key = (model_name, cache_dir or "")
    with _cache_lock:
        if cache_key in _model_cache:
            _logger.info("INGEST: embedding model cache hit, model=%s", model_name)
            return _model_cache[cache_key]

        local_only = os.environ.get("TRANSFORMERS_OFFLINE") == "1"
        model_path = Path(model_name)
        if model_path.exists():
            model = HuggingFaceEmbedding(model_name=str(model_path), local_files_only=True)
        else:
            model = HuggingFaceEmbedding(
                model_name=model_name,
                cache_folder=cache_dir,
                local_files_only=local_only,
            )
        _model_cache[cache_key] = model
        return model


def clear_embedding_model_cache() -> None:
    """Clear the in-process embedding model cache.

    Use when switching models or freeing memory. Next get_embedding_model call
    will load from disk again.
    """
    with _cache_lock:
        _model_cache.clear()
