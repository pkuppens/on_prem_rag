# src/backend/rag_pipeline/agents/llm_selector.py
"""
Agent-specific LLM routing and selection.

This module provides intelligent LLM selection based on agent roles and task
requirements, allowing different agents to use optimized models for their
specific responsibilities.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from crewai import LLM

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for an LLM instance."""

    provider: str  # "ollama", "openai", "anthropic", etc.
    model: str  # Model identifier (e.g., "llama3.2:3b", "gpt-4o")
    temperature: float = 0.7
    base_url: str | None = None
    api_key: str | None = None
    max_tokens: int | None = None
    top_p: float | None = None


# Default agent-to-LLM mapping optimized for task requirements
# Uses locally available models with provider diversity (llama, mistral, deepseek)
# All models run locally via Ollama - no external API calls
DEFAULT_AGENT_LLM_MAPPING: dict[str, LLMConfig] = {
    "PreprocessingAgent": LLMConfig(
        provider="ollama",
        model="llama3.2:latest",  # 2GB - fast, good for text cleanup
        temperature=0.3,  # Lower temperature for consistent preprocessing
        base_url="http://localhost:11434",
    ),
    "LanguageAssessorAgent": LLMConfig(
        provider="ollama",
        model="mistral:latest",  # 4.1GB - excellent for language analysis
        temperature=0.3,
        base_url="http://localhost:11434",
    ),
    "ClinicalExtractorAgent": LLMConfig(
        provider="ollama",
        model="deepseek-r1:latest",  # 4.7GB - reasoning model for extraction
        temperature=0.2,  # Low temperature for accuracy
        base_url="http://localhost:11434",
    ),
    "SummarizationAgent": LLMConfig(
        provider="ollama",
        model="llama3.1:latest",  # 4.7GB - good balance for summarization
        temperature=0.5,
        base_url="http://localhost:11434",
    ),
    "QualityControlAgent": LLMConfig(
        provider="ollama",
        model="mistral:latest",  # 4.1GB - reliable for QC tasks
        temperature=0.1,  # Very low temperature for consistent QC
        base_url="http://localhost:11434",
    ),
}

# Environment variable overrides for agent-specific models
# Format: AGENT_LLM_<AGENT_NAME>_MODEL, AGENT_LLM_<AGENT_NAME>_PROVIDER, etc.
ENV_PREFIX = "AGENT_LLM_"


