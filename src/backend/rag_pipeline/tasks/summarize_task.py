# src/backend/rag_pipeline/tasks/summarize_task.py
"""
Compatibility shim — re-exports from backend.medical_agents.tasks.summarize_task.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents.tasks directly.
"""

from backend.medical_agents.tasks.summarize_task import *  # noqa: F401, F403
