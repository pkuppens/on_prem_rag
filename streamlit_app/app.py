"""Minimal Streamlit RAG chat over the production QA API (#206).

A lightweight developer workbench: ask a question, see the answer and its sources.
It only calls the existing backend — no RAG logic lives here.

Run against a locally running backend:

    uv run start-backend                               # FastAPI on http://localhost:8000
    uv run streamlit run streamlit_app/app.py

Point it at another backend (e.g. the docker-compose stack on port 9180) with:

    ON_PREM_RAG_API_URL=http://localhost:9180 uv run streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

DEFAULT_API_URL = "http://localhost:8000"
QA_PATH = "/api/v1/qa"
REQUEST_TIMEOUT_S = 120.0  # local LLM generation can be slow
# The backend default (0.7) drops relevant chunks for small embedding models (all-MiniLM scores ~0.6-0.7).
DEFAULT_SIMILARITY_THRESHOLD = 0.5
DEFAULT_TOP_K = 5


class BackendError(Exception):
    """The QA backend was unreachable or returned an error."""


def get_api_url() -> str:
    """Return the backend base URL from ON_PREM_RAG_API_URL, defaulting to localhost."""
    return os.environ.get("ON_PREM_RAG_API_URL", DEFAULT_API_URL).rstrip("/")


def describe_http_error(response: httpx.Response) -> str:
    """Turn an error response into a message, including the backend's remediation steps when present."""
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    if isinstance(detail, dict):
        steps = "".join(f"\n- {step}" for step in detail.get("remediation", []))
        return f"Backend returned {response.status_code}: {detail.get('error', detail)}{steps}"
    return f"Backend returned {response.status_code}: {detail or response.text[:300]}"


def ask_backend(
    question: str,
    api_url: str,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """POST the question to the QA endpoint and return the parsed response.

    Raises:
        BackendError: on connection failure, timeout, or a non-2xx response.
    """
    payload = {"question": question, "similarity_threshold": similarity_threshold, "top_k": top_k}
    try:
        response = httpx.post(f"{api_url}{QA_PATH}", json=payload, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise BackendError(describe_http_error(e.response)) from e
    except httpx.TimeoutException as e:
        raise BackendError(
            f"Backend at {api_url} did not answer within {REQUEST_TIMEOUT_S:.0f} s. "
            "The local LLM may still be loading; try again, or check that Ollama is running (ollama ps)."
        ) from e
    except httpx.HTTPError as e:
        raise BackendError(
            f"Could not reach backend at {api_url}: {e}\n"
            "- Start it: uv run start-backend\n"
            "- Or set ON_PREM_RAG_API_URL (docker-compose stack: http://localhost:9180)"
        ) from e


def render_sources(sources: list[dict]) -> None:
    """Render retrieved chunks as collapsible entries: document, page, score, text."""
    if not sources:
        st.caption("No sources retrieved: the vector store may be empty, or lower the similarity threshold in the sidebar.")
        return
    for i, source in enumerate(sources, start=1):
        name = source.get("document_name", "unknown document")
        page = source.get("page_number", "?")
        score = source.get("similarity_score")
        score_text = f" • score {score:.3f}" if isinstance(score, int | float) else ""
        with st.expander(f"[{i}] {name} • page {page}{score_text}"):
            st.write(source.get("text", ""))


def render_turn(turn: dict) -> None:
    """Render one question/answer pair from the chat history."""
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        if "error" in turn:
            st.error(turn["error"])
            return
        st.write(turn["answer"])
        render_sources(turn["sources"])


def main() -> None:
    """Streamlit entry point: chat history plus a query input."""
    st.set_page_config(page_title="On-prem RAG chat")
    st.title("On-prem RAG chat")
    api_url = get_api_url()
    st.caption(f"Backend: {api_url}")
    threshold = st.sidebar.slider("Similarity threshold", 0.0, 1.0, DEFAULT_SIMILARITY_THRESHOLD, 0.05)
    top_k = st.sidebar.slider("Top k chunks", 1, 20, DEFAULT_TOP_K)

    history: list[dict] = st.session_state.setdefault("history", [])
    for turn in history:
        render_turn(turn)

    question = st.chat_input("Ask a question about your documents...")
    if not question:
        return

    try:
        result = ask_backend(question, api_url, similarity_threshold=threshold, top_k=top_k)
        turn = {"question": question, "answer": result.get("answer", ""), "sources": result.get("sources", [])}
    except BackendError as e:
        turn = {"question": question, "error": str(e)}
    history.append(turn)
    render_turn(turn)


main()
