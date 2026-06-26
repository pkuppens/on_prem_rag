"""Compatibility shim — re-exports from new Evaluation BC location.

The evaluation package has moved to ``backend.evaluation``.
This shim preserves imports from the old ``backend.rag_pipeline.evaluation`` path.
"""

from backend.evaluation.metrics import (  # noqa: F401
    EvaluationResult,
    compute_aggregates,
    hit_rate_at_k,
    mrr,
    precision_at_k,
    recall_at_k,
)

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "mrr",
    "hit_rate_at_k",
    "EvaluationResult",
    "compute_aggregates",
]
