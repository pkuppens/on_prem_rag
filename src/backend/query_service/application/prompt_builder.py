"""Prompt construction logic for the RAG query workflow.

Builds prompt strings from user questions, retrieved context chunks,
and conversation history. Extracted from the QASystem to keep the
orchestrator focused on workflow coordination.
"""

from __future__ import annotations

from typing import Any

from backend.query_service.domain.value_objects import ConversationContext


class PromptBuilder:
    """Builds LLM prompts from query components.

    Constructs prompts by combining:
    - System instructions
    - Conversation history (for multi-turn context)
    - Retrieved document context
    - The user's question
    """

    SYSTEM_TEMPLATE: str = "Based on the following context from uploaded documents, please answer the question."

    def build_qa_prompt(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Build a complete prompt for question answering.

        Args:
            question: The user's question.
            context_chunks: Retrieved document chunks.
            conversation_history: Optional prior conversation messages.

        Returns:
            Formatted prompt string for LLM generation.
        """
        context_text = self._format_context(context_chunks)
        history_section = self._format_history(conversation_history)

        parts = []
        parts.append(self.SYSTEM_TEMPLATE)

        if history_section:
            parts.append(history_section)

        parts.append(f"Context:\n{context_text}")
        parts.append(f"Question: {question}")
        parts.append("Answer:")

        return "\n\n".join(parts)

    def build_direct_prompt(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Build a prompt without RAG context (direct LLM response).

        Used for direct/streaming mode where no retrieval is needed.

        Args:
            question: The user's question.
            conversation_history: Optional prior conversation messages.

        Returns:
            Formatted prompt string.
        """
        if not conversation_history:
            return question

        history_text = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history[-4:])
        return f"Prior conversation:\n{history_text}\n\nUser: {question}\n\nAssistant:"

    def _format_context(self, chunks: list[dict[str, Any]]) -> str:
        """Format document chunks into a context block.

        Args:
            chunks: List of retrieval result dicts.

        Returns:
            Formatted context string.
        """
        return "\n\n".join(
            [f"Document: {chunk['document_name']}\nContent: {chunk['text']}" for chunk in chunks]
        )

    def _format_history(self, history: list[dict[str, str]] | None) -> str:
        """Format conversation history into a string section.

        Args:
            history: List of {role, content} dicts.

        Returns:
            Formatted history string or empty string.
        """
        if not history:
            return ""

        ctx = ConversationContext.from_history(history)
        if ctx.is_empty:
            return ""

        return f"Prior conversation:\n{ctx.formatted}"
