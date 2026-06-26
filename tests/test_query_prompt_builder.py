"""Tests for the PromptBuilder application service."""
from __future__ import annotations

from backend.query_service.application.prompt_builder import PromptBuilder


class TestPromptBuilder:
    def test_build_qa_prompt_basic(self):
        builder = PromptBuilder()
        chunks = [
            {"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.9, "text": "The sky is blue."}
        ]
        prompt = builder.build_qa_prompt("What color is the sky?", chunks)
        assert "What color is the sky?" in prompt
        assert "The sky is blue." in prompt
        assert "doc.pdf" in prompt

    def test_build_qa_prompt_with_conversation_history(self):
        builder = PromptBuilder()
        chunks = [{"document_name": "doc.pdf", "page_number": 1, "similarity_score": 0.9, "text": "content"}]
        history = [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
        ]
        prompt = builder.build_qa_prompt("new question", chunks, conversation_history=history)
        assert "previous question" in prompt
        assert "previous answer" in prompt
        assert "new question" in prompt

    def test_build_qa_prompt_empty_chunks(self):
        builder = PromptBuilder()
        prompt = builder.build_qa_prompt("What?", [])
        assert "What?" in prompt

    def test_build_direct_prompt_no_history(self):
        builder = PromptBuilder()
        prompt = builder.build_direct_prompt("hello")
        assert prompt == "hello"

    def test_build_direct_prompt_with_history(self):
        builder = PromptBuilder()
        history = [{"role": "user", "content": "previous question"}]
        prompt = builder.build_direct_prompt("new question", history)
        assert "previous question" in prompt
        assert "new question" in prompt

    def test_format_history_empty(self):
        builder = PromptBuilder()
        result = builder._format_history(None)
        assert result == ""

    def test_format_history_with_empty_context(self):
        builder = PromptBuilder()
        result = builder._format_history([])
        assert result == ""

    def test_format_history_with_content(self):
        builder = PromptBuilder()
        result = builder._format_history([{"role": "user", "content": "hi"}])
        assert "Prior conversation" in result
        assert "hi" in result
