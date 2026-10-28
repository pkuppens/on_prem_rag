#!/usr/bin/env python3
"""Tiered pre-push test runner (#212): run heavy test tiers on the dev PC, fast tier everywhere.

Called by ``githooks/pre-push`` after dependency sync and ruff. Detects what this machine can run
and runs every tier it is capable of; any failing tier blocks the push.

  Tier    Runs                                              Needs
  fast    pytest -m "not internet and not slow and ..."     always
  slow    pytest -m "slow and not internet and ..."         NVIDIA GPU (nvidia-smi lists one)
  ollama  pytest -m "ollama and not internet and ..."       Ollama reachable (auto-started if installed)
  e2e     scripts/e2e_smoke.py --skip-streamlit             Ollama reachable

A machine without a GPU or Ollama still runs the fast tier and prints which tiers it skipped and why.
The run is recorded in ``tmp/github/pr-bodies/<issue>-local-test-report.md`` (issue number taken from
the branch name), ready for ``gh pr comment <PR> --body-file <report>``.

Environment:
  PRE_PUSH_FAST=1      run the fast tier only (heavy tiers reported as skipped)
  PRE_PUSH_DRY_RUN=1   detect capabilities and print the plan without running anything
                       (with --hook, as the pre-push hook calls it, the push is then blocked)

Usage:
  uv run python scripts/pre_push_tiers.py [--fast] [--dry-run] [--hook]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "tmp" / "github" / "pr-bodies"

# Never run on push: network-dependent, full Docker stack, or paid cloud LLM tests.
EXCLUDED = "not internet and not docker and not cloud_llm"


@dataclass
class Tier:
    """One test tier: the command to run and whether this machine can run it."""

    name: str
    command: list[str]
    skip_reason: str | None = None
    status: str = "not run"
    duration_s: float = 0.0
    summary: str = ""
    # A gated tier ran because its capability was detected; if every test still skips, the
    # capability is not reaching the tests (e.g. a misrouted OLLAMA_BASE_URL), so that fails.
    gated: bool = False


@dataclass
class Capabilities:
    """What this machine offers to the heavy tiers; ``None`` means present, a string says why not."""

    gpu: str | None
    ollama: str | None
    notes: list[str] = field(default_factory=list)


def pytest_command(marker: str) -> list[str]:
    return [sys.executable, "-m", "pytest", "-m", f"{marker} and {EXCLUDED}"]


def detect_gpu() -> tuple[str | None, str]:
    """Return (skip reason or None, description) based on ``nvidia-smi -L``."""
    binary = shutil.which("nvidia-smi")
    if binary is None:
        return "no NVIDIA GPU (nvidia-smi not on PATH)", ""
    try:
        out = subprocess.run([binary, "-L"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"nvidia-smi failed: {e}", ""
    gpus = [line for line in out.splitlines() if line.startswith("GPU ")]
    if not gpus:
        return "nvidia-smi lists no GPU", ""
    return None, gpus[0].split(" (UUID")[0]


def tier_env() -> dict[str, str]:
    """Environment for the tiers: OLLAMA_BASE_URL with the Docker host alias mapped to localhost.

    A ``.env`` written for containers (``host.docker.internal``) would otherwise make the native
    test process miss the local Ollama and skip every ``ollama`` test.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from e2e_smoke import resolve_ollama_url

    return {**os.environ, "OLLAMA_BASE_URL": resolve_ollama_url()}


def detect_ollama() -> tuple[str | None, str]:
    """Return (skip reason or None, description); starts a locally installed Ollama when it is not running."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from e2e_smoke import SmokeError, ensure_ollama, resolve_ollama_url

    url = resolve_ollama_url()
    try:
        models = ensure_ollama(url)
    except SmokeError as e:
        return e.problem, ""
    return None, f"{url} ({len(models)} models)"


def detect_capabilities() -> Capabilities:
    gpu_reason, gpu_desc = detect_gpu()
    ollama_reason, ollama_desc = detect_ollama()
    notes = [f"GPU: {gpu_desc or gpu_reason}", f"Ollama: {ollama_desc or ollama_reason}"]
    return Capabilities(gpu=gpu_reason, ollama=ollama_reason, notes=notes)


def plan_tiers(caps: Capabilities, fast_only: bool) -> list[Tier]:
    """Build the tier list; heavy tiers carry a skip reason when the machine (or the user) rules them out."""
    tiers = [
        Tier("fast", pytest_command("not slow and not ollama")),
        Tier("slow", pytest_command("slow and not ollama"), skip_reason=caps.gpu, gated=True),
        Tier("ollama", pytest_command("ollama"), skip_reason=caps.ollama, gated=True),
        Tier(
            "e2e",
            [sys.executable, str(ROOT / "scripts" / "e2e_smoke.py"), "--skip-streamlit"],
            skip_reason=caps.ollama,
        ),
    ]
    if fast_only:
        for tier in tiers[1:]:
            tier.skip_reason = "PRE_PUSH_FAST=1"
    for tier in tiers:
        if tier.skip_reason:
            tier.status = "skipped"
    return tiers


def last_summary_line(output: str) -> str:
    """The pytest ``=== N passed in Xs ===`` line, or the last non-empty line for other commands."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in reversed(lines):
        if re.match(r"^=+ .*\b(passed|failed|skipped|error|errors|no tests ran|deselected)\b.* =+$", line):
            return line.strip("= ")
    return lines[-1] if lines else ""


