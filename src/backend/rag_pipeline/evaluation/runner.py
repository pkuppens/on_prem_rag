"""Compatibility shim — re-exports from new Evaluation BC location.

The evaluation package has moved to ``backend.evaluation``.
This shim preserves ``from backend.rag_pipeline.evaluation.runner import ...``.
"""

from backend.evaluation.runner import (  # noqa: F401
    evaluate_retrieval,
    run_evaluation,
)
