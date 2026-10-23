#!/usr/bin/env python3
"""End-to-end smoke test: Ollama -> backend -> upload -> POST /api/v1/qa -> Streamlit chat (#206).

Automates the manual check "ask a question against a sample document and inspect answer + sources".
Each step fails with an actionable message (what is wrong, how to fix it) and tries to recover first:

  1. Ollama reachable          -> auto-starts `ollama serve` if the binary is installed
  2. LLM model available       -> prints `ollama pull <model>`; pulls it with --pull
  3. Backend healthy           -> auto-starts `uv run start-backend` (stopped again on exit)
  4. LLM health via backend    -> GET /api/v1/health/llm
  5. Upload sample document    -> async upload, polls the task until indexed
  6. Ask a question            -> answer is non-empty and cites the sample document
  7. Streamlit chat            -> runs streamlit_app/app.py headlessly against the real backend

Usage:
  uv run python scripts/e2e_smoke.py
  uv run python scripts/e2e_smoke.py --pull                 # pull a missing model automatically
  uv run python scripts/e2e_smoke.py --api-url http://localhost:9180 --no-start-backend  # docker stack
  just e2e

Environment: OLLAMA_BASE_URL (default http://localhost:11434), OLLAMA_MODEL / LLM_MODEL (default mistral).
Exit code 0 when every step passes, 1 on the first failing step.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DOC = ROOT / "tests" / "fixtures" / "metformin_summary.txt"
SAMPLE_QUESTION = "What is metformin indicated for, and when is it contraindicated?"
STREAMLIT_APP = ROOT / "streamlit_app" / "app.py"
BACKEND_LOG = ROOT / "tmp" / "debug" / "e2e-backend.log"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class SmokeError(Exception):
    """A failed step, with the remediation steps a developer should take."""

    def __init__(self, problem: str, *remediation: str) -> None:
        super().__init__(problem)
        self.problem = problem
        self.remediation = remediation


def log(msg: str) -> None:
    print(msg, flush=True)


def wait_until(check: Callable[[], bool], timeout_s: float, interval_s: float = 1.0) -> bool:
    """Poll ``check`` until it returns True or ``timeout_s`` elapses."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(interval_s)
    return False


def resolve_ollama_url() -> str:
    """OLLAMA_BASE_URL, mapped to localhost when it names the Docker host alias (we run natively)."""
    url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    return url.replace("host.docker.internal", "localhost")


def resolve_model() -> str:
    """Same precedence as the backend (llm_gateway config): LLM_MODEL > OLLAMA_MODEL > mistral."""
    return os.environ.get("LLM_MODEL") or os.environ.get("OLLAMA_MODEL") or "mistral"


def ollama_models(url: str) -> list[str] | None:
    """Return installed model names, or None when Ollama is unreachable."""
    try:
        resp = httpx.get(f"{url}/api/tags", timeout=3)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except (httpx.HTTPError, ValueError):
        return None


