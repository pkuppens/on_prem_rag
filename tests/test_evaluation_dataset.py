"""Tests for RAG evaluation dataset schema and validation.

As a user I want evaluation datasets to conform to a defined schema, so I can run
reliable benchmarks across different configurations.
Technical: Validates question, ground_truth_contexts, expected_answer structure.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _load_benchmark(path: Path) -> list[dict]:
    """Load benchmark JSON from path."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _validate_item(item: dict) -> list[str]:
    """Validate a single benchmark item. Returns list of error messages."""
    errors = []
    if not isinstance(item, dict):
        return ["Item must be a dict"]
    if "question" not in item:
        errors.append("Missing 'question'")
    elif not isinstance(item["question"], str) or not item["question"].strip():
        errors.append("'question' must be non-empty string")
    if "ground_truth_contexts" not in item:
        errors.append("Missing 'ground_truth_contexts'")
    elif not isinstance(item["ground_truth_contexts"], list):
        errors.append("'ground_truth_contexts' must be a list")
    elif not item["ground_truth_contexts"]:
        errors.append("'ground_truth_contexts' must be non-empty")
    else:
        for i, ctx in enumerate(item["ground_truth_contexts"]):
            if not isinstance(ctx, str) or not ctx.strip():
                errors.append(f"ground_truth_contexts[{i}] must be non-empty string")
    if "expected_answer" in item and item["expected_answer"] is not None:
        if not isinstance(item["expected_answer"], str):
            errors.append("'expected_answer' must be string when present")
        elif not item["expected_answer"].strip():
            errors.append("'expected_answer' must be non-empty when present")
    return errors


class TestEvaluationDatasetSchema:
    """Schema validation for RAG evaluation benchmarks."""

    @pytest.fixture
    def benchmark_path(self) -> Path:
        """Path to healthcare benchmark fixture."""
        return Path(__file__).parent / "fixtures" / "healthcare_benchmark.json"

    def test_benchmark_file_exists(self, benchmark_path: Path) -> None:
        """As a user I want the benchmark file to exist, so I can run evaluation.
        Technical: healthcare_benchmark.json must be present.
        """
        assert benchmark_path.exists(), f"Benchmark not found: {benchmark_path}"

    def test_benchmark_valid_json(self, benchmark_path: Path) -> None:
        """As a user I want the benchmark to be valid JSON, so the runner can load it.
        Technical: File must parse as JSON array.
        """
        data = _load_benchmark(benchmark_path)
        assert isinstance(data, list), "Benchmark must be a JSON array"

    def test_benchmark_has_required_keys(self, benchmark_path: Path) -> None:
        """As a user I want each item to have question and ground_truth_contexts.
        Technical: Required keys present per RAG_EVALUATION.md schema.
        """
        data = _load_benchmark(benchmark_path)
        required = {"question", "ground_truth_contexts"}
        for i, item in enumerate(data):
            missing = required - set(item.keys())
            assert not missing, f"Item {i} missing keys: {missing}"

    def test_benchmark_item_validation(self, benchmark_path: Path) -> None:
        """As a user I want all items to pass schema validation.
        Technical: Each item must have non-empty question and ground_truth_contexts.
        """
        data = _load_benchmark(benchmark_path)
        for i, item in enumerate(data):
            errors = _validate_item(item)
            assert not errors, f"Item {i}: {errors}"

    def test_benchmark_has_thirty_plus_items(self, benchmark_path: Path) -> None:
        """As a user I want a substantial benchmark for reliable metrics.
        Technical: At least 30 triples per acceptance criteria.
        """
        data = _load_benchmark(benchmark_path)
        assert len(data) >= 30, f"Expected >= 30 items, got {len(data)}"

    def test_validate_item_helper_rejects_empty_question(self) -> None:
        """Technical: _validate_item rejects empty question."""
        errors = _validate_item({"question": "   ", "ground_truth_contexts": ["x"]})
        assert any("question" in e.lower() for e in errors)

    def test_validate_item_helper_rejects_empty_contexts(self) -> None:
        """Technical: _validate_item rejects empty ground_truth_contexts."""
        errors = _validate_item({"question": "Q?", "ground_truth_contexts": []})
        assert any("ground_truth" in e.lower() for e in errors)

    def test_validate_item_helper_accepts_valid_item(self) -> None:
        """Technical: _validate_item accepts valid item."""
        errors = _validate_item(
            {
                "question": "What is E11?",
                "ground_truth_contexts": ["E11 is type 2 diabetes."],
                "expected_answer": "E11",
            }
        )
        assert errors == []
