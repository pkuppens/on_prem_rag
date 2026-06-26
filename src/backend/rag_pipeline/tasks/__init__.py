# src/backend/rag_pipeline/tasks/__init__.py
"""
Compatibility shim — re-exports from backend.medical_agents.tasks.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents.tasks directly.
"""

from backend.medical_agents.tasks import *  # noqa: F401, F403
