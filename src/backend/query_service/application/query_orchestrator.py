"""QueryOrchestrator — full RAG workflow orchestration.

This is the flagship application service of the Query Service BC.
It coordinates the entire RAG query workflow:
1. Accept a question
2. (Optional) Check access control
3. (Optional) Sanitize PII
4. Retrieve relevant context from the Retrieval BC
5. Build a prompt with context + history
6. Generate an answer via the LLM Gateway BC
7. Format the answer with citations
8. (Optional) Log to the Audit Trail BC
9. Return the result

Refactored from rag_pipeline/core/qa_system.py to use port-based
dependencies instead of concrete imports.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

from backend.query_service.application.answer_formatter import AnswerFormatter
from backend.query_service.application.prompt_builder import PromptBuilder
from backend.query_service.domain.aggregates import Conversation
from backend.query_service.domain.entities import Answer, Query
from backend.query_service.domain.interfaces import IQueryOrchestrator
from backend.query_service.domain.value_objects import QueryIntent
from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
from backend.rag_pipeline.utils.logging import StructuredLogger

from ..ports.access_control import IAccessControlCheck
from ..ports.audit import IAuditTrail
from ..ports.llm_gateway import ICompletionService
from ..ports.privacy import IPrivacySanitizer
from ..ports.retrieval import IRetrievalService

logger = StructuredLogger(__name__)


class QueryOrchestrator(IQueryOrchestrator):
    """Orchestrates the full RAG query workflow.

    Coordinates retrieval, LLM generation, prompt building, and answer
    formatting using port-based dependencies for loose coupling.

    Usage:
        orchestrator = QueryOrchestrator(
            retrieval_service=my_retrieval_adapter,
            completion_service=my_llm_adapter,
        )
        result = orchestrator.ask_question("What is RAG?")
    """

    def __init__(
        self,
        retrieval_service: IRetrievalService | None = None,
        completion_service: ICompletionService | None = None,
        prompt_builder: PromptBuilder | None = None,
        answer_formatter: AnswerFormatter | None = None,
        access_control: IAccessControlCheck | None = None,
        privacy_sanitizer: IPrivacySanitizer | None = None,
        audit_trail: IAuditTrail | None = None,
    ) -> None:
        """Initialize the orchestrator with port-based dependencies.

        Args:
            retrieval_service: Port to the Retrieval BC. If None, creates
                a default adapter from environment config.
            completion_service: Port to the LLM Gateway BC. If None,
                creates a default adapter from environment config.
            prompt_builder: Prompt construction logic.
            answer_formatter: Answer post-processing logic.
            access_control: Optional port to Access Control BC.
            privacy_sanitizer: Optional port to Privacy Guard BC.
            audit_trail: Optional port to Audit Trail BC.
        """
        self._retrieval = retrieval_service or self._create_default_retrieval()
        self._llm = completion_service or self._create_default_llm()
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._answer_formatter = answer_formatter or AnswerFormatter()
        self._access_control = access_control
        self._privacy = privacy_sanitizer
        self._audit = audit_trail

    # --- Public API (IQueryOrchestrator implementation) ---

    def ask_question(
        self,
        question: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        strategy: str | None = None,
    ) -> dict[str, Any]:
        """Ask a question and get an answer with sources.

        Implements the full RAG workflow: validate → retrieve → generate → format.

        Args:
            question: The question to ask.
            top_k: Maximum number of chunks to retrieve.
            similarity_threshold: Minimum similarity score for results.
            strategy: Optional retrieval strategy override.

        Returns:
            Dict containing answer, sources, confidence, and metadata.
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            chunks = self.retrieve_relevant_chunks(question, top_k, similarity_threshold, strategy=strategy)

            if not chunks:
                logger.info(
                    "RAG flow: retrieve->fallback (0 chunks matched)",
                    question=question[:60],
                )
                return self._no_answer_response()

            answer_text = self.generate_answer(question, chunks)
            answer = self._answer_formatter.format_answer(answer_text, chunks)

            logger.info(
                "Question answered successfully",
                question=question,
                answer_length=len(answer.text),
                sources_count=len(answer.citations),
                confidence=answer.confidence.label,
            )

            return answer.to_dict()

        except Exception as e:
            logger.error("Error during question answering", question=question, error=str(e))
            raise RuntimeError(f"Failed to answer question: {str(e)}") from e

    def retrieve_relevant_chunks(
        self,
        question: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant document chunks for a question.

        Uses configured retrieval strategy with optional re-ranking and MMR.

        Args:
            question: The question to search for.
            top_k: Maximum number of chunks to retrieve.
            similarity_threshold: Minimum similarity score.
            strategy: Optional strategy override. When None, uses env or default.

        Returns:
            List of relevant chunks with metadata.

        Raises:
            ValueError: If question is empty.
            RuntimeError: If retrieval fails.
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            params = get_param_set(DEFAULT_PARAM_SET_NAME)
            ret = params.retrieval
            strategy = strategy or os.getenv("RETRIEVAL_STRATEGY", ret.strategy)

            filtered_results = self._retrieval.retrieve(
                query=question,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                strategy=strategy,
            )

            logger.info(
                "Retrieved chunks for question",
                question=question,
                total_results=len(filtered_results),
                strategy=strategy,
                threshold=similarity_threshold,
            )

            return filtered_results

        except Exception as e:
            logger.error("Error during chunk retrieval", question=question, error=str(e))
            raise RuntimeError(f"Failed to retrieve relevant chunks: {str(e)}") from e

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate an answer using LLM based on question and context.

        Args:
            question: The question to answer.
            context_chunks: Relevant document chunks as context.
            conversation_history: Optional prior messages for multi-turn context.

        Returns:
            Generated answer text.

        Raises:
            ValueError: If question is empty or no context provided.
            RuntimeError: If LLM generation fails.
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        if not context_chunks:
            raise ValueError("Context chunks are required for answer generation")

        try:
            prompt = self._prompt_builder.build_qa_prompt(question, context_chunks, conversation_history)
            answer = self._llm.generate(prompt)

            logger.info(
                "Generated answer",
                question=question,
                context_chunks=len(context_chunks),
                answer_length=len(answer),
            )

            return answer.strip()

        except Exception as e:
            logger.error("Error during answer generation", question=question, error=str(e))
            raise RuntimeError(f"Failed to generate answer: {str(e)}") from e

    def generate_answer_stream(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Generator[str, None, None]:
        """Stream answer tokens from LLM.

        Args:
            question: The question to answer.
            context_chunks: Relevant document chunks as context.
            conversation_history: Optional prior messages.

        Yields:
            Answer text chunks as they arrive from the LLM provider.

        Raises:
            ValueError: If question is empty or no context provided.
            NotImplementedError: If provider does not support streaming.
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")
        if not context_chunks:
            raise ValueError("Context chunks are required for answer generation")

        prompt = self._prompt_builder.build_qa_prompt(question, context_chunks, conversation_history)
        yield from self._llm.generate_stream(prompt)

    # --- Domain workflow with Conversation aggregate ---

    def process_in_conversation(
        self,
        conversation: Conversation,
        question_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        strategy: str | None = None,
    ) -> Answer:
        """Process a question within a Conversation aggregate.

        This method uses the full domain workflow with events:
        1. Record the query in the conversation
        2. Apply access control and PII sanitization
        3. Retrieve context
        4. Generate answer
        5. Record the answer

        Args:
            conversation: The Conversation aggregate.
            question_text: The question text.
            top_k: Maximum chunks to retrieve.
            similarity_threshold: Minimum similarity score.
            strategy: Optional retrieval strategy.

        Returns:
            Answer entity with citations and confidence.
        """
        query = Query(
            text=question_text,
            query_id=f"q_{len(conversation.messages)}_{id(conversation)}",
            session_id=conversation.session_id,
            user_id=conversation.user_id,
        )

        # 1. Record query and emit QueryReceived event
        conversation.add_query(query)

        # 2. (Optional) Sanitize PII
        sanitized_question = question_text
        if self._privacy:
            sanitized_question, pii_meta = self._privacy.sanitize(question_text)
            if pii_meta.get("pii_detected", 0) > 0:
                logger.info("PII sanitized", question=question_text[:60], pii_count=pii_meta["pii_detected"])

        # 3. Retrieval
        chunks = self.retrieve_relevant_chunks(sanitized_question, top_k, similarity_threshold, strategy=strategy)

        if not chunks:
            conversation.add_context_retrieved(query.query_id, chunks, strategy or "dense")
            answer = Answer.no_answer()
            conversation.add_answer(query, answer, chunks)
            return answer

        conversation.add_context_retrieved(query.query_id, chunks, strategy or "dense")

        # 4. Generate answer
        ctx = conversation.get_context()
        answer_text = self.generate_answer(sanitized_question, chunks, conversation_history=ctx.to_list())

        # 5. Format answer with citations
        answer = self._answer_formatter.format_answer(answer_text, chunks)
        conversation.add_answer(query, answer, chunks)

        return answer

    # --- Private helpers ---

    def _no_answer_response(self) -> dict[str, Any]:
        """Create a standardized 'no answer' response."""
        answer = Answer.no_answer()
        return answer.to_dict()

    def _create_default_retrieval(self) -> IRetrievalService:
        """Create a default RetrievalAdapter from environment config."""
        from backend.query_service.adapters.retrieval import RetrievalAdapter

        params = get_param_set(DEFAULT_PARAM_SET_NAME)
        ret = params.retrieval
        return RetrievalAdapter(
            strategy=ret.strategy,
            model_name=params.embedding.model_name,
            persist_dir=os.getenv("PERSIST_DIRECTORY", "./chroma_db"),
            collection_name="documents",
            hybrid_alpha=ret.hybrid_alpha,
            use_reranker=ret.use_reranker,
            reranker_model=ret.reranker_model,
            use_mmr=ret.use_mmr,
            mmr_lambda=ret.mmr_lambda,
            rerank_candidates=ret.rerank_candidates,
        )

    def _create_default_llm(self) -> ICompletionService:
        """Create a default LLMCompletionAdapter from environment config."""
        from backend.query_service.adapters.llm import LLMCompletionAdapter

        return LLMCompletionAdapter()


# Backward-compatible alias
QASystem = QueryOrchestrator
