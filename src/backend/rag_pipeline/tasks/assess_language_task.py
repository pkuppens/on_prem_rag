# src/backend/rag_pipeline/tasks/assess_language_task.py
"""
Compatibility shim — re-exports from backend.medical_agents.tasks.assess_language_task.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents.tasks directly.
"""

from backend.medical_agents.tasks.assess_language_task import *  # noqa: F401, F403
