"""Tests for the AnswerFormatter application service."""
from __future__ import annotations

from backend.query_service.application.answer_formatter import AnswerFormatter


class TestAnswerFormatter:
    def test_format_answer_with_chunks(self):
        formatter = AnswerFormatter()
        chunks = [
            {"document_name": "doc1.pdf", "page_number": 3, "similarity_score": 0.85, "text": "content about X"},
            {"document_name": "doc2.pdf", "page_number": 5, "similarity_score": 0.72, "text": "more content"},
        ]
        answer = formatter.format_answer("Some answer text", chunks)
        assert answer.text == "Some answer text"
        assert len(answer.citations) == 2
        assert answer.citations[0].document_name == "doc1.pdf"
        assert answer.citations[0].similarity_score == 0.85
        assert answer.confidence.label == "medium"

    def test_format_answer_high_confidence(self):
        formatter = AnswerFormatter()
        chunks = [
            {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.95, "text": "content"}
        ]
        answer = formatter.format_answer("Answer", chunks)
        assert answer.confidence.label == "high"

    def test_format_answer_low_confidence(self):
        formatter = AnswerFormatter()
        chunks = [
            {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.3, "text": "content"}
        ]
        answer = formatter.format_answer("Answer", chunks)
        assert answer.confidence.label == "low"

    def test_format_answer_no_chunks(self):
        formatter = AnswerFormatter()
        answer = formatter.format_answer("Answer", [])
        assert len(answer.citations) == 0
        assert answer.confidence.score == 0.0

    def test_format_answer_strips_answer_text(self):
        formatter = AnswerFormatter()
        chunks = [
            {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.8, "text": "content"}
        ]
        answer = formatter.format_answer("  answer with spaces  ", chunks)
        assert answer.text == "answer with spaces"
