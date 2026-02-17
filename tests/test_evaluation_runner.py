"""Tests for RAG evaluation runner.

As a user I want the evaluation runner to work with a fixture dataset, so I can
test without ChromaDB. Technical: Uses mocked retrieval; no real vector store.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.rag_pipeline.evaluation.runner import evaluate_retrieval, run_evaluation


def _chunk(text: str) -> dict:
    """Helper to build chunk dict."""
    return {"text": text, "record_id": "x"}


class TestEvaluateRetrieval:
    """Tests for evaluate_retrieval with mock retrieve_fn."""

    def test_returns_one_result_per_dataset_item(self) -> None:
        """As a user I want one EvaluationResult per question.
        Technical: evaluate_retrieval returns len(dataset) results.
        """
        dataset = [
            {"question": "Q1?", "ground_truth_contexts": ["ctx1 long enough here"]},
            {"question": "Q2?", "ground_truth_contexts": ["ctx2 long enough here"]},
        ]

        def retrieve(query: str, top_k: int) -> list[dict]:
            if "Q1" in query:
                return [_chunk("ctx1 long enough here")]
            return [_chunk("ctx2 long enough here")]

        results = evaluate_retrieval(dataset, retrieve, top_k=5)
        assert len(results) == 2
        assert results[0].question == "Q1?"
        assert results[1].question == "Q2?"

    def test_skips_empty_question_or_contexts(self) -> None:
        """Technical: Items with empty question or ground_truth_contexts are skipped."""
        dataset = [
            {"question": "Valid?", "ground_truth_contexts": ["ctx long enough here"]},
            {"question": "", "ground_truth_contexts": ["x" * 25]},
            {"question": "Q?", "ground_truth_contexts": []},
        ]
        results = evaluate_retrieval(dataset, lambda q, k: [], top_k=5)
        assert len(results) == 1
        assert results[0].question == "Valid?"


class TestRunEvaluation:
    """Tests for run_evaluation with mocked retrieve factory."""

    @pytest.fixture
    def fixture_dataset_path(self, tmp_path: Path) -> Path:
        """Create a minimal valid benchmark JSON file."""
        data = [
            {
                "question": "What is E11?",
                "ground_truth_contexts": ["E11 is type 2 diabetes code with enough chars here"],
            },
            {
                "question": "What is metformin?",
                "ground_truth_contexts": ["Metformin is indicated for type 2 diabetes with enough chars"],
            },
        ]
        p = tmp_path / "benchmark.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_run_evaluation_returns_per_config_results(self, fixture_dataset_path: Path) -> None:
        """As a user I want run_evaluation to return results per config.
        Technical: Returns dict with config_name -> results, aggregates.
        """

        def make_retrieve(config_name: str):
            def retrieve(query: str, top_k: int) -> list[dict]:
                return [_chunk("E11 is type 2 diabetes code with enough chars here")]

            return retrieve

        report = run_evaluation(
            dataset_path=fixture_dataset_path,
            configs=["dense", "hybrid"],
            retrieve_fn_factory=make_retrieve,
            top_k=5,
        )
        assert "dense" in report
        assert "hybrid" in report
        assert "results" in report["dense"]
        assert "aggregates" in report["dense"]
        assert len(report["dense"]["results"]) == 2
        assert "mrr" in report["dense"]["aggregates"]
        assert "recall_at_5" in report["dense"]["aggregates"]
        assert "num_queries" in report["dense"]["aggregates"]

    def test_run_evaluation_file_not_found_raises(self) -> None:
        """Technical: FileNotFoundError when dataset path does not exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            run_evaluation(
                dataset_path="/nonexistent/benchmark.json",
                configs=["dense"],
                retrieve_fn_factory=lambda c: lambda q, k: [],
            )

    def test_run_evaluation_invalid_json_raises(self, tmp_path: Path) -> None:
        """Technical: ValueError when JSON is not an array."""
        p = tmp_path / "bad.json"
        p.write_text('{"not": "array"}', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON array"):
            run_evaluation(
                dataset_path=p,
                configs=["dense"],
                retrieve_fn_factory=lambda c: lambda q, k: [],
            )
