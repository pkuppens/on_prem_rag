"""Tests for the minimal Streamlit RAG chat (streamlit_app/app.py, #206).

The app is run headlessly with Streamlit's AppTest; httpx.post is patched so no backend is needed.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "streamlit_app" / "app.py")

QA_RESPONSE = {
    "answer": "Metformin is the first-line treatment.",
    "sources": [
        {"document_name": "guideline.pdf", "page_number": 3, "similarity_score": 0.912, "text": "Start metformin..."},
    ],
    "confidence": "high",
    "chunks_retrieved": 1,
    "average_similarity": 0.912,
}


def _ok_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def _run_with_question(question: str, post: MagicMock) -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    with patch("httpx.post", post):
        at.run()
        at.chat_input[0].set_value(question).run()
    return at


def test_question_renders_answer_and_sources():
    """As a developer I want to ask a question and see the RAG answer with its sources,
    so I can inspect RAG behaviour without the React frontend.

    The app posts the question to /api/v1/qa and renders answer plus one expander per source.
    """
    post = MagicMock(return_value=_ok_response(QA_RESPONSE))
    at = _run_with_question("What is the first-line treatment?", post)

    assert not at.exception
    url = post.call_args.args[0]
    assert url == "http://localhost:8000/api/v1/qa"
    assert post.call_args.kwargs["json"] == {
        "question": "What is the first-line treatment?",
        "similarity_threshold": 0.5,
        "top_k": 5,
    }
    rendered = [m.value for m in at.markdown]
    assert "What is the first-line treatment?" in rendered
    assert QA_RESPONSE["answer"] in rendered
    assert len(at.expander) == 1
    assert "guideline.pdf" in at.expander[0].label


def test_conversation_keeps_previous_turns():
    """As a developer I want earlier questions to stay visible, so the chat reads in order."""
    post = MagicMock(return_value=_ok_response(QA_RESPONSE))
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    with patch("httpx.post", post):
        at.run()
        at.chat_input[0].set_value("first question").run()
        at.chat_input[0].set_value("second question").run()

    rendered = [m.value for m in at.markdown]
    assert rendered.index("first question") < rendered.index("second question")
    assert len(at.session_state["history"]) == 2


def test_unreachable_backend_shows_error():
    """As a developer I want a visible error with start instructions when the backend is down."""
    at = _run_with_question("anything", MagicMock(side_effect=httpx.ConnectError("connection refused")))

    assert not at.exception
    assert len(at.error) == 1
    assert "Could not reach backend" in at.error[0].value
    assert "uv run start-backend" in at.error[0].value


def test_timeout_shows_ollama_hint():
    """As a developer I want a timeout explained (slow or stopped LLM), not reported as unreachable."""
    at = _run_with_question("anything", MagicMock(side_effect=httpx.ReadTimeout("timed out")))

    assert not at.exception
    assert "did not answer within" in at.error[0].value
    assert "Ollama" in at.error[0].value


def test_backend_remediation_is_shown():
    """As a developer I want the backend's remediation steps (e.g. ollama pull) shown for a missing model."""
    request = httpx.Request("POST", "http://localhost:8000/api/v1/qa")
    detail = {"error": "LLM model not available", "model": "mistral", "remediation": ["Pull the model: ollama pull mistral"]}
    response = httpx.Response(503, json={"detail": detail}, request=request)
    failing = MagicMock()
    failing.raise_for_status.side_effect = httpx.HTTPStatusError("503", request=request, response=response)

    at = _run_with_question("anything", MagicMock(return_value=failing))

    assert not at.exception
    assert "LLM model not available" in at.error[0].value
    assert "ollama pull mistral" in at.error[0].value


def test_backend_http_error_shows_status():
    """As a developer I want backend 5xx errors surfaced with their status code."""
    request = httpx.Request("POST", "http://localhost:8000/api/v1/qa")
    response = httpx.Response(503, text="LLM unavailable", request=request)
    failing = MagicMock()
    failing.raise_for_status.side_effect = httpx.HTTPStatusError("503", request=request, response=response)

    at = _run_with_question("anything", MagicMock(return_value=failing))

    assert not at.exception
    assert "503" in at.error[0].value
    assert "LLM unavailable" in at.error[0].value


def test_api_url_from_env(monkeypatch: pytest.MonkeyPatch):
    """Ensure ON_PREM_RAG_API_URL overrides the default backend URL (trailing slash stripped)."""
    monkeypatch.setenv("ON_PREM_RAG_API_URL", "http://localhost:9180/")
    post = MagicMock(return_value=_ok_response(QA_RESPONSE))
    _run_with_question("q", post)

    assert post.call_args.args[0] == "http://localhost:9180/api/v1/qa"


def test_empty_sources_shows_hint():
    """Ensure an answer without sources tells the user the vector store may be empty."""
    post = MagicMock(return_value=_ok_response({**QA_RESPONSE, "sources": []}))
    at = _run_with_question("q", post)

    assert len(at.expander) == 0
    assert any("No sources retrieved" in c.value for c in at.caption)
