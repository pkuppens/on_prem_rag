from __future__ import annotations

"""LLM provider abstractions.

This module implements a minimal provider factory used in
[FEAT-003](../../../project/program/features/FEAT-003.md).
See docs/technical/LLM.md for design details.

Supports Ollama, OpenAI, Anthropic, Azure, and HuggingFace via LiteLLM.
Configure via LLM_BACKEND and LLM_MODEL env vars.
"""

from abc import ABC, abstractmethod


class ModelNotFoundError(RuntimeError):
    """Raised when the configured Ollama model is not available."""

    def __init__(self, model_name: str, host: str, raw_error: str = "") -> None:
        self.model_name = model_name
        self.host = host
        self.raw_error = raw_error
        super().__init__(
            f"Ollama model '{model_name}' not found. "
            f"Pull it with: ollama pull {model_name} "
            f"(or set OLLAMA_MODEL to an available model, e.g. llama3.2:1b)"
        )


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_answer(self, prompt: str) -> str:
        """Return an answer for the given prompt."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is healthy."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, config: dict) -> None:
        self.model_name = model_name
        self.config = config
        self.host = config.get("host", "http://localhost:11434")

    def generate_answer(self, prompt: str) -> str:
        """Generate an answer using Ollama LLM.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Generated answer text

        Raises:
            RuntimeError: If LLM service is unavailable or returns an error
        """
        import json

        import httpx

        try:
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1000},
            }

            # Make request to Ollama API
            with httpx.Client(timeout=30.0) as client:
                response = client.post(f"{self.host}/api/generate", json=payload, headers={"Content-Type": "application/json"})
                response.raise_for_status()

                # Parse response
                result = response.json()

                if "response" not in result:
                    raise RuntimeError("Invalid response format from Ollama")

                return result["response"].strip()

        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to connect to Ollama service: {str(e)}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404 and "not found" in (e.response.text or "").lower():
                raise ModelNotFoundError(
                    model_name=self.model_name,
                    host=self.host,
                    raw_error=e.response.text,
                ) from e
            raise RuntimeError(f"Ollama API error: {e.response.status_code} - {e.response.text}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Ollama response: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error during answer generation: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy.

        Returns:
            True if service is available, False otherwise
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False


class LlamaCppProvider(LLMProvider):
    def __init__(self, model_name: str, config: dict) -> None:
        self.model_name = model_name
        self.config = config

    def generate_answer(self, prompt: str) -> str:
        return f"llama.cpp({self.model_name}): {prompt[:10]}..."


class HuggingFaceProvider(LLMProvider):
    def __init__(self, model_name: str, config: dict) -> None:
        self.model_name = model_name
        self.config = config

    def generate_answer(self, prompt: str) -> str:
        return f"HF({self.model_name}): {prompt[:10]}..."


class LiteLLMProvider(LLMProvider):
    """LLM provider using LiteLLM for unified multi-backend support.

    Supports ollama, openai, anthropic, azure, huggingface.
    Configure via LLM_BACKEND and LLM_MODEL (or OLLAMA_MODEL for legacy).
    """

    def __init__(self, model: str, api_base: str | None = None) -> None:
        """Initialize LiteLLM provider.

        Args:
            model: LiteLLM model string (e.g. ollama/mistral, openai/gpt-4).
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


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(provider_type: str, model_name: str, config: dict) -> LLMProvider:
        if provider_type == "ollama":
            return OllamaProvider(model_name, config)
        if provider_type == "llamacpp":
            return LlamaCppProvider(model_name, config)
        if provider_type == "huggingface":
            return HuggingFaceProvider(model_name, config)
        raise ValueError(f"Unknown provider type: {provider_type}")


def get_llm_provider_from_env() -> LLMProvider:
    """Create LLM provider from LLM_BACKEND and LLM_MODEL env vars.

    Uses LiteLLM for ollama, openai, anthropic, azure, huggingface.
    For backward compatibility, OLLAMA_MODEL and OLLAMA_BASE_URL are used when
    LLM_BACKEND is ollama and LLM_MODEL is not set.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If LLM_BACKEND is unknown.
    """
    from backend.rag_pipeline.config.llm_config import get_llm_config

    config = get_llm_config()
    return LiteLLMProvider(
        model=config.litellm_model,
        api_base=config.api_base,
    )


__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "LlamaCppProvider",
    "HuggingFaceProvider",
    "LiteLLMProvider",
    "LLMProviderFactory",
    "get_llm_provider_from_env",
]
