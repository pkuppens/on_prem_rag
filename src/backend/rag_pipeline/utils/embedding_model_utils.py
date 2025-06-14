from __future__ import annotations

"""Utilities for retrieving embedding models with caching support.

See docs/technical/EMBEDDING.md for usage examples and caching strategy.
"""

import os
from pathlib import Path

from llama_index.embeddings.huggingface import HuggingFaceEmbedding


def get_embedding_model(model_name: str, cache_dir: str | None = None) -> HuggingFaceEmbedding:
    """Return a HuggingFaceEmbedding with optional cache handling.

    The function first checks if ``model_name`` refers to an existing path.
    If so, it is loaded from disk using ``local_files_only=True``. Otherwise
    the model is loaded from Hugging Face, falling back to offline mode when
    ``TRANSFORMERS_OFFLINE=1`` is set.
    """
    local_only = os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    model_path = Path(model_name)
    if model_path.exists():
        return HuggingFaceEmbedding(model_name=str(model_path), local_files_only=True)

    return HuggingFaceEmbedding(
        model_name=model_name,
        cache_folder=cache_dir,
        local_files_only=local_only,
    )
