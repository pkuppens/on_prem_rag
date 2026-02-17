from __future__ import annotations

"""LLM provider abstractions.

This module implements a minimal provider factory used in
[FEAT-003](../../../project/program/features/FEAT-003.md).
See docs/technical/LLM.md for design details.
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


__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "LlamaCppProvider",
    "HuggingFaceProvider",
    "LLMProviderFactory",
]
