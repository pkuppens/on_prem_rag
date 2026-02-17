"""Tests for RAG evaluation metrics.

As a user I want retrieval metrics to be correct, so I can compare strategies.
Technical: Precision@k, Recall@k, MRR, Hit@k with text-based matching.
"""

from __future__ import annotations

import pytest

from backend.rag_pipeline.evaluation.metrics import (
    EvaluationResult,
    compute_aggregates,
    hit_rate_at_k,
    mrr,
    precision_at_k,
    recall_at_k,
)


def _chunk(text: str, record_id: str = "x") -> dict:
    """Helper to build chunk dict."""
    return {"text": text, "record_id": record_id}


class TestPrecisionAtK:
    """Tests for Precision@k metric."""

    def test_precision_at_3_two_hits_in_top_3(self) -> None:
        """As a user I want Precision@k to reflect retrieval accuracy.
        Technical: Precision@3 = 2/3 when 2 of top 3 match ground truth.
        Uses strings >= 20 chars for matching (per schema).
        """
        gt = ["exact match text here for precision", "another relevant passage content here"]
        retrieved = [
            _chunk("exact match text here for precision"),
            _chunk("irrelevant passage that does not match anything here"),
            _chunk("another relevant passage content here"),
        ]
        assert precision_at_k(retrieved, gt, 3) == pytest.approx(2 / 3)

    def test_precision_zero_when_no_matches(self) -> None:
        """Technical: Precision@k = 0 when no retrieved chunks match."""
        retrieved = [
            _chunk("a" * 25),
            _chunk("b" * 25),
            _chunk("c" * 25),
        ]
        gt = ["completely different text xyz not in retrieved"]
        assert precision_at_k(retrieved, gt, 3) == 0.0

    def test_precision_at_k_zero_returns_zero(self) -> None:
        """Technical: k=0 yields 0."""
        assert precision_at_k([_chunk("x")], ["x"], 0) == 0.0


class TestRecallAtK:
    """Tests for Recall@k metric."""

    def test_recall_at_5_all_gt_in_top_5(self) -> None:
        """As a user I want Recall@k to measure coverage.
        Technical: Recall@5 = 1.0 when all ground truth found in top 5.
        Uses strings >= 20 chars for matching.
        """
        gt = ["first context passage here", "second context passage here"]
        retrieved = [
            _chunk("irrelevant passage here"),
            _chunk("first context passage here"),
            _chunk("other passage content"),
            _chunk("second context passage here"),
            _chunk("more content here"),
        ]
        assert recall_at_k(retrieved, gt, 5) == pytest.approx(1.0)

    def test_recall_partial_when_one_missing(self) -> None:
        """Technical: Recall@5 = 0.5 when 1 of 2 ground truth in top 5."""
        gt = ["found context passage here", "not found anywhere in top results"]
        retrieved = [
            _chunk("found context passage here"),
            _chunk("a" * 25),
            _chunk("b" * 25),
            _chunk("c" * 25),
            _chunk("d" * 25),
        ]
        assert recall_at_k(retrieved, gt, 5) == pytest.approx(0.5)

    def test_recall_empty_gt_returns_one(self) -> None:
        """Technical: Recall = 1.0 when no ground truth (vacuous)."""
        assert recall_at_k([_chunk("x")], [], 5) == 1.0


class TestMRR:
    """Tests for Mean Reciprocal Rank."""

    def test_mrr_first_hit_at_rank_2(self) -> None:
        """As a user I want MRR to reward earlier hits.
        Technical: MRR = 1/2 when first hit at rank 2.
        """
        gt = ["target passage with enough characters here"]
        retrieved = [
            _chunk("wrong passage here"),
            _chunk("target passage with enough characters here"),
            _chunk("other passage"),
        ]
        assert mrr(retrieved, gt) == pytest.approx(0.5)

    def test_mrr_first_hit_at_rank_1(self) -> None:
        """Technical: MRR = 1.0 when first result is hit."""
        gt = ["target passage with enough characters"]
        assert mrr([_chunk("target passage with enough characters")], gt) == pytest.approx(1.0)

    def test_mrr_no_hits_returns_zero(self) -> None:
        """Technical: MRR = 0 when no matches."""
        assert mrr([_chunk("a" * 25), _chunk("b" * 25)], ["x" * 30]) == 0.0


class TestHitRateAtK:
    """Tests for Hit@k metric."""

    def test_hit_at_5_when_any_gt_in_top_5(self) -> None:
        """As a user I want Hit@k to indicate any relevant result.
        Technical: Hit@5 = 1 if any ground truth in top 5.
        """
        gt = ["target passage with enough characters"]
        retrieved = [
            _chunk("a" * 25),
            _chunk("b" * 25),
            _chunk("target passage with enough characters"),
            _chunk("d" * 25),
            _chunk("e" * 25),
        ]
        assert hit_rate_at_k(retrieved, gt, 5) == 1

    def test_hit_at_5_zero_when_no_gt_in_top_5(self) -> None:
        """Technical: Hit@5 = 0 when target not in top 5."""
        gt = ["target passage with enough characters"]
        retrieved = [
            _chunk("a" * 25),
            _chunk("b" * 25),
            _chunk("c" * 25),
            _chunk("d" * 25),
            _chunk("e" * 25),
            _chunk("target passage with enough characters"),
        ]
        assert hit_rate_at_k(retrieved, gt, 5) == 0


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_to_dict_serializable(self) -> None:
        """Technical: to_dict produces JSON-serializable structure."""
        r = EvaluationResult(question="Q?", precision_at_5=0.6, recall_at_5=0.8, mrr=0.5, hit_at_5=1)
        d = r.to_dict()
        assert d["question"] == "Q?"
        assert d["precision_at_5"] == 0.6
        assert d["recall_at_5"] == 0.8
        assert d["mrr"] == 0.5
        assert d["hit_at_5"] == 1


class TestComputeAggregates:
    """Tests for aggregate metrics."""

    def test_aggregates_average_over_results(self) -> None:
        """Technical: Aggregates are means over results."""
        results = [
            EvaluationResult("Q1", mrr=0.5, recall_at_5=0.6, hit_at_5=1, precision_at_5=0.4),
            EvaluationResult("Q2", mrr=0.5, recall_at_5=0.8, hit_at_5=1, precision_at_5=0.6),
        ]
        agg = compute_aggregates(results)
        assert agg["mrr"] == pytest.approx(0.5)
        assert agg["recall_at_5"] == pytest.approx(0.7)
        assert agg["hit_at_5"] == pytest.approx(1.0)
        assert agg["precision_at_5"] == pytest.approx(0.5)
        assert agg["num_queries"] == 2

    def test_aggregates_empty_returns_zeros(self) -> None:
        """Technical: Empty list yields zero aggregates."""
        agg = compute_aggregates([])
        assert agg["num_queries"] == 0
        assert agg["mrr"] == 0.0
        assert agg["recall_at_5"] == 0.0