class AgentLLMSelector:
    """
    Selects and configures LLMs based on agent type and requirements.

    Supports:
    - Default mappings optimized per agent type
    - Environment variable overrides
    - Runtime configuration updates
    - Fallback to a default LLM when agent-specific config unavailable
    """

    def __init__(
        self,
        custom_mapping: dict[str, LLMConfig] | None = None,
        default_config: LLMConfig | None = None,
    ):
        """
        Initialize the LLM selector.

        Args:
            custom_mapping: Optional custom agent-to-LLM mapping that overrides defaults.
            default_config: Default LLM config used when no agent-specific config exists.
        """
        # Start with default mapping
        self._mapping: dict[str, LLMConfig] = DEFAULT_AGENT_LLM_MAPPING.copy()

        # Override with custom mapping if provided
        if custom_mapping:
            self._mapping.update(custom_mapping)

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Default fallback config
        self._default_config = default_config or LLMConfig(
            provider="ollama",
            model="llama3.2:3b",
            temperature=0.7,
            base_url="http://localhost:11434",
        )

        # Cache of created LLM instances
        self._llm_cache: dict[str, LLM] = {}

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to the mapping."""
        for agent_name in list(self._mapping.keys()):
            # Normalize agent name for env var (e.g., PreprocessingAgent -> PREPROCESSING_AGENT)
            env_name = agent_name.upper()
            if not env_name.endswith("_AGENT"):
                env_name = f"{env_name}_AGENT"

            # Check for overrides
            model_env = os.getenv(f"{ENV_PREFIX}{env_name}_MODEL")
            provider_env = os.getenv(f"{ENV_PREFIX}{env_name}_PROVIDER")
            temp_env = os.getenv(f"{ENV_PREFIX}{env_name}_TEMPERATURE")
            base_url_env = os.getenv(f"{ENV_PREFIX}{env_name}_BASE_URL")

            if any([model_env, provider_env, temp_env, base_url_env]):
                current = self._mapping[agent_name]
                self._mapping[agent_name] = LLMConfig(
                    provider=provider_env or current.provider,
                    model=model_env or current.model,
                    temperature=float(temp_env) if temp_env else current.temperature,
                    base_url=base_url_env or current.base_url,
                    api_key=current.api_key,
                    max_tokens=current.max_tokens,
                    top_p=current.top_p,
                )
                logger.info(f"Applied env overrides for {agent_name}")

    def get_config(self, agent_name: str) -> LLMConfig:
        """
        Get the LLM configuration for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., "PreprocessingAgent").

        Returns:
            LLMConfig for the agent, or default config if not found.
        """
        config = self._mapping.get(agent_name, self._default_config)
        logger.debug(f"LLM config for {agent_name}: {config.provider}/{config.model}")
        return config

    def create_llm(self, agent_name: str, use_cache: bool = True) -> LLM:
        """
        Create an LLM instance for a specific agent.

        Args:
            agent_name: Name of the agent.
            use_cache: If True, returns cached instance if available.

        Returns:
            Configured LLM instance.
        """
        if use_cache and agent_name in self._llm_cache:
            logger.debug(f"Using cached LLM for {agent_name}")
            return self._llm_cache[agent_name]

        config = self.get_config(agent_name)
        llm = self._create_llm_from_config(config)

        if use_cache:
            self._llm_cache[agent_name] = llm

        return llm

    def _create_llm_from_config(self, config: LLMConfig) -> LLM:
        """Create an LLM instance from a configuration."""
        # Build model string based on provider
        if config.provider == "ollama":
            model_string = f"ollama/{config.model}"
        elif config.provider == "openai":
            model_string = config.model  # OpenAI models don't need prefix
        elif config.provider == "anthropic":
            model_string = config.model
        else:
            model_string = f"{config.provider}/{config.model}"

        # Build kwargs for LLM constructor
        kwargs: dict[str, Any] = {
            "model": model_string,
            "temperature": config.temperature,
        }

        if config.base_url:
            kwargs["base_url"] = config.base_url

        if config.api_key:
            kwargs["api_key"] = config.api_key

        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens

        if config.top_p is not None:
            kwargs["top_p"] = config.top_p

        return LLM(**kwargs)

    def update_mapping(self, agent_name: str, config: LLMConfig) -> None:
        """
        Update the LLM mapping for a specific agent.

        Args:
            agent_name: Name of the agent.
            config: New LLM configuration.
        """
        self._mapping[agent_name] = config
        # Invalidate cache for this agent
        self._llm_cache.pop(agent_name, None)
        logger.info(f"Updated LLM mapping for {agent_name}: {config.provider}/{config.model}")

    def get_all_mappings(self) -> dict[str, LLMConfig]:
        """Get all current agent-to-LLM mappings."""
        return self._mapping.copy()

    def clear_cache(self) -> None:
        """Clear the LLM instance cache."""
        self._llm_cache.clear()
        logger.debug("Cleared LLM cache")


# Global selector instance (singleton pattern)
_global_selector: AgentLLMSelector | None = None


def get_llm_selector() -> AgentLLMSelector:
    """Get the global AgentLLMSelector instance."""
    global _global_selector
    if _global_selector is None:
        _global_selector = AgentLLMSelector()
    return _global_selector


def get_llm_for_agent(agent_name: str) -> LLM:
    """
    Convenience function to get an LLM for a specific agent.

    Args:
        agent_name: Name of the agent.

    Returns:
        Configured LLM instance.
    """
    return get_llm_selector().create_llm(agent_name)
