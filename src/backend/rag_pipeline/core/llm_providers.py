from __future__ import annotations

"""LLM provider abstractions.

This module implements a minimal provider factory used in
[FEAT-003](../../../project/program/features/FEAT-003.md).
See docs/technical/LLM.md for design details.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_answer(self, prompt: str) -> str:
        """Return an answer for the given prompt."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, config: dict) -> None:
        self.model_name = model_name
        self.config = config

    def generate_answer(self, prompt: str) -> str:
        return f"Ollama({self.model_name}): {prompt[:10]}..."


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
