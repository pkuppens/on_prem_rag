"""Tests for the Query Service Bounded Context domain layer.

Covers aggregates, entities, value objects, and domain events.
"""

from __future__ import annotations

from backend.query_service.domain.aggregates import Conversation
from backend.query_service.domain.entities import Answer, Citation, Query
from backend.query_service.domain.events import (
    AnswerGenerated,
    CitationIncluded,
    ContextRetrieved,
    QueryReceived,
)
from backend.query_service.domain.value_objects import (
    Confidence,
    ConversationContext,
    QueryIntent,
)


class TestQueryEntity:
    def test_is_empty_returns_true_for_whitespace(self):
        q = Query(text="   ")
        assert q.is_empty()

    def test_is_empty_returns_false_for_text(self):
        q = Query(text="hello")
        assert not q.is_empty()

    def test_sanitized_short(self):
        q = Query(text="short")
        assert q.sanitized(60) == "short"

    def test_sanitized_long(self):
        q = Query(text="a" * 100)
        assert q.sanitized(60).endswith("...")
        assert len(q.sanitized(60)) == 63

    def test_to_dict(self):
        q = Query(text="test question", query_id="q1", user_id="user_1", session_id="sess_1")
        d = q.to_dict()
        assert d["query_id"] == "q1"
        assert d["text_snippet"] == "test question"


class TestAnswerEntity:
    def test_no_answer(self):
        a = Answer.no_answer()
        assert a.text == "I couldn't find relevant information to answer your question."
        assert a.confidence.label == "low"

    def test_no_answer_custom_message(self):
        a = Answer.no_answer("Custom message")
        assert a.text == "Custom message"

    def test_to_dict(self):
        a = Answer(text="some answer", chunks_retrieved=3, average_similarity=0.75)
        d = a.to_dict()
        assert d["answer"] == "some answer"
        assert d["chunks_retrieved"] == 3

    def test_default_citations_empty(self):
        a = Answer(text="answer")
        assert a.citations == []


class TestCitation:
    def test_from_chunk(self):
        chunk = {
            "document_name": "doc.pdf",
            "page_number": 3,
            "similarity_score": 0.85,
            "text": "Some relevant content here",
        }
        c = Citation.from_chunk(chunk)
        assert c.document_name == "doc.pdf"
        assert c.page_number == 3
        assert c.similarity_score == 0.85

    def test_from_chunk_truncates_long_text(self):
        chunk = {
            "document_name": "doc.pdf",
            "page_number": 1,
            "similarity_score": 0.9,
            "text": "x" * 500,
        }
        c = Citation.from_chunk(chunk, preview_length=100)
        assert len(c.text_preview) == 103

    def test_from_chunk_falls_back_to_unknown(self):
        c = Citation.from_chunk({"text": "hello"})
        assert c.document_name == "unknown"

    def test_to_dict(self):
        chunk = {"document_name": "doc.pdf", "page_number": 2, "similarity_score": 0.75, "text": "text"}
        c = Citation.from_chunk(chunk)
        d = c.to_dict()
        assert d["document_name"] == "doc.pdf"
        assert d["page_number"] == 2


class TestConfidence:
    def test_from_high_similarity(self):
        c = Confidence.from_average_similarity(0.9)
        assert c.label == "high"
        assert c.score == 0.9

    def test_from_medium_similarity(self):
        c = Confidence.from_average_similarity(0.7)
        assert c.label == "medium"

    def test_from_low_similarity(self):
        c = Confidence.from_average_similarity(0.3)
        assert c.label == "low"

    def test_low_factory(self):
        c = Confidence.low()
        assert c.label == "low"
        assert c.score == 0.0

    def test_to_dict(self):
        c = Confidence(label="high", score=0.85)
        d = c.to_dict()
        assert d["label"] == "high"
        assert d["score"] == 0.85


class TestConversationContext:
    def test_from_history(self):
        ctx = ConversationContext.from_history([{"role": "user", "content": "hi"}], max_messages=6)
        assert len(ctx.messages) == 1
        assert ctx.messages[0]["content"] == "hi"

    def test_from_history_none(self):
        ctx = ConversationContext.from_history(None)
        assert ctx.is_empty

    def test_formatted_empty(self):
        ctx = ConversationContext.from_history(None)
        assert ctx.formatted == ""

    def test_formatted(self):
        ctx = ConversationContext.from_history([
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
        ])
        expected = "user: hello\nassistant: world"
        assert ctx.formatted == expected

    def test_to_list(self):
        history = [{"role": "user", "content": "hi"}]
        ctx = ConversationContext.from_history(history)
        assert ctx.to_list() == history


class TestConversationAggregate:
    def test_initial_state(self):
        conv = Conversation(session_id="sess_1")
        assert conv.message_count == 0
        assert conv.last_user_message is None

    def test_add_query(self):
        conv = Conversation(session_id="sess_1")
        query = Query(text="hello")
        event = conv.add_query(query)
        assert conv.message_count == 1
        assert conv.last_user_message == "hello"
        assert isinstance(event, QueryReceived)
        assert event.text == "hello"

    def test_add_answer(self):
        conv = Conversation(session_id="sess_1")
        query = Query(text="hello")
        answer = Answer(text="world", confidence=Confidence(label="high", score=0.9), chunks_retrieved=3, average_similarity=0.9)
        conv.add_query(query)
        event = conv.add_answer(query, answer, [])
        assert conv.message_count == 2
        assert isinstance(event, AnswerGenerated)
        assert event.confidence == "high"

    def test_add_context_retrieved(self):
        conv = Conversation(session_id="sess_1")
        event = conv.add_context_retrieved("q1", [{"text": "chunk"}], "hybrid")
        assert isinstance(event, ContextRetrieved)
        assert event.chunk_count == 1
        assert event.strategy == "hybrid"

    def test_get_context_limits_messages(self):
        conv = Conversation(session_id="sess_1")
        for i in range(10):
            conv.add_query(Query(text=f"q{i}"))
        ctx = conv.get_context(max_messages=4)
        assert len(ctx.messages) == 4
        assert ctx.messages[-1]["content"] == "q9"

    def test_clear_events(self):
        conv = Conversation(session_id="sess_1")
        conv.add_query(Query(text="hi"))
        events = conv.clear_events()
        assert len(events) == 1
        assert conv.pending_events == []


class TestDomainEvents:
    def test_query_received_to_dict(self):
        e = QueryReceived(query_id="q1", text="hello", user_id="u1", session_id="s1")
        d = e.to_dict()
        assert d["event"] == "QueryReceived"
        assert d["query_id"] == "q1"

    def test_context_retrieved_to_dict(self):
        e = ContextRetrieved(query_id="q1", chunk_count=3, strategy="hybrid")
        d = e.to_dict()
        assert d["event"] == "ContextRetrieved"
        assert d["chunk_count"] == 3

    def test_answer_generated_to_dict(self):
        e = AnswerGenerated(query_id="q1", confidence="high", chunks_retrieved=3, session_id="s1")
        d = e.to_dict()
        assert d["event"] == "AnswerGenerated"
        assert d["confidence"] == "high"

    def test_citation_included_to_dict(self):
        e = CitationIncluded(query_id="q1", citation_count=2)
        d = e.to_dict()
        assert d["event"] == "CitationIncluded"
        assert d["citation_count"] == 2

    def test_query_intent_enum(self):
        assert QueryIntent.INFORMATION_SEEKING.value == 1
        assert QueryIntent.UNKNOWN.value == 4
