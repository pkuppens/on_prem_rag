#!/usr/bin/env python3
"""Patch llama_index for CI compatibility.

1. llama_index.llms.huggingface: re-export HuggingFaceInferenceAPI (moved to
   llama-index-llms-huggingface-api).
2. llama_index.core.llms: wrap types import in try/except for ChatMessage
   (some CI environments fail the normal import from base.llms.types).

Run after: uv sync --dev
Run before: pytest
"""

from __future__ import annotations

import site
import sys
from pathlib import Path


def _patch_core_llms() -> int:
    """Patch llama_index.core.llms to handle ChatMessage import failures."""
    init_py = None
    for sp in site.getsitepackages():
        candidate = Path(sp) / "llama_index" / "core" / "llms" / "__init__.py"
        if candidate.exists():
            init_py = candidate
            break
    if init_py is None:
        return 0

    content = init_py.read_text()
    if "except ImportError" in content and "ChatMessage" in content:
        print("llama_index.core.llms already patched for ChatMessage")
        return 0

    old_block = """from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseAsyncGen,
    CompletionResponseGen,
    ImageBlock,
    LLMMetadata,
    MessageRole,
    TextBlock,
    AudioBlock,
    VideoBlock,
    DocumentBlock,
    CachePoint,
    CacheControl,
    CitableBlock,
    CitationBlock,
)"""
    new_block = """try:
    from llama_index.core.base.llms.types import (
        ChatMessage,
        ChatResponse,
        ChatResponseAsyncGen,
        ChatResponseGen,
        CompletionResponse,
        CompletionResponseAsyncGen,
        CompletionResponseGen,
        ImageBlock,
        LLMMetadata,
        MessageRole,
        TextBlock,
        AudioBlock,
        VideoBlock,
        DocumentBlock,
        CachePoint,
        CacheControl,
        CitableBlock,
        CitationBlock,
    )
except ImportError as _e:
    # Fallback: try loading types module (can help with circular import in CI)
    import importlib.util
    _spec = importlib.util.find_spec("llama_index.core.base.llms.types")
    _llm_types = None
    if _spec and _spec.loader:
        _llm_types = importlib.util.module_from_spec(_spec)
        try:
            _spec.loader.exec_module(_llm_types)
        except Exception:
            _llm_types = None
    if not _llm_types:
        raise ImportError("llama_index.core.base.llms.types could not be loaded") from _e
    ChatMessage = getattr(_llm_types, "ChatMessage", None)
    ChatResponse = getattr(_llm_types, "ChatResponse", None)
    ChatResponseAsyncGen = getattr(_llm_types, "ChatResponseAsyncGen", None)
    ChatResponseGen = getattr(_llm_types, "ChatResponseGen", None)
    CompletionResponse = getattr(_llm_types, "CompletionResponse", None)
    CompletionResponseAsyncGen = getattr(_llm_types, "CompletionResponseAsyncGen", None)
    CompletionResponseGen = getattr(_llm_types, "CompletionResponseGen", None)
    ImageBlock = getattr(_llm_types, "ImageBlock", None)
    LLMMetadata = getattr(_llm_types, "LLMMetadata", None)
    MessageRole = getattr(_llm_types, "MessageRole", None)
    TextBlock = getattr(_llm_types, "TextBlock", None)
    AudioBlock = getattr(_llm_types, "AudioBlock", None)
    VideoBlock = getattr(_llm_types, "VideoBlock", None)
    DocumentBlock = getattr(_llm_types, "DocumentBlock", None)
    CachePoint = getattr(_llm_types, "CachePoint", None)
    CacheControl = getattr(_llm_types, "CacheControl", None)
    CitableBlock = getattr(_llm_types, "CitableBlock", None)
    CitationBlock = getattr(_llm_types, "CitationBlock", None)"""

    if old_block not in content:
        # Format might differ (e.g. different line breaks)
        print("llama_index.core.llms: unexpected format, skipping ChatMessage patch", file=sys.stderr)
        return 0

    init_py.write_text(content.replace(old_block, new_block))
    print("Patched llama_index.core.llms for ChatMessage import fallback")
    return 0


def _patch_huggingface() -> int:
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

    # Add re-export: try huggingface_api package, stub if not installed
    patch = '''
try:
    from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
except ImportError:
    HuggingFaceInferenceAPI = None  # type: ignore[misc,assignment]  # noqa: N816

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


def main() -> int:
    """Run all patches."""
    _patch_core_llms()
    return _patch_huggingface()


if __name__ == "__main__":
    sys.exit(main())
