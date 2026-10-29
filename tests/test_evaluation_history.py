"""Tests for persisted evaluation run history.

As a user I want every evaluation run recorded with a run id and timestamp, so I can compare
embedding models and retrieval configs over time. Technical: JSONL history file; CLI runs use a
mocked run_evaluation, no vector store.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.evaluation import cli
from backend.evaluation.history import append_history, build_history_rows, read_history


def _report(mrr: float) -> dict:
    """Minimal run_evaluation-shaped report with a single 'dense' config."""
    return {"dense": {"results": [], "aggregates": {"mrr": mrr, "recall_at_5": 0.5, "num_queries": 2}}}


class TestBuildHistoryRows:
    """Tests for flattening a report into history rows."""

    def test_one_row_per_config_with_shared_run_metadata(self) -> None:
        """As a user I want each config's metrics tagged with the run they belong to.
        Technical: rows share run_id/timestamp and carry config name plus aggregates.
        """
        report = {**_report(0.8), "hybrid": {"results": [], "aggregates": {"mrr": 0.9}}}
        ts = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)

        rows = build_history_rows(report, dataset="bench.json", embedding_model="m", top_k=5, run_id="r1", run_timestamp=ts)

        assert [r["retrieval_config"] for r in rows] == ["dense", "hybrid"]
        assert {r["run_id"] for r in rows} == {"r1"}
        assert rows[0]["run_timestamp"] == "2026-10-29T12:00:00+00:00"
        assert rows[0]["mrr"] == 0.8
        assert rows[0]["dataset"] == "bench.json"
        assert rows[0]["embedding_model"] == "m"
        assert rows[0]["top_k"] == 5

    def test_generates_run_id_when_not_given(self) -> None:
        """Technical: two builds without run_id get distinct uuids."""
        a = build_history_rows(_report(0.1), dataset="d", embedding_model="m", top_k=5)
        b = build_history_rows(_report(0.1), dataset="d", embedding_model="m", top_k=5)
        assert a[0]["run_id"] != b[0]["run_id"]


class TestAppendHistory:
    """Tests for the JSONL history file."""

    def test_appends_and_creates_parent_dir(self, tmp_path: Path) -> None:
        """Technical: append creates missing dirs and never overwrites earlier rows."""
        path = tmp_path / "eval-runs" / "history.jsonl"
        append_history([{"run_id": "a"}], path)
        append_history([{"run_id": "b"}], path)
        assert [r["run_id"] for r in read_history(path)] == ["a", "b"]

    def test_read_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Technical: no history yet is not an error."""
        assert read_history(tmp_path / "none.jsonl") == []


class TestCliHistory:
    """Tests for history recording in the evaluate-rag CLI."""

    @pytest.fixture
    def run_cli(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        """Run cli.main with given args, a fake run_evaluation per config, and a fixed embedding model."""
        monkeypatch.setattr(cli, "_embedding_model_name", lambda: "test-embedder")

        def fake_run_evaluation(dataset_path, configs=None, top_k=5):
            return {c: _report(0.5)["dense"] for c in configs or ["dense"]}

        monkeypatch.setattr("backend.evaluation.runner.run_evaluation", fake_run_evaluation)

        def run(*args: str) -> int:
            monkeypatch.setattr(sys, "argv", ["evaluate-rag", "--dataset", str(tmp_path / "bench.json"), *args])
            return cli.main()

        return run

    def test_two_runs_with_different_configs_give_two_distinct_rows(
        self, run_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """As a user I want two evaluation runs to leave two comparable records.
        Technical: distinct run_ids, correct config and metadata; stdout stays the plain JSON report.
        """
        history = tmp_path / "history.jsonl"

        assert run_cli("--configs", "dense", "--history", str(history)) == 0
        stdout_first = capsys.readouterr().out
        assert run_cli("--configs", "hybrid", "--history", str(history)) == 0

        rows = read_history(history)
        assert len(rows) == 2
        assert rows[0]["run_id"] != rows[1]["run_id"]
        assert [r["retrieval_config"] for r in rows] == ["dense", "hybrid"]
        assert all(r["dataset"] == "bench.json" and r["embedding_model"] == "test-embedder" for r in rows)
        assert json.loads(stdout_first) == {"dense": _report(0.5)["dense"]}

    def test_no_history_flag_skips_recording(self, run_cli, tmp_path: Path) -> None:
        """Technical: --no-history leaves no file behind."""
        history = tmp_path / "history.jsonl"
        assert run_cli("--no-history", "--history", str(history)) == 0
        assert not history.exists()
