"""Domain value objects for the LLM Gateway bounded context.

These are immutable value objects that represent LLM interaction data:
prompts, completions, model identifiers, and token usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


class ModelNotFoundError(RuntimeError):
    """Raised when the configured model is not available on the provider host.

    Includes the model name, host, and raw error for diagnostic purposes.
    """

    def __init__(self, model_name: str, host: str = "", raw_error: str = "") -> None:
        self.model_name = model_name
        self.host = host
        self.raw_error = raw_error
        super().__init__(
            f"Ollama model '{model_name}' not found. "
            f"Pull it with: ollama pull {model_name} "
            f"(or set OLLAMA_MODEL to an available model, e.g. llama3.2:1b)"
        )


@dataclass(frozen=True)
class ModelIdentifier:
    """Identifies an LLM model by provider and model name.

    Examples:
        ModelIdentifier(provider="ollama", model="mistral")
        ModelIdentifier(provider="openai", model="gpt-4")
    """

    provider: str
    model: str

    @property
    def litellm_model(self) -> str:
        """Full LiteLLM model string (e.g. 'ollama/mistral')."""
        return f"{self.provider}/{self.model}"

    @property
    def backend_model_pair(self) -> str:
        """Human-readable backend/model for logging."""
        return f"{self.provider}/{self.model}"


@dataclass(frozen=True)
class Prompt:
    """A prompt to be sent to an LLM with generation parameters."""

    text: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass(frozen=True)
class TokenUsage:
    """Token usage information for a completion."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class Completion:
    """A complete (non-streaming) response from an LLM."""

    text: str
    model: str
    usage: Optional[TokenUsage] = None


@dataclass(frozen=True)
class CompletionChunk:
    """A single chunk from a streaming LLM response."""

    content: str
    finished: bool = False
