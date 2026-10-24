#!/usr/bin/env python3
"""UI smoke test and demo run: every user-facing surface, driven in a real browser (#213).

Where `e2e_smoke.py` checks the API and runs Streamlit headlessly, this script opens each UI in Chromium:

  1. Ollama + model + backend + LLM health   -> reuses the e2e_smoke.py checks (starts what is missing)
  2. Streamlit chat (8501), React UI (5173), Chainlit chat (8002) -> started when not running
  3. Playwright spec src/frontend/smoke/ui-smoke.spec.ts -> one test per demo step, screenshot per step

Defects that already have an issue are listed in src/frontend/smoke/known-issues.json. Their steps are
marked as expected failures: the run stays green while they fail, and turns red once they pass, as a
reminder to remove the entry when the issue is fixed.

Usage:
  uv run python scripts/ui_smoke.py
  uv run python scripts/ui_smoke.py --headed          # watch it (demo mode)
  uv run python scripts/ui_smoke.py --grep streamlit  # run one step
  just smoke

Screenshots and Playwright artifacts: tmp/debug/smoke/. Exit code 0 when every step passes or fails as known.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
from e2e_smoke import (
    ROOT,
    SAMPLE_DOC,
    SAMPLE_QUESTION,
    SmokeError,
    check_llm_health,
    ensure_backend,
    ensure_model,
    ensure_ollama,
    log,
    resolve_model,
    resolve_ollama_url,
    stop_process,
    wait_until,
)

FRONTEND_DIR = ROOT / "src" / "frontend"
SMOKE_OUT = ROOT / "tmp" / "debug" / "smoke"
KNOWN_ISSUES = FRONTEND_DIR / "smoke" / "known-issues.json"


@dataclass(frozen=True)
class Service:
    """A UI process the smoke test can start when nothing answers on ``url``."""

    name: str
    url: str
    command: list[str]
    cwd: Path
    env: dict[str, str]


def http_ok(url: str) -> bool:
    try:
        return httpx.get(url, timeout=3).status_code < 500
    except httpx.HTTPError:
        return False


def ensure_service(svc: Service, start: bool) -> subprocess.Popen | None:
    """Return the process we started (to stop later), or None when the service was already running."""
    if http_ok(svc.url):
        log(f"  {svc.name} running at {svc.url}")
        return None
    if not start:
        raise SmokeError(f"{svc.name} is not reachable at {svc.url}.", f"Start it: {' '.join(svc.command)}")

    log_path = SMOKE_OUT / f"{svc.name.lower().replace(' ', '-')}.log"
    log(f"  {svc.name} not running; starting `{' '.join(svc.command)}` (log: {log_path.relative_to(ROOT)})...")
    with open(log_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(svc.command, cwd=svc.cwd, env={**os.environ, **svc.env}, stdout=log_file, stderr=subprocess.STDOUT)
    if not wait_until(lambda: http_ok(svc.url) or proc.poll() is not None, timeout_s=120, interval_s=2) or proc.poll() is not None:
        stop_process(proc)
        raise SmokeError(f"{svc.name} did not come up at {svc.url} within 120 s.", f"Inspect {log_path}")
    log(f"  {svc.name} started")
    return proc


def ui_services(args: argparse.Namespace) -> list[Service]:
    npm = shutil.which("npm") or "npm"
    return [
        Service(
            "Streamlit",
            args.streamlit_url,
            ["uv", "run", "streamlit", "run", "streamlit_app/app.py", "--server.headless", "true", "--server.port", "8501"],
            ROOT,
            {"ON_PREM_RAG_API_URL": args.api_url},
        ),
        Service("React UI", args.frontend_url, [npm, "run", "dev", "--", "--port", "5173"], FRONTEND_DIR, {}),
        Service("Chainlit", args.chainlit_url, ["uv", "run", "start-chat"], ROOT, {"CHAINLIT_PORT": "8002"}),
    ]


def run_playwright(args: argparse.Namespace) -> int:
    npx = shutil.which("npx")
    if npx is None or not (FRONTEND_DIR / "node_modules" / "@playwright" / "test").exists():
        raise SmokeError(
            "Playwright is not installed for the frontend.",
            "cd src/frontend && npm ci && npx playwright install chromium",
        )
    cmd = [npx, "playwright", "test", "--config", "playwright.smoke.config.ts"]
    if args.headed:
        cmd.append("--headed")
    if args.grep:
        cmd += ["--grep", args.grep]
    env = {
        **os.environ,
        "SMOKE_API_URL": args.api_url,
        "SMOKE_FRONTEND_URL": args.frontend_url,
        "SMOKE_STREAMLIT_URL": args.streamlit_url,
        "SMOKE_CHAINLIT_URL": args.chainlit_url,
        "SMOKE_OUT": str(SMOKE_OUT),
        "SMOKE_SAMPLE_DOC": str(SAMPLE_DOC),
        "SMOKE_SAMPLE_QUESTION": SAMPLE_QUESTION,
    }
    log(f"  {' '.join(cmd[1:])}")
    return subprocess.run(cmd, cwd=FRONTEND_DIR, env=env, check=False).returncode


def run(args: argparse.Namespace) -> int:
    SMOKE_OUT.mkdir(parents=True, exist_ok=True)
    ollama_url, model = resolve_ollama_url(), resolve_model()
    started: list[subprocess.Popen | None] = []
    try:
        log("[1/3] Backend prerequisites")
        ensure_model(ollama_url, model, ensure_ollama(ollama_url), args.pull)
        started.append(ensure_backend(args.api_url, args.start, ollama_url))
        check_llm_health(args.api_url, model)

        log("[2/3] User interfaces")
        for svc in ui_services(args):
            started.append(ensure_service(svc, args.start))

        log("[3/3] Browser walkthrough")
        return run_playwright(args)
    finally:
        for proc in reversed(started):
            stop_process(proc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api-url", default=os.environ.get("ON_PREM_RAG_API_URL", "http://localhost:8000"))
    parser.add_argument("--frontend-url", default="http://localhost:5173")
    parser.add_argument("--streamlit-url", default="http://localhost:8501")
    parser.add_argument("--chainlit-url", default="http://localhost:8002")
    parser.add_argument("--headed", action="store_true", help="show the browser (demo mode)")
    parser.add_argument("--grep", help="only run steps whose title matches this pattern")
    parser.add_argument("--pull", action="store_true", help="pull the LLM model when it is missing")
    parser.add_argument("--no-start", dest="start", action="store_false", help="fail instead of starting services")
    args = parser.parse_args()
    args.api_url = args.api_url.rstrip("/")
    try:
        code = run(args)
    except SmokeError as e:
        log(f"\nFAILED: {e.problem}")
        for step in e.remediation:
            log(f"  -> {step}")
        return 1
    known = json.loads(KNOWN_ISSUES.read_text(encoding="utf-8"))
    if known:
        log("\nKnown issues (steps expected to fail; shown as 'x' above, an unexpected pass fails the run):")
        for step, entry in known.items():
            log(f"  - {step}: {entry['summary']} ({entry['issue']})")
    log(f"\nScreenshots: {SMOKE_OUT.relative_to(ROOT)}")
    log("UI smoke test passed." if code == 0 else "UI smoke test FAILED (see Playwright output above).")
    return code


if __name__ == "__main__":
    sys.exit(main())
