"""Retrieval evaluation metrics.

Implements Precision@k, Recall@k, MRR, Hit@k.
Uses text-based matching: a retrieved chunk matches ground truth when
the shorter (normalized) string is contained in the longer (min 20 chars).
"""

from __future__ import annotations

from dataclasses import dataclass


def _normalize(text: str) -> str:
    """Normalize text for matching: lowercase, collapse whitespace."""
    return " ".join(text.lower().strip().split())


def _chunk_matches_ground_truth(chunk_text: str, ground_truth_contexts: list[str]) -> bool:
    """Check if a retrieved chunk matches any ground truth context.

    Match when: shorter of the two (normalized) is contained in the longer,
    and the shorter has at least 20 characters.
    """
    norm_chunk = _normalize(chunk_text)
    if len(norm_chunk) < 20:
        return False
    for gt in ground_truth_contexts:
        norm_gt = _normalize(gt)
        if len(norm_gt) < 20:
            continue
        shorter = norm_chunk if len(norm_chunk) <= len(norm_gt) else norm_gt
        longer = norm_gt if len(norm_chunk) <= len(norm_gt) else norm_chunk
        if shorter in longer:
            return True
    return False


def _get_hit_ranks(
    retrieved_chunks: list[dict],
    ground_truth_contexts: list[str],
) -> list[int]:
    """Return 1-based ranks where retrieved chunks match ground truth."""
    hits: list[int] = []
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        text = chunk.get("text", "") or ""
        if _chunk_matches_ground_truth(text, ground_truth_contexts):
            hits.append(rank)
    return hits


def precision_at_k(
    retrieved_chunks: list[dict],
    ground_truth_contexts: list[str],
    k: int,
) -> float:
    """Precision at k: fraction of top-k retrieved that match ground truth.

    Args:
        retrieved_chunks: List of dicts with "text" key (from retrieval).
        ground_truth_contexts: List of relevant passage texts.
        k: Cutoff rank.

    Returns:
        Value in [0, 1]. 0 if k is 0.
    """
    if k <= 0:
        return 0.0
    top_k = retrieved_chunks[:k]
    hits = sum(1 for c in top_k if _chunk_matches_ground_truth(c.get("text", "") or "", ground_truth_contexts))
    return hits / k


def recall_at_k(
    retrieved_chunks: list[dict],
    ground_truth_contexts: list[str],
    k: int,
) -> float:
    """Recall at k: fraction of ground truth contexts found in top-k.

    Args:
        retrieved_chunks: List of dicts with "text" key.
        ground_truth_contexts: List of relevant passage texts.
        k: Cutoff rank.

    Returns:
        Value in [0, 1]. 1.0 if all ground truth found in top-k.
    """
    if not ground_truth_contexts:
        return 1.0
    top_k = retrieved_chunks[:k]
    # Count how many ground truth contexts are "covered" by at least one retrieved chunk
    covered = 0
    for gt in ground_truth_contexts:
        norm_gt = _normalize(gt)
        if len(norm_gt) < 20:
            covered += 1
            continue
        for c in top_k:
            text = c.get("text", "") or ""
            if _chunk_matches_ground_truth(text, [gt]):
                covered += 1
                break
    return covered / len(ground_truth_contexts)


def mrr(
    retrieved_chunks: list[dict],
    ground_truth_contexts: list[str],
) -> float:
    """Mean Reciprocal Rank: 1/rank of first hit, 0 if none.

    Args:
        retrieved_chunks: List of dicts with "text" key.
        ground_truth_contexts: List of relevant passage texts.

    Returns:
        Value in [0, 1]. MRR = 1/2 when first hit at rank 2.
    """
    hit_ranks = _get_hit_ranks(retrieved_chunks, ground_truth_contexts)
    if not hit_ranks:
        return 0.0
    return 1.0 / min(hit_ranks)


def hit_rate_at_k(
    retrieved_chunks: list[dict],
    ground_truth_contexts: list[str],
    k: int,
) -> int:
    """Hit rate at k: 1 if any ground truth in top-k, else 0.

    Args:
        retrieved_chunks: List of dicts with "text" key.
        ground_truth_contexts: List of relevant passage texts.
        k: Cutoff rank.

    Returns:
        0 or 1.
    """
    hit_ranks = _get_hit_ranks(retrieved_chunks, ground_truth_contexts)
    return 1 if any(r <= k for r in hit_ranks) else 0


@dataclass
class EvaluationResult:
    """Per-query evaluation result with retrieval metrics."""

    question: str
    precision_at_5: float = 0.0
    recall_at_5: float = 0.0
    mrr: float = 0.0
    hit_at_5: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict for JSON output."""
        return {
            "question": self.question,
            "precision_at_5": round(self.precision_at_5, 4),
            "recall_at_5": round(self.recall_at_5, 4),
            "mrr": round(self.mrr, 4),
            "hit_at_5": self.hit_at_5,
        }


def compute_aggregates(results: list[EvaluationResult]) -> dict:
    """Aggregate metrics over a list of EvaluationResult."""
    if not results:
        return {
            "mrr": 0.0,
            "recall_at_5": 0.0,
            "hit_at_5": 0.0,
            "precision_at_5": 0.0,
            "num_queries": 0,
        }
    n = len(results)
    return {
        "mrr": sum(r.mrr for r in results) / n,
        "recall_at_5": sum(r.recall_at_5 for r in results) / n,
        "hit_at_5": sum(r.hit_at_5 for r in results) / n,
        "precision_at_5": sum(r.precision_at_5 for r in results) / n,
        "num_queries": n,
    }