def ensure_ollama(url: str) -> list[str]:
    """Make sure Ollama answers on ``url``; start `ollama serve` if it is installed but not running."""
    if (models := ollama_models(url)) is not None:
        log(f"  Ollama reachable at {url} ({len(models)} models)")
        return models

    binary = shutil.which("ollama")
    if binary is None:
        raise SmokeError(
            f"Ollama is not reachable at {url} and the `ollama` binary is not on PATH.",
            "Install Ollama: https://ollama.com/download",
            "Then start it: ollama serve",
            "Or point OLLAMA_BASE_URL at a running Ollama instance.",
        )
    if "localhost" not in url and "127.0.0.1" not in url:
        raise SmokeError(
            f"Ollama is not reachable at {url} (remote host, not auto-starting).",
            "Start Ollama on that host, or unset OLLAMA_BASE_URL to use a local instance.",
        )

    log("  Ollama not running; starting `ollama serve` in the background...")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
    # Bind `ollama serve` to the configured host:port, not its default 11434.
    env = {**os.environ, "OLLAMA_HOST": urlparse(url).netloc}
    subprocess.Popen(
        [binary, "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        start_new_session=sys.platform != "win32",
    )
    if not wait_until(lambda: ollama_models(url) is not None, timeout_s=30):
        raise SmokeError(
            "Started `ollama serve`, but it did not answer within 30 s.",
            "Run `ollama serve` in a terminal and read its output (port 11434 already in use?).",
        )
    log("  Ollama started (left running after this script exits)")
    return ollama_models(url) or []


def model_available(model: str, installed: list[str]) -> bool:
    """Ollama treats `mistral` and `mistral:latest` as the same model."""
    wanted = model if ":" in model else f"{model}:latest"
    return wanted in installed or model in installed


def ensure_model(url: str, model: str, installed: list[str], pull: bool) -> None:
    """Check the configured model is present; pull it when ``pull`` is set."""
    if model_available(model, installed):
        log(f"  Model {model} available")
        return
    if not pull:
        raise SmokeError(
            f"Ollama model '{model}' is not installed.",
            f"Download it: ollama pull {model}   (or rerun this script with --pull)",
            "Or use an installed model: OLLAMA_MODEL=<name>  (list them with: ollama list)",
        )
    log(f"  Pulling {model} (this can take several minutes)...")
    if subprocess.run(["ollama", "pull", model], check=False).returncode != 0:
        raise SmokeError(f"`ollama pull {model}` failed.", "Check the model name at https://ollama.com/library")


def backend_healthy(api_url: str) -> bool:
    try:
        return httpx.get(f"{api_url}/api/v1/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


def ensure_backend(api_url: str, start: bool, ollama_url: str) -> subprocess.Popen | None:
    """Return a backend process we started (to stop later), or None when one was already running."""
    if backend_healthy(api_url):
        log(f"  Backend healthy at {api_url}")
        return None
    if not start:
        raise SmokeError(
            f"Backend is not reachable at {api_url}.",
            "Start it: uv run start-backend   (FastAPI on http://localhost:8000)",
            "Docker stack: docker-compose up --build   (then use --api-url http://localhost:9180)",
        )

    BACKEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    log(f"  Backend not running; starting `uv run start-backend` (log: {BACKEND_LOG.relative_to(ROOT)})...")
    env = {**os.environ, "OLLAMA_BASE_URL": ollama_url, "PYTHONIOENCODING": "utf-8"}
    with open(BACKEND_LOG, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(["uv", "run", "start-backend"], cwd=ROOT, env=env, stdout=log_file, stderr=subprocess.STDOUT)
    # First start loads embedding models; allow a few minutes.
    if not wait_until(lambda: backend_healthy(api_url) or proc.poll() is not None, timeout_s=240, interval_s=2):
        stop_backend(proc)
        raise SmokeError("Backend did not become healthy within 240 s.", f"Inspect {BACKEND_LOG}")
    if proc.poll() is not None:
        tail = BACKEND_LOG.read_text(encoding="utf-8", errors="replace")[-1500:]
        raise SmokeError(
            f"Backend exited during startup (code {proc.returncode}).",
            "Last log lines:\n" + tail,
            "Port 8000 in use? Stop the other process or pass --api-url to reuse it.",
        )
    log("  Backend started")
    return proc


def stop_backend(proc: subprocess.Popen | None) -> None:
    """Stop a backend we started, including uvicorn's reload child processes."""
    if proc is None or proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False)
    else:
        proc.terminate()
    proc.wait(timeout=15)


def check_llm_health(api_url: str, model: str) -> None:
    resp = httpx.get(f"{api_url}/api/v1/health/llm", timeout=30)
    if resp.status_code != 200:
        raise SmokeError(
            f"Backend cannot reach its LLM: {resp.status_code} {resp.text[:300]}",
            "The backend reads OLLAMA_BASE_URL itself; for a native backend it must be http://localhost:11434.",
            f"Check the model the backend uses matches an installed one (expected {model}).",
        )
    log(f"  Backend LLM ok: {resp.json().get('backend')}")


def upload_sample(api_url: str) -> None:
    """Upload the sample document asynchronously and wait until it is indexed."""
    with open(SAMPLE_DOC, "rb") as f:
        files = {"files": (SAMPLE_DOC.name, f, "text/plain")}
        resp = httpx.post(f"{api_url}/api/v1/documents", params={"async": "true"}, files=files, timeout=60)
    if resp.status_code >= 400:
        raise SmokeError(f"Upload failed: {resp.status_code} {resp.text[:300]}", "See backend logs.")
    task_id = resp.json().get("task_id")
    if not task_id:  # duplicate content is skipped and already indexed
        log(f"  {SAMPLE_DOC.name} already indexed")
        return

    status: dict = {}

    def done() -> bool:
        nonlocal status
        status = httpx.get(f"{api_url}/api/v1/documents/tasks/{task_id}", timeout=10).json()
        return status.get("status") in ("completed", "completed_with_errors", "error")

    if not wait_until(done, timeout_s=180, interval_s=2):
        raise SmokeError(f"Indexing {SAMPLE_DOC.name} did not finish within 180 s.", f"Last status: {status}")
    if status.get("status") != "completed":
        raise SmokeError(
            f"Indexing failed: {status.get('message')}",
            "Embedding model missing? Run: uv run python scripts/setup_embedding_models.py",
        )
    log(f"  Indexed {SAMPLE_DOC.name}")


def cites_sample(document_name: str) -> bool:
    """Async uploads store the file with a timestamp suffix, e.g. metformin_summary_1792748702.txt."""
    return document_name.startswith(SAMPLE_DOC.stem)


def ask(api_url: str) -> None:
    payload = {"question": SAMPLE_QUESTION, "similarity_threshold": 0.3}
    resp = httpx.post(f"{api_url}/api/v1/qa", json=payload, timeout=180)
    if resp.status_code == 503:
        detail = resp.json().get("detail", {})
        steps = detail.get("remediation", []) if isinstance(detail, dict) else []
        raise SmokeError(f"QA endpoint: {detail.get('error', detail) if isinstance(detail, dict) else detail}", *steps)
    if resp.status_code != 200:
        raise SmokeError(f"QA endpoint returned {resp.status_code}: {resp.text[:300]}", "See backend logs.")

    body = resp.json()
    answer, sources = body.get("answer", "").strip(), body.get("sources", [])
    names = {s.get("document_name") or "" for s in sources}
    if not answer:
        raise SmokeError("QA answer is empty.", "Check the LLM output in the backend logs.")
    if not any(cites_sample(n) for n in names):
        raise SmokeError(
            f"Answer does not cite {SAMPLE_DOC.name} (sources: {sorted(n for n in names if n)}).",
            "Retrieval returned other or no chunks; check the vector store and similarity threshold.",
        )
    log(f"  Answer ({len(answer)} chars, {len(sources)} sources): {answer[:160]}...")


def check_streamlit(api_url: str) -> None:
    """Run the Streamlit chat headlessly against the real backend and check it renders an answer."""
    from streamlit.testing.v1 import AppTest

    os.environ["ON_PREM_RAG_API_URL"] = api_url
    at = AppTest.from_file(str(STREAMLIT_APP), default_timeout=180)
    at.run()
    at.chat_input[0].set_value(SAMPLE_QUESTION).run()
    if at.exception:
        raise SmokeError(
            f"Streamlit app raised: {at.exception[0].value}", "Run it manually: uv run streamlit run streamlit_app/app.py"
        )
    if at.error:
        raise SmokeError(f"Streamlit app showed an error: {at.error[0].value}")
    labels = [e.label for e in at.expander]
    if not any(SAMPLE_DOC.stem in label for label in labels):
        raise SmokeError(f"Streamlit app rendered no source for {SAMPLE_DOC.name} (expanders: {labels}).")
    log(f"  Streamlit rendered answer with {len(labels)} sources")


def run(args: argparse.Namespace) -> None:
    ollama_url, model = resolve_ollama_url(), resolve_model()
    api_url = args.api_url.rstrip("/")
    steps: list[tuple[str, Callable[[], object]]] = []
    state: dict = {}
    steps.append(("Ollama", lambda: state.update(models=ensure_ollama(ollama_url))))
    steps.append(("LLM model", lambda: ensure_model(ollama_url, model, state["models"], args.pull)))
    steps.append(("Backend", lambda: state.update(proc=ensure_backend(api_url, args.start_backend, ollama_url))))
    steps.append(("Backend LLM health", lambda: check_llm_health(api_url, model)))
    steps.append(("Upload sample document", lambda: upload_sample(api_url)))
    steps.append(("Ask question", lambda: ask(api_url)))
    if not args.skip_streamlit:
        steps.append(("Streamlit chat", lambda: check_streamlit(api_url)))

    try:
        for i, (name, step) in enumerate(steps, start=1):
            log(f"[{i}/{len(steps)}] {name}")
            step()
    finally:
        stop_backend(state.get("proc"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api-url", default=os.environ.get("ON_PREM_RAG_API_URL", "http://localhost:8000"))
    parser.add_argument("--pull", action="store_true", help="pull the LLM model when it is missing")
    parser.add_argument("--no-start-backend", dest="start_backend", action="store_false", help="fail instead of starting it")
    parser.add_argument("--skip-streamlit", action="store_true", help="skip the Streamlit UI check")
    args = parser.parse_args()
    try:
        run(args)
    except SmokeError as e:
        log(f"\nFAILED: {e.problem}")
        for step in e.remediation:
            log(f"  -> {step}")
        return 1
    except httpx.HTTPError as e:
        log(f"\nFAILED: unexpected HTTP error: {e}")
        return 1
    log("\nE2E smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
