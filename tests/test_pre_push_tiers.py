"""Tests for scripts/pre_push_tiers.py (#212): capability-gated pre-push test tiers."""

import subprocess
import sys

import pytest

from scripts import pre_push_tiers
from scripts.pre_push_tiers import Capabilities, Tier, last_summary_line, plan_tiers, render_report, report_path


def tier_by_name(tiers: list[Tier], name: str) -> Tier:
    return next(t for t in tiers if t.name == name)


class TestPlanTiers:
    """As a developer I want heavy tiers to run only where the hardware supports them."""

    def test_dev_pc_runs_every_tier(self):
        """With a GPU and Ollama, all four tiers are scheduled."""
        tiers = plan_tiers(Capabilities(gpu=None, ollama=None), fast_only=False)
        assert [t.name for t in tiers] == ["fast", "slow", "ollama", "e2e"]
        assert all(t.status == "not run" and t.skip_reason is None for t in tiers)

    def test_machine_without_gpu_or_ollama_runs_fast_only_and_says_why(self):
        """Without capabilities, heavy tiers are skipped with the detection reason."""
        tiers = plan_tiers(Capabilities(gpu="no NVIDIA GPU", ollama="Ollama unreachable"), fast_only=False)
        assert tier_by_name(tiers, "fast").skip_reason is None
        assert tier_by_name(tiers, "slow").skip_reason == "no NVIDIA GPU"
        assert tier_by_name(tiers, "ollama").skip_reason == "Ollama unreachable"
        assert tier_by_name(tiers, "e2e").skip_reason == "Ollama unreachable"
        assert all(t.status == "skipped" for t in tiers[1:])

    def test_pre_push_fast_opts_out_of_heavy_tiers(self):
        """PRE_PUSH_FAST=1 skips heavy tiers even on the dev PC."""
        tiers = plan_tiers(Capabilities(gpu=None, ollama=None), fast_only=True)
        assert tier_by_name(tiers, "fast").skip_reason is None
        assert {t.skip_reason for t in tiers[1:]} == {"PRE_PUSH_FAST=1"}

    def test_tiers_do_not_overlap_and_never_run_network_tests(self):
        """Each pytest tier excludes internet/docker/cloud_llm, and fast excludes slow and ollama."""
        tiers = plan_tiers(Capabilities(gpu=None, ollama=None), fast_only=False)
        markers = {t.name: t.command[-1] for t in tiers if "pytest" in t.command}
        assert all("not internet and not docker and not cloud_llm" in m for m in markers.values())
        assert markers["fast"].startswith("not slow and not ollama")
        assert markers["slow"].startswith("slow and not ollama")
        assert markers["ollama"].startswith("ollama")
        assert "--skip-streamlit" in tier_by_name(tiers, "e2e").command


class TestReportPath:
    """As a reviewer I want the report file prefixed with the issue number so I can match it to its PR."""

    @pytest.mark.parametrize(
        ("branch", "name"),
        [
            ("feature/212-pre-push-heavy-tiers", "212-local-test-report.md"),
            ("task/88-fix", "88-local-test-report.md"),
            ("chore/tidy-docs", "chore-tidy-docs-local-test-report.md"),
            ("", "detached-local-test-report.md"),
        ],
    )
    def test_prefix(self, branch: str, name: str):
        assert report_path(branch).name == name


class TestSummaryAndReport:
    def test_extracts_pytest_summary_line(self):
        output = "collected 3 items\n...\n======= 3 passed, 1 skipped in 2.10s =======\n"
        assert last_summary_line(output) == "3 passed, 1 skipped in 2.10s"

    def test_falls_back_to_last_line_for_non_pytest_output(self):
        assert last_summary_line("[1/6] Ollama\n\nE2E smoke test passed.\n") == "E2E smoke test passed."

    def test_report_lists_every_tier_and_overall_result(self):
        tiers = plan_tiers(Capabilities(gpu="no NVIDIA GPU", ollama=None), fast_only=False)
        tier_by_name(tiers, "fast").status = "passed"
        tier_by_name(tiers, "ollama").status = "failed"
        report = render_report(tiers, Capabilities(gpu="no NVIDIA GPU", ollama=None, notes=["GPU: none"]), "b", "abc1234")
        assert "FAILED" in report.splitlines()[0]
        assert "| slow | skipped | - | no NVIDIA GPU |" in report
        assert "| e2e | not run |" in report
        assert "`abc1234`" in report and "- GPU: none" in report


class TestDetectGpu:
    def test_no_nvidia_smi(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(pre_push_tiers.shutil, "which", lambda _: None)
        reason, _ = pre_push_tiers.detect_gpu()
        assert reason and "nvidia-smi not on PATH" in reason

    def test_gpu_listed(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(pre_push_tiers.shutil, "which", lambda _: "nvidia-smi")
        listing = "GPU 0: NVIDIA GeForce RTX 4090 (UUID: GPU-x)\n"
        monkeypatch.setattr(pre_push_tiers.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=listing))
        assert pre_push_tiers.detect_gpu() == (None, "GPU 0: NVIDIA GeForce RTX 4090")


class TestRunTier:
    def test_failing_command_marks_tier_failed(self):
        tier = Tier("x", [sys.executable, "-c", "print('boom'); raise SystemExit(1)"])
        assert pre_push_tiers.run_tier(tier) is False
        assert tier.status == "failed" and tier.summary == "boom"

    def test_no_tests_collected_is_not_a_failure(self):
        tier = Tier("x", [sys.executable, "-c", "raise SystemExit(5)"])
        assert pre_push_tiers.run_tier(tier) is True


class TestDryRun:
    """As a maintainer I want a dry run from the hook to block the push, so it is never a gate bypass."""

    @pytest.mark.parametrize(("argv", "expected"), [(["--dry-run"], 0), (["--dry-run", "--hook"], 1)])
    def test_exit_code(self, monkeypatch: pytest.MonkeyPatch, argv: list[str], expected: int):
        monkeypatch.setattr(sys, "argv", ["pre_push_tiers.py", "--fast", *argv])
        assert pre_push_tiers.main() == expected
