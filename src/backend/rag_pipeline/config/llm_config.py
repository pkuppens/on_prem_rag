"""Compatibility shim — re-exports from the new LLM Gateway bounded context.

This file is kept for backward compatibility during the migration.
Import from ``backend.llm_gateway.infrastructure`` directly for new code.
"""

from backend.llm_gateway.infrastructure import *  # noqa: F401, F403

__all__ = [
    "LLMConfig",
    "get_llm_config",
    "check_data_sovereignty",
    "get_model_for_backend",
    "get_litellm_model_for_backend",
    "DEFAULT_BACKEND",
    "DEFAULT_MODEL",
    "BACKEND_TO_PREFIX",
    "CLOUD_BACKENDS",
    "BACKEND_DEFAULT_MODELS",
    "BACKEND_MODEL_ENV_VARS",
]
