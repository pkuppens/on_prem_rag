"""LiteLLM-based LLM provider with multi-backend support.

Supports Ollama, OpenAI, Anthropic, Azure, HuggingFace, and Gemini
via the unified LiteLLM interface. Configure via LLM_BACKEND and LLM_MODEL.
"""

from __future__ import annotations

from backend.llm_gateway.domain.interfaces import LLMProvider, StreamingLLMProvider


class LiteLLMProvider(StreamingLLMProvider):
    """LLM provider using LiteLLM for unified multi-backend support.

    Supports ollama, openai, anthropic, azure, huggingface, gemini.
    """

    def __init__(self, model: str, api_base: str | None = None) -> None:
        """Initialize LiteLLM provider.

        Args:
            model: LiteLLM model string (e.g. 'ollama/mistral', 'openai/gpt-4').
            api_base: Optional API base URL (used for Ollama).
        """
        self.model = model
        self.api_base = api_base

    def generate_answer(self, prompt: str) -> str:
        """Generate an answer using LiteLLM completion.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            Generated answer text.

        Raises:
            RuntimeError: If completion fails.
        """
        import litellm

        try:
            kwargs: dict = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            if self.api_base:
                kwargs["api_base"] = self.api_base

            response = litellm.completion(**kwargs)
            choice = response.choices[0] if response.choices else None
            if not choice or not getattr(choice, "message", None):
                raise RuntimeError("Empty or invalid response from LLM")
            content = choice.message.content if hasattr(choice.message, "content") else str(choice.message)
            return (content or "").strip()
        except Exception as e:
            raise RuntimeError(f"LiteLLM completion failed: {e}") from e

    def generate_answer_stream(self, prompt: str):
        """Stream answer tokens from the LLM provider.

        Yields partial content as the provider sends it (token- or chunk-level).
        We pass through what the provider delivers; we never simulate streaming.
        If the provider does not support streaming, callers should use
        generate_answer() instead.

        Args:
            prompt: The prompt to send to the LLM.

        Yields:
            Partial content strings as they arrive from the provider.

        Raises:
            RuntimeError: If streaming fails.
        """
        import litellm

        try:
            kwargs: dict = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }
            if self.api_base:
                kwargs["api_base"] = self.api_base

            stream = litellm.completion(**kwargs)
            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue
                delta = getattr(choice, "delta", None)
                if not delta:
                    continue
                content = getattr(delta, "content", None) or (delta.get("content") if isinstance(delta, dict) else None)
                if content:
                    yield content
        except Exception as e:
            raise RuntimeError(f"LiteLLM streaming failed: {e}") from e

    async def health_check(self) -> bool:
        """Check provider health via a minimal completion.

        For Ollama, uses /api/tags when api_base is set for efficiency.
        For other backends, performs a minimal completion (may incur cost).
        """
        if self.api_base:
            import httpx

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(f"{self.api_base.rstrip('/')}/api/tags")
                    return r.status_code == 200
            except (httpx.RequestError, httpx.TimeoutException):
                return False

        import litellm

        try:
            litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