def run_tier(tier: Tier, env: dict[str, str] | None = None) -> bool:
    """Run one tier, streaming its output; record status, duration and summary line."""
    print(f"\n[PRE-PUSH] === tier {tier.name}: {' '.join(tier.command[1:])}", flush=True)
    start = time.monotonic()
    proc = subprocess.Popen(
        tier.command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    captured: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        captured.append(line)
    returncode = proc.wait()
    tier.duration_s = time.monotonic() - start
    tier.summary = last_summary_line("".join(captured))
    # pytest exit code 5 = no tests collected for this marker; not a failure.
    tier.status = "passed" if returncode in (0, 5) else "failed"
    if tier.gated and tier.status == "passed" and "skipped" in tier.summary and not re.search(r"\b\d+ passed", tier.summary):
        tier.status = "failed"
        tier.summary += " (all skipped although the capability was detected; run pytest -rs to see why)"
    return tier.status == "passed"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip()


def report_path(branch: str) -> Path:
    """``<issue>-local-test-report.md`` when the branch names an issue, else the sanitised branch name."""
    match = re.search(r"(?:^|/)(\d+)-", branch)
    prefix = match.group(1) if match else re.sub(r"[^A-Za-z0-9_.-]+", "-", branch) or "detached"
    return REPORT_DIR / f"{prefix}-local-test-report.md"


def render_report(tiers: list[Tier], caps: Capabilities, branch: str, commit: str) -> str:
    passed = all(t.status in ("passed", "skipped") for t in tiers)
    rows = [
        f"| {t.name} | {t.status} | {f'{t.duration_s:.0f}s' if t.duration_s else '-'} | {t.skip_reason or t.summary or '-'} |"
        for t in tiers
    ]
    return "\n".join(
        [
            f"## Local pre-push test report: {'PASSED' if passed else 'FAILED'}",
            "",
            f"- Branch: `{branch}`",
            f"- Commit: `{commit}`",
            f"- Run at: {datetime.now().isoformat(timespec='seconds')}",
            *[f"- {note}" for note in caps.notes],
            "",
            "| Tier | Status | Duration | Detail |",
            "|------|--------|----------|--------|",
            *rows,
            "",
            "_Generated by `scripts/pre_push_tiers.py` (#212)._",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fast", action="store_true", default=os.environ.get("PRE_PUSH_FAST") == "1")
    parser.add_argument("--dry-run", action="store_true", default=os.environ.get("PRE_PUSH_DRY_RUN") == "1")
    parser.add_argument("--hook", action="store_true", help="called from githooks/pre-push: a dry run blocks the push")
    args = parser.parse_args()

    print("[PRE-PUSH] Detecting test capabilities...", flush=True)
    caps = (
        Capabilities(gpu=None, ollama=None, notes=["Capabilities: not detected (PRE_PUSH_FAST=1)"])
        if args.fast
        else detect_capabilities()
    )
    for note in caps.notes:
        print(f"[PRE-PUSH]   {note}")
    tiers = plan_tiers(caps, args.fast)
    for tier in tiers:
        state = f"SKIP ({tier.skip_reason})" if tier.skip_reason else "RUN"
        print(f"[PRE-PUSH]   tier {tier.name:<6} {state}")
    if args.dry_run:
        print("[PRE-PUSH] Dry run: no tests executed.")
        # Inside the hook a dry run must not let an untested push through.
        return 1 if args.hook else 0

    env = tier_env()
    for tier in tiers:
        if tier.status == "not run" and not run_tier(tier, env):
            break  # first failure blocks the push; later tiers stay "not run"
    branch, commit = git("rev-parse", "--abbrev-ref", "HEAD"), git("rev-parse", "--short", "HEAD")
    path = report_path(branch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(tiers, caps, branch, commit), encoding="utf-8")

    print("\n[PRE-PUSH] Tier results:")
    for tier in tiers:
        print(f"[PRE-PUSH]   {tier.name:<6} {tier.status:<8} {tier.skip_reason or tier.summary}")
    print(f"[PRE-PUSH] Report: {path.relative_to(ROOT)}  (post with: gh pr comment <PR> --body-file {path.relative_to(ROOT)})")
    return 1 if any(t.status == "failed" for t in tiers) else 0


if __name__ == "__main__":
    sys.exit(main())
