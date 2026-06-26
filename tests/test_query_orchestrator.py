"""Tests for the QueryOrchestrator application service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.query_service.application.query_orchestrator import QueryOrchestrator


@pytest.fixture
def mock_deps():
    retrieval = MagicMock()
    retrieval.retrieve.return_value = [
        {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.85, "text": "A chunk of text about diabetes."}
    ]
    llm = MagicMock()
    llm.generate.return_value = "Diabetes is a chronic condition."
    return retrieval, llm


class TestQueryOrchestrator:
    def test_ask_question_success(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        result = orch.ask_question("What is diabetes?")
        assert result["answer"] == "Diabetes is a chronic condition."
        assert result["chunks_retrieved"] == 1
        retrieval.retrieve.assert_called_once()
        llm.generate.assert_called_once()

    def test_ask_question_empty_raises(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        with pytest.raises(ValueError, match="cannot be empty"):
            orch.ask_question("   ")

    def test_ask_question_no_chunks_returns_fallback(self, mock_deps):
        retrieval, llm = mock_deps
        retrieval.retrieve.return_value = []
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        result = orch.ask_question("What is diabetes?")
        assert "couldn't find relevant information" in result["answer"].lower()
        assert result["chunks_retrieved"] == 0

    def test_retrieve_relevant_chunks_empty_raises(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        with pytest.raises(ValueError, match="cannot be empty"):
            orch.retrieve_relevant_chunks("   ")

    def test_retrieve_relevant_chunks_success(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        chunks = orch.retrieve_relevant_chunks("What is diabetes?")
        assert len(chunks) == 1
        assert chunks[0]["similarity_score"] == 0.85

    def test_generate_answer_success(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        chunks = orch.retrieve_relevant_chunks("What is diabetes?")
        answer = orch.generate_answer("What is diabetes?", chunks)
        assert answer == "Diabetes is a chronic condition."

    def test_generate_answer_empty_question_raises(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        with pytest.raises(ValueError, match="cannot be empty"):
            orch.generate_answer("   ", [{"text": "context"}])

    def test_generate_answer_empty_context_raises(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        with pytest.raises(ValueError, match="required"):
            orch.generate_answer("question", [])

    def test_process_in_conversation_no_chunks(self, mock_deps):
        retrieval, llm = mock_deps
        retrieval.retrieve.return_value = []
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)

        from backend.query_service.domain.aggregates import Conversation
        conv = Conversation(session_id="test_session")
        answer = orch.process_in_conversation(conv, "What is diabetes?")
        assert "couldn't find relevant information" in answer.text.lower()
        assert len(conv.pending_events) == 3  # query, context, answer

    def test_process_in_conversation_with_chunks(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)

        from backend.query_service.domain.aggregates import Conversation
        conv = Conversation(session_id="test_session")
        answer = orch.process_in_conversation(conv, "What is diabetes?")
        assert answer.text == "Diabetes is a chronic condition."
        events = conv.pending_events
        assert len(events) >= 3

    def test_process_in_conversation_with_privacy(self, mock_deps):
        retrieval, llm = mock_deps
        privacy = MagicMock()
        privacy.sanitize.return_value = ("sanitized question", {"pii_detected": 0})
        orch = QueryOrchestrator(
            retrieval_service=retrieval,
            completion_service=llm,
            privacy_sanitizer=privacy,
        )

        from backend.query_service.domain.aggregates import Conversation
        conv = Conversation(session_id="test_session")
        answer = orch.process_in_conversation(conv, "What is diabetes?")
        assert answer.text == "Diabetes is a chronic condition."
        privacy.sanitize.assert_called_once()

    def test_no_answer_response(self, mock_deps):
        retrieval, llm = mock_deps
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        result = orch._no_answer_response()
        assert "couldn't find relevant information" in result["answer"].lower()

    def test_generate_answer_stream_not_implemented(self, mock_deps):
        retrieval, llm = mock_deps
        llm.generate_stream.side_effect = NotImplementedError("no stream")
        orch = QueryOrchestrator(retrieval_service=retrieval, completion_service=llm)
        chunks = [{"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.85, "text": "context"}]
        with pytest.raises(NotImplementedError):
            list(orch.generate_answer_stream("What is diabetes?", chunks))

    def test_default_retrieval_creates_adapter(self):
        with patch("backend.query_service.adapters.retrieval.RetrievalAdapter") as mock_cls:
            orch = QueryOrchestrator()
            mock_cls.assert_called_once()

    def test_default_llm_creates_adapter(self):
        with patch("backend.query_service.adapters.llm.LLMCompletionAdapter"):
            orch = QueryOrchestrator()
            assert orch._llm is not None
