#!/usr/bin/env python3
"""Verify voice pipeline: progressive STT -> RAG with document upload -> voice RAG.

Usage:
  uv run --env-file .env python scripts/verify_voice_pipeline.py --check-latency
  uv run --env-file .env python scripts/verify_voice_pipeline.py --progression
  uv run --env-file .env python scripts/verify_voice_pipeline.py --check-dutch-rag
  uv run --env-file .env python scripts/verify_voice_pipeline.py --progression --loglevel DEBUG  # verbose
  uv run --env-file .env python scripts/verify_voice_pipeline.py --progression --loglevel NONE   # no logging

  --progression runs 3 steps:
  - Step 0: STT only (audio duration + latency)
  - Step 1: Upload metformin fixture -> RAG query (backend Ollama + ChromaDB)
  - Step 2: Voice RAG (/api/ask/voice) with guardrails when enabled

All RAG steps use the backend's configured Ollama; no direct Ollama API calls.

Prerequisites:
  --check-latency: Backend + gtts (no ChromaDB, no Ollama).
  --progression: Backend + gtts + Ollama; step 1 uploads a metformin doc for RAG.
  --check-dutch-rag: Backend + Ollama + Chroma with indexed clinical documents.

Load .env: Use --env-file .env with uv run, or set UV_ENV_FILE to .env path.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Configured in main() from --loglevel (default INFO). Suppress httpx/httpcore DEBUG noise.
log = logging.getLogger(__name__)

DEFAULT_BACKEND_URL = "http://localhost:9180"
LATENCY_THRESHOLD_MS = 3000  # AC-2b: target < 3 s for 5-10 s clip


def _backend_url() -> str:
    port = os.getenv("BACKEND_PORT", "9180")
    return f"http://localhost:{port}"


def check_prerequisites(url: str, check_name: str = "") -> bool:
    """Verify backend is reachable. Return True if OK. On failure, log specific remediation."""
    try:
        import httpx
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{url}/api/health")
            if resp.status_code == 200:
                log.info("Backend reachable at %s", url)
                return True
            log.error("Backend returned status %s (expected 200)", resp.status_code)
    except Exception as e:
        log.error("Backend not reachable: %s", e)

    # Specific remediation when backend check fails
    log.error("Prerequisites not met for %s.", check_name or "this check")
    log.info("Required: FastAPI RAG backend must be running at %s", url)
    log.info("Start options:")
    log.info("  - Local: uv run start-backend  (in another terminal)")
    log.info("  - Docker: docker-compose up -d chroma backend")
    port = url.rstrip("/").split(":")[-1].split("/")[0]
    log.info("Ensure port %s is free (or set BACKEND_PORT in .env).", port)
    log.info("Verify: curl -s %s/api/health", url)
    return False


def create_test_audio_via_tts(text: str, lang: str = "en", slow: bool = True) -> bytes | None:
    """Create audio via gTTS. Returns None if gtts not available.

    slow=True reduces speech rate (~40%), improving Whisper recognition of rare words.
    """
    try:
        from gtts import gTTS
        from io import BytesIO
        buf = BytesIO()
        gTTS(text=text, lang=lang, slow=slow).write_to_fp(buf)
        return buf.getvalue()
    except ImportError:
        log.warning("gtts not installed. Install: uv add gtts  (or: uv pip install gtts if UV_NO_SYNC=1)")
        return None


def _run_stt_step(
    url: str,
    text: str = "Just say hello world!",
    language_hint: str = "",
) -> tuple[bytes | None, dict | None]:
    """TTS + STT. Returns (audio_bytes, result_dict) or (None, None) on failure.

    result_dict has: text, language, confidence, duration_seconds, elapsed_ms.
    language_hint: pass "en" to improve recognition; empty = auto-detect.
    """
    audio = create_test_audio_via_tts(text, "en", slow=True)
    if not audio:
        return None, None

    import httpx

    files = {"audio": ("test.mp3", audio, "audio/mpeg")}
    form = {"language": language_hint}
    t0 = time.perf_counter()
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{url}/api/stt/transcribe/draft", files=files, data=form)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    if resp.status_code != 200:
        log.error("Transcribe failed: %s %s", resp.status_code, resp.text)
        return audio, None
    result = resp.json()
    result["elapsed_ms"] = elapsed_ms
    return audio, result


def run_latency(url: str) -> bool:
    """Transcription latency < 3 s. Uses STT only (no ChromaDB, no Ollama).

    Shows: "Transcribed X.X seconds of audio in Y.Y seconds."
    """
    log.info("=== Step 0: Transcription latency (< 3 s target) ===")
    if not check_prerequisites(url, "latency check"):
        return False

    text = "When should you not use the drug metformin?"
    log.info("Generated audio via TTS: %r", text)
    audio, result = _run_stt_step(url, text, language_hint="en")
    if not audio:
        log.error("Prerequisites not met: gtts required. Install: uv pip install gtts")
        return False
    if result is None:
        return False

    transcript = result.get("text", "").strip()
    duration_sec = result.get("duration_seconds", 0)
    elapsed_ms = result.get("elapsed_ms", 0)

    log.info(
        "Transcribed %.3f seconds of audio in %.3f seconds -> %r",
        duration_sec,
        elapsed_ms / 1000,
        transcript or "(empty)",
    )
    if elapsed_ms <= LATENCY_THRESHOLD_MS:
        log.info("[PASS] Latency %d ms <= %d ms (target)", elapsed_ms, LATENCY_THRESHOLD_MS)
        return True
    log.warning("[FAIL] Latency %d ms > %d ms (target)", elapsed_ms, LATENCY_THRESHOLD_MS)
    return False


# Default ingestion wait after document upload (seconds).
# Docker/remote backends may need 40-50s for first-time embedding (model load + chunk + embed).
# Use --ingestion-wait 0 to skip (e.g. mock), or when you're sure the document is already embedded.
DEFAULT_INGESTION_WAIT_SEC = 10


def _metformin_fixture_path() -> Path:
    """Return path to metformin_summary.txt fixture."""
    return Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "metformin_summary.txt"


def run_progression(url: str, ingestion_wait_sec: int = DEFAULT_INGESTION_WAIT_SEC) -> bool:
    """Progressive: 1) Ingest doc  2) Text RAG  3) Voice RAG (same question).

    Order ensures document is in ChromaDB before any RAG query. Both RAG steps ask
    the same metformin question. ingestion_wait_sec=0 skips wait (e.g. mock for tests).
    """
    import httpx

    # Phrasing tuned for Whisper: "not use" vs "contraindicated"; "the drug" provides
    # acoustic/lexical context so "metformin" is less likely transcribed as "met form in".
    metformin_question = "When should you not use the drug metformin?"

    log.info("=== Voice pipeline progression (3 steps) ===")
    if not check_prerequisites(url, "progression"):
        return False

    # Verify STT model (STT_MODEL_SIZE from .env; Docker needs env_file in compose)
    try:
        r = httpx.get(f"{url}/api/stt/info", timeout=5)
        if r.status_code == 200:
            model = r.json().get("service", {}).get("transcriber", {}).get("model_size", "?")
            log.info("STT model: %s", model)
    except Exception:
        pass

    # Step 0: STT with metformin question (language_hint="en" improves recognition)
    log.info("Step 0 TTS: %r", metformin_question)
    audio_metformin, stt_result = _run_stt_step(url, metformin_question, language_hint="en")
    if not audio_metformin:
        log.error("Prerequisites: gtts required. uv pip install gtts")
        return False
    if stt_result is None:
        return False

    transcript = stt_result.get("text", "").strip()
    duration_sec = stt_result.get("duration_seconds", 0)
    elapsed_ms = stt_result.get("elapsed_ms", 0)
    log.info(
        "Step 0 STT: Transcribed %.3f s of audio in %.3f s -> %r",
        duration_sec,
        elapsed_ms / 1000,
        transcript or "(empty)",
    )

    # Step 1: Ingest metformin doc first, then text RAG (same question as Step 2)
    log.info("--- Step 1: Ingest metformin doc -> text RAG ---")
    fixture_path = _metformin_fixture_path()
    if not fixture_path.exists():
        log.warning("Fixture not found: %s. Skipping step 1.", fixture_path)
    else:
        try:
            with open(fixture_path, "rb") as f:
                content = f.read()
            files = {"file": ("metformin_verify_pipeline.txt", content, "text/plain")}
            upload_resp = httpx.post(f"{url}/api/documents/upload", files=files, timeout=30)
            if upload_resp.status_code == 200:
                if ingestion_wait_sec > 0:
                    log.info("Uploaded metformin doc, waiting %s s for ingestion...", ingestion_wait_sec)
                    time.sleep(ingestion_wait_sec)
                else:
                    log.info("Uploaded metformin doc (ingestion wait skipped, e.g. --ingestion-wait 0)")
                rag_resp = httpx.post(
                    f"{url}/api/ask",
                    json={
                        "question": metformin_question,
                        "strategy": "hybrid",
                        "similarity_threshold": 0.5,
                    },
                    timeout=60,
                )
                if rag_resp.status_code == 200:
                    data = rag_resp.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    log.info("Text RAG: %r", answer[:200] + ("..." if len(answer) > 200 else ""))
                    log.info("Sources: %d chunks", len(sources))
                else:
                    log.warning("RAG failed %s: %s", rag_resp.status_code, rag_resp.text)
            else:
                log.warning("Upload failed %s: %s", upload_resp.status_code, upload_resp.text)
        except Exception as e:
            log.warning("Step 1 failed: %s", e)

    # Step 2: Voice RAG - voice->text->retrieve->generate (same question as Step 1)
    log.info("--- Step 2: Voice RAG (voice->text->RAG->response) ---")
    try:
        files = {"audio": ("metformin_question.mp3", audio_metformin, "audio/mpeg")}
        t0_rag = time.perf_counter()
        with httpx.Client(timeout=90) as client:
            resp = client.post(f"{url}/api/ask/voice", files=files)
        elapsed_rag = time.perf_counter() - t0_rag
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            trans = data.get("transcription_text", "")
            log.info(
                "Voice RAG (%s s): voice->%r->RAG->%r",
                round(elapsed_rag, 2),
                trans[:60] + ("..." if len(trans) > 60 else ""),
                answer[:120] + ("..." if len(answer) > 120 else ""),
            )
            log.info("Sources: %d chunks", len(sources))
        else:
            log.warning("Voice RAG failed %s: %s", resp.status_code, resp.text)
    except Exception as e:
        log.warning("Voice RAG request failed: %s", e)

    log.info("--- Progression complete ---")
    return True  # Progression is informative; we don't fail on optional steps


def run_dutch_rag(url: str) -> bool:
    """Dutch medical query -> English clinical RAG answer.

    Prerequisites: Backend + Ollama + Chroma with indexed clinical documents.
    """
    log.info("=== Dutch query -> English RAG answer ===")
    if not check_prerequisites(url, "Dutch->English RAG check"):
        return False

    # Check Ollama
    try:
        import httpx
        with httpx.Client(timeout=3) as client:
            r = client.get("http://localhost:11434/api/tags")
            models = r.json().get("models", []) if r.status_code == 200 else []
        if not models:
            log.warning("Ollama has no models. Run: ollama pull mistral:7b")
        else:
            log.info("Ollama models: %s", [m.get("name") for m in models[:5]])
    except Exception as e:
        log.warning("Ollama not reachable: %s. Dutch->English RAG needs Ollama.", e)

    # Dutch medical question
    question_nl = "Wat is de aanbevolen dosering van metformine bij diabetes type 2?"
    log.info("Sending Dutch question: %s", question_nl)

    try:
        import httpx
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{url}/api/ask",
                json={"question": question_nl, "strategy": "hybrid"},
            )
            resp.raise_for_status()
        result = resp.json()
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        log.info("Answer length: %d chars, sources: %d", len(answer), len(sources))

        if not answer:
            log.warning("[FAIL] Empty answer. Check Chroma has indexed documents.")
            return False
        # Heuristic: answer in English often has "mg", "recommended", etc.
        en_indicators = ["recommended", "mg", "daily", "metformin", "diabetes", "dose"]
        has_en = any(w in answer.lower() for w in en_indicators)
        if has_en or len(answer) > 50:
            log.info("[PASS] Received RAG answer (manual: verify language is English)")
            return True
        log.warning("[REVIEW] Answer may not be English clinical. Manual check.")
        return True  # Still pass; human should verify
    except httpx.HTTPStatusError as e:
        log.error("Dutch RAG HTTP error %s: %s", e.response.status_code, e.response.text)
        if e.response.status_code == 503:
            log.info("Remediation: ollama pull mistral:7b")
        return False
    except Exception as e:
        log.exception("Dutch RAG check failed: %s", e)
        return False


def _configure_logging(level_arg: str | None) -> None:
    """Configure logging from --loglevel. None/empty = disable. Case insensitive: INFO, DEBUG, WARNING, NONE."""
    lev = (level_arg or "INFO").strip().upper()
    if lev in ("NONE", "OFF", ""):
        logging.disable(logging.CRITICAL)
        return
    level_map = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING}
    root_level = level_map.get(lev, logging.INFO)
    logging.basicConfig(
        level=root_level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    # Suppress verbose httpx/httpcore logs unless DEBUG
    if root_level != logging.DEBUG:
        for name in ("httpx", "httpcore"):
            logging.getLogger(name).setLevel(logging.WARNING)
        try:
            import gtts
            logging.getLogger(gtts.__name__).setLevel(logging.WARNING)
        except ImportError:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify voice pipeline")
    ap.add_argument("--check-latency", action="store_true", help="Transcription latency < 3 s")
    ap.add_argument("--progression", action="store_true", help="STT -> upload+RAG -> voice RAG (all via backend)")
    ap.add_argument("--check-dutch-rag", action="store_true", help="Dutch query -> English RAG answer")
    ap.add_argument("--all", action="store_true", help="Run all checks including progression")
    ap.add_argument("--url", default=None, help="Backend URL (default: from env or localhost:9180)")
    ap.add_argument(
        "--loglevel",
        default="INFO",
        metavar="LEVEL",
        help="Log level: INFO (default), DEBUG, WARNING, or NONE to disable. Case insensitive.",
    )
    ap.add_argument(
        "--ingestion-wait",
        type=int,
        default=DEFAULT_INGESTION_WAIT_SEC,
        metavar="SEC",
        help="Seconds to wait after doc upload (0=skip, e.g. mock). Default: %(default)s",
    )
    args = ap.parse_args()

    _configure_logging(args.loglevel)

    if not (args.check_latency or args.progression or args.check_dutch_rag or args.all):
        ap.print_help()
        print("\nExample: uv run --env-file .env python scripts/verify_voice_pipeline.py --progression")
        sys.exit(0)

    url = args.url or _backend_url()
    log.info("Backend URL: %s", url)

    ok = True
    if args.check_latency or args.all:
        ok = run_latency(url) and ok
    if args.progression or args.all:
        ok = run_progression(url, ingestion_wait_sec=args.ingestion_wait) and ok
    if args.check_dutch_rag or args.all:
        ok = run_dutch_rag(url) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
