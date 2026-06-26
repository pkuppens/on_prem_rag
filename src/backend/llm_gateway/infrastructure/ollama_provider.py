"""Ollama-specific LLM provider implementation.

Communicates with the Ollama HTTP API for local LLM inference.
Configure via OLLAMA_BASE_URL (default: http://localhost:11434) and OLLAMA_MODEL.
"""

from __future__ import annotations

import json

import httpx

from backend.llm_gateway.domain.interfaces import LLMProvider
from backend.llm_gateway.domain.value_objects import ModelNotFoundError


class OllamaProvider(LLMProvider):
    """LLM provider that uses Ollama's local HTTP API for inference."""

    def __init__(self, model_name: str, config: dict) -> None:
        """Initialize Ollama provider.

        Args:
            model_name: Name of the Ollama model (e.g. 'mistral', 'llama3.2:1b').
            config: Dictionary with optional 'host' key (default http://localhost:11434).
        """
        self.model_name = model_name
        self.config = config
        self.host = config.get("host", "http://localhost:11434")

    def generate_answer(self, prompt: str) -> str:
        """Generate an answer using Ollama LLM.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            Generated answer text.

        Raises:
            ModelNotFoundError: If the model is not available on the Ollama host.
            RuntimeError: If LLM service is unavailable or returns an error.
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1000},
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

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
        """Check if Ollama service is healthy by listing available tags.

        Returns:
            True if service is available, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False
