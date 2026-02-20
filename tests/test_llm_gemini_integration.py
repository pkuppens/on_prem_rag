"""Integration test for Google Gemini Cloud LLM via LiteLLM.

As a user I want to verify that GEMINI_API_KEY works with the RAG pipeline,
so I can switch to Google Gemini as the Cloud LLM backend.
Technical: LiteLLM completion with gemini/gemini-2.0-flash; minimal token use.
Run only during integration: uv run pytest -m cloud_llm --run-internet

Note: Test may fail with 429 RateLimitError if Gemini free tier quota is exceeded.
"""

from __future__ import annotations

import os

import pytest

# Skip entire module if GEMINI_API_KEY not set (safe for CI without the secret)
pytest.importorskip("litellm")


def _gemini_key_available() -> bool:
    """Return True if GEMINI_API_KEY is set and non-empty."""
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


@pytest.mark.cloud_llm
@pytest.mark.internet
@pytest.mark.skipif(not _gemini_key_available(), reason="GEMINI_API_KEY not set; needed for Gemini integration")
class TestGeminiCloudLLMIntegration:
    """Validate Google Gemini integration via LiteLLM.

    Runs only when GEMINI_API_KEY is set (e.g. in CI as repo secret for PR validation).
    Uses a minimal prompt to limit token cost (Gemini free tier).
    """

    def test_gemini_completion_returns_non_empty_response(self) -> None:
        """As a user I want a simple Q&A to validate Gemini connectivity,
        so I can confirm API key and model work.
        Technical: One completion with short prompt; max_tokens=5; non-empty response.
        """
        import litellm

        from backend.rag_pipeline.config.llm_config import get_litellm_model_for_backend

        prompt = "Reply with exactly one word: OK"
        model = get_litellm_model_for_backend("gemini")

        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
        )
        choice = response.choices[0] if response.choices else None
        assert choice is not None
        content = getattr(choice.message, "content", None) or str(choice.message)
        assert content and len(content.strip()) > 0, "Expected non-empty response from Gemini"
