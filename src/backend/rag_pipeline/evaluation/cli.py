"""Compatibility shim — re-exports from new Evaluation BC location.

The evaluation package has moved to ``backend.evaluation``.
This shim preserves ``from backend.rag_pipeline.evaluation.cli import ...``.
"""

from backend.evaluation.cli import main  # noqa: F401
