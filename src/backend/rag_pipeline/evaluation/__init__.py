"""RAG evaluation framework.

Batch evaluation of retrieval and generation quality.
See docs/technical/RAG_EVALUATION.md for schema and usage.
"""

from backend.rag_pipeline.evaluation.metrics import (
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
