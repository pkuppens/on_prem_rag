"""PROTOTYPE — throwaway, not production code.

Answers one design question: what should the RAG Inspector Streamlit layout
look like for #206 (minimal chat) and #207 (full strategy-comparison
dashboard) in pkuppens/on_prem_rag?

Three structurally different variants, switchable via ?variant=A|B|C (and a
sidebar selectbox as a fallback, since Streamlit reruns the whole script on
every interaction rather than routing client-side like a JS app — there is
no keyboard-arrow / floating-bar equivalent here, so the switcher lives in
the sidebar instead).

Run:
    uv run streamlit run streamlit_app/prototype_rag_inspector.py

Do NOT fold this file into streamlit_app/app.py directly — it is meant to
be flipped through, a decision picked (or bits stolen from each), and then
implemented properly against #206 / #207.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pandas as pd
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/qa"
DOCUMENTS_URL = f"{BASE_URL}/api/v1/documents"
STRATEGIES = ["dense", "sparse", "hybrid", "bm25"]

st.set_page_config(page_title="RAG Inspector — PROTOTYPE", layout="wide")


# ---------------------------------------------------------------------------
# Fake / real backend call — falls back to canned demo data if the backend
# is not running, so the prototype is explorable without `start-backend`.
# ---------------------------------------------------------------------------


@dataclass
class QAResult:
    answer: str
    sources: list[dict] = field(default_factory=list)
    confidence: str = "medium"
    chunks_retrieved: int = 0
    average_similarity: float = 0.0
    retrieval_time_ms: int = 0
    strategy: str = "dense"
    backend_reachable: bool = True


def _demo_result(question: str, strategy: str, top_k: int) -> QAResult:
    """Canned response so the layout is explorable with no backend running."""
    base_scores = {"dense": 0.87, "sparse": 0.71, "hybrid": 0.91, "bm25": 0.68}
    score = base_scores.get(strategy, 0.8)
    sources = [
        {
            "rank": i + 1,
            "document": f"guideline-{chr(88 + i)}.pdf",
            "score": round(score - i * 0.07, 2),
            "text": f"[demo chunk {i + 1}] Relevant passage discussing '{question[:40]}...' under NICE/WHO guidance §{{}}.".format(
                3 + i
            ),
        }
        for i in range(min(top_k, 5))
    ]
    return QAResult(
        answer=f"(demo answer) Based on {len(sources)} retrieved passages, the recommended approach "
        f"for '{question}' under **{strategy}** retrieval is a short course of first-line therapy, "
        "with escalation guided by response at 48h.",
        sources=sources,
        confidence="high" if score > 0.85 else "medium",
        chunks_retrieved=len(sources),
        average_similarity=sum(s["score"] for s in sources) / len(sources) if sources else 0.0,
        retrieval_time_ms=int(80 + score * 100),
        strategy=strategy,
        backend_reachable=False,
    )


def render_sources_table(sources: list[dict]) -> None:
    """Render the rank/document/score table, or a hint if nothing was retrieved."""
    if not sources:
        st.info("No chunks retrieved — the vector store may be empty. Ingest documents first, then re-run the query.")
        return
    df = pd.DataFrame(sources)
    st.dataframe(df[["rank", "document", "score"]], use_container_width=True, hide_index=True)


def list_documents() -> list[str] | None:
    """Return ingested filenames, or None if the backend is unreachable."""
    try:
        resp = requests.get(DOCUMENTS_URL, timeout=3)
        resp.raise_for_status()
        return resp.json().get("files", [])
    except requests.exceptions.RequestException:
        return None


def upload_document(uploaded_file) -> tuple[bool, str]:
    try:
        resp = requests.post(
            DOCUMENTS_URL,
            files={"file": (uploaded_file.name, uploaded_file.getvalue())},
            timeout=30,
        )
        resp.raise_for_status()
        return True, f"Queued '{uploaded_file.name}' for ingestion."
    except requests.exceptions.RequestException as e:
        return False, f"Upload failed: {e}"


def ingest_from_url(url: str) -> tuple[bool, str]:
    try:
        resp = requests.post(DOCUMENTS_URL + "/ingest-from-url", json={"url": url}, timeout=60)
        resp.raise_for_status()
        return True, f"Queued '{url}' for ingestion."
    except requests.exceptions.RequestException as e:
        return False, f"Ingest failed: {e}"


def delete_document(filename: str) -> tuple[bool, str]:
    try:
        resp = requests.delete(f"{DOCUMENTS_URL}/{filename}", timeout=10)
        resp.raise_for_status()
        return True, f"Deleted '{filename}'."
    except requests.exceptions.RequestException as e:
        return False, f"Delete failed for '{filename}': {e}"


def render_documents_panel() -> None:
    """Shared documents counter + ingest/delete management, used by all variants."""
    files = list_documents()

    if files is None:
        st.sidebar.warning("⚠️ Backend unreachable — document count unavailable.")
        return

    with st.sidebar.expander(f"📄 {len(files)} document(s) ingested", expanded=(len(files) == 0)):
        if len(files) == 0:
            st.caption("No documents ingested yet — queries will return 0 chunks until you add some.")

        st.markdown("**Ingest a document**")
        uploaded = st.file_uploader("Upload file", type=["pdf", "txt", "md", "docx", "doc", "csv", "json"], key="doc_upload")
        if uploaded is not None and st.button("Upload & ingest", key="doc_upload_btn"):
            ok, msg = upload_document(uploaded)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

        url = st.text_input("...or ingest from URL", key="doc_url")
        if st.button("Ingest from URL", key="doc_url_btn") and url:
            ok, msg = ingest_from_url(url)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

        if files:
            st.markdown("**Manage ingested documents**")
            for f in files:
                c1, c2 = st.columns([4, 1])
                c1.write(f)
                if c2.button("🗑️", key=f"del_{f}", help=f"Delete '{f}'"):
                    ok, msg = delete_document(f)
                    (st.success if ok else st.error)(msg)
                    st.rerun()

            st.markdown("---")
            confirm = st.checkbox("Confirm delete ALL documents", key="confirm_delete_all")
            if st.button("🗑️ Delete all", key="delete_all_btn", disabled=not confirm, type="secondary"):
                failures = [f for f in files if not delete_document(f)[0]]
                if failures:
                    st.error(f"Failed to delete: {', '.join(failures)}")
                else:
                    st.success("All documents deleted.")
                st.rerun()


def call_qa_api(question: str, strategy: str, top_k: int, similarity_threshold: float) -> QAResult:
    start = time.perf_counter()
    try:
        resp = requests.post(
            API_URL,
            json={
                "question": question,
                "strategy": strategy,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
            },
            timeout=3,
        )
        resp.raise_for_status()
        data = resp.json()
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return QAResult(
            answer=data["answer"],
            sources=data["sources"],
            confidence=data["confidence"],
            chunks_retrieved=data["chunks_retrieved"],
            average_similarity=data["average_similarity"],
            retrieval_time_ms=elapsed_ms,
            strategy=strategy,
            backend_reachable=True,
        )
    except requests.exceptions.RequestException:
        return _demo_result(question, strategy, top_k)


# ---------------------------------------------------------------------------
# Variant A — Chat-first, inspector inline per turn (closest to #206 feel,
# with #207's controls folded in as a per-message expander)
# ---------------------------------------------------------------------------


def variant_a() -> None:
    st.caption("Variant A — Chat-first, inline per-turn inspector")

    with st.sidebar:
        st.subheader("Retrieval settings")
        strategy = st.selectbox("Strategy", STRATEGIES, index=0)
        top_k = st.slider("Top K", 1, 20, 5)
        threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7)

    if "history_a" not in st.session_state:
        st.session_state.history_a = []

    for turn in st.session_state.history_a:
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            if not turn["result"].backend_reachable:
                st.warning("Backend unreachable — showing demo data.")
            st.write(turn["result"].answer)
            with st.expander(f"🔍 Inspect retrieval ({turn['result'].strategy}, {turn['result'].chunks_retrieved} chunks)"):
                render_sources_table(turn["result"].sources)
                c1, c2, c3 = st.columns(3)
                c1.metric("Avg similarity", f"{turn['result'].average_similarity:.2f}")
                c2.metric("Confidence", turn["result"].confidence)
                c3.metric("Retrieval time", f"{turn['result'].retrieval_time_ms} ms")
                for s in turn["result"].sources:
                    with st.expander(f"#{s['rank']} — {s['document']} (score {s['score']})"):
                        st.write(s["text"])

    question = st.chat_input("Ask a question about your documents...")
    if question:
        result = call_qa_api(question, strategy, top_k, threshold)
        st.session_state.history_a.append({"question": question, "result": result})
        st.rerun()


# ---------------------------------------------------------------------------
# Variant B — Dashboard-first, form input, run-history table for comparison
# ---------------------------------------------------------------------------


def variant_b() -> None:
    st.caption("Variant B — Dashboard form, evidence table, run-history for comparison")

    with st.sidebar:
        st.subheader("Retrieval settings")
        strategy = st.radio("Strategy", STRATEGIES, index=0)
        top_k = st.slider("Top K", 1, 20, 5)
        threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7)

    if "history_b" not in st.session_state:
        st.session_state.history_b = []

    question = st.text_input("Question", placeholder="What treatment is recommended for...?")
    ask = st.button("Ask", type="primary")

    if ask and question:
        result = call_qa_api(question, strategy, top_k, threshold)
        st.session_state.history_b.append(
            {
                "question": question,
                "strategy": strategy,
                "top_k": top_k,
                "avg_similarity": round(result.average_similarity, 3),
                "retrieval_ms": result.retrieval_time_ms,
                "confidence": result.confidence,
            }
        )
        st.session_state.last_result_b = result

    result: QAResult | None = st.session_state.get("last_result_b")
    if result is not None:
        if not result.backend_reachable:
            st.warning("Backend unreachable — showing demo data.")
        with st.container(border=True):
            st.markdown("**Answer**")
            st.write(result.answer)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Retrieval time", f"{result.retrieval_time_ms} ms")
        c2.metric("Chunks retrieved", result.chunks_retrieved)
        c3.metric("Avg similarity", f"{result.average_similarity:.2f}")
        c4.metric("Confidence", result.confidence)

        st.markdown("**Retrieved evidence**")
        render_sources_table(result.sources)
        for s in result.sources:
            with st.expander(f"#{s['rank']} — {s['document']} (score {s['score']})"):
                st.write(s["text"])

    if st.session_state.history_b:
        st.markdown("---")
        st.markdown("**Run history** (compare strategies for the same question)")
        st.dataframe(pd.DataFrame(st.session_state.history_b), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Variant C — Run every strategy at once, compare via tabs + summary table
# ---------------------------------------------------------------------------


def variant_c() -> None:
    st.caption("Variant C — Fan out to all strategies at once, compare via summary table + tabs")

    with st.sidebar:
        st.subheader("Query settings")
        top_k = st.slider("Top K", 1, 20, 5)
        threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7)
        chosen = st.multiselect("Strategies to compare", STRATEGIES, default=STRATEGIES)

    question = st.text_input("Question", placeholder="What treatment is recommended for...?")
    ask = st.button("Compare", type="primary")

    if ask and question and chosen:
        st.session_state.results_c = {s: call_qa_api(question, s, top_k, threshold) for s in chosen}

    results: dict[str, QAResult] = st.session_state.get("results_c", {})
    if results:
        any_demo = any(not r.backend_reachable for r in results.values())
        if any_demo:
            st.warning("Backend unreachable — showing demo data.")

        st.markdown("**Summary**")
        summary_df = pd.DataFrame(
            [
                {
                    "strategy": s,
                    "avg_similarity": round(r.average_similarity, 3),
                    "chunks_retrieved": r.chunks_retrieved,
                    "retrieval_ms": r.retrieval_time_ms,
                    "confidence": r.confidence,
                }
                for s, r in results.items()
            ]
        )
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        tabs = st.tabs(list(results.keys()))
        for tab, (strategy, result) in zip(tabs, results.items(), strict=True):
            with tab:
                st.write(result.answer)
                render_sources_table(result.sources)
                for s in result.sources:
                    with st.expander(f"#{s['rank']} — {s['document']} (score {s['score']})"):
                        st.write(s["text"])


# ---------------------------------------------------------------------------
# Switcher
# ---------------------------------------------------------------------------

VARIANTS = {
    "A": ("Chat-first, inline inspector", variant_a),
    "B": ("Dashboard form + run history", variant_b),
    "C": ("Fan-out compare (tabs)", variant_c),
}

params = st.query_params
current = params.get("variant", "A")
if current not in VARIANTS:
    current = "A"

st.title("RAG Inspector — PROTOTYPE")
render_documents_panel()
label, _ = VARIANTS[current]
picked = st.sidebar.selectbox(
    "Prototype variant",
    list(VARIANTS.keys()),
    index=list(VARIANTS.keys()).index(current),
    format_func=lambda k: f"{k} — {VARIANTS[k][0]}",
)
if picked != current:
    st.query_params["variant"] = picked
    st.rerun()

st.sidebar.markdown("---")

VARIANTS[current][1]()
