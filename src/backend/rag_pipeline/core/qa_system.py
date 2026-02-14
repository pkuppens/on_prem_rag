"""Question Answering system for the RAG pipeline.

This module implements the core Q&A functionality as specified in STORY-003.
It provides vector search retrieval and LLM integration for answering questions
about uploaded documents.

See docs/technical/LLM.md for design details.
"""

from __future__ import annotations

import os
from typing import Any

from backend.rag_pipeline.config.parameter_sets import get_param_set
from backend.rag_pipeline.core.embeddings import query_embeddings
from backend.rag_pipeline.core.llm_providers import LLMProvider, OllamaProvider
from backend.rag_pipeline.core.vector_store import get_vector_store_manager_from_env

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class QASystem:
    """Question Answering system that combines vector search with LLM generation."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        """Initialize the QA system.

        Args:
            llm_provider: Optional LLM provider. If None, will use default Ollama provider.
        """
        self.llm_provider = llm_provider or self._create_default_llm_provider()
        self.vector_store_manager = get_vector_store_manager_from_env()

    def _create_default_llm_provider(self) -> LLMProvider:
        """Create default Ollama LLM provider.

        Returns:
            Configured Ollama provider instance.
        """
        model_name = os.getenv("OLLAMA_MODEL", "mistral:7b")
        ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaProvider(model_name=model_name, config={"host": ollama_host})

    def retrieve_relevant_chunks(self, question: str, top_k: int = 5, similarity_threshold: float = 0.7) -> list[dict[str, Any]]:
        """Retrieve relevant document chunks for a question.

        Args:
            question: The question to search for
            top_k: Maximum number of chunks to retrieve
            similarity_threshold: Minimum similarity score for results

        Returns:
            List of relevant chunks with metadata and similarity scores

        Raises:
            ValueError: If question is empty
            RuntimeError: If retrieval fails
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            # Get default parameter set for embedding model
            from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME

            params = get_param_set(DEFAULT_PARAM_SET_NAME)

            # Query embeddings using existing function
            results = query_embeddings(
                query=question,
                model_name=params.embedding.model_name,
                persist_dir=self.vector_store_manager.config.persist_directory,
                collection_name=self.vector_store_manager.config.collection_name,
                top_k=top_k,
            )

            # Filter results by similarity threshold
            filtered_results = [result for result in results["all_results"] if result["similarity_score"] >= similarity_threshold]

            logger.info(
                "Retrieved chunks for question",
                question=question,
                total_results=len(results["all_results"]),
                filtered_results=len(filtered_results),
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
            question: The question to answer
            context_chunks: Relevant document chunks as context
            conversation_history: Optional prior messages [{role, content}] for multi-turn context

        Returns:
            Generated answer text

        Raises:
            ValueError: If question is empty or no context provided
            RuntimeError: If LLM generation fails
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        if not context_chunks:
            raise ValueError("Context chunks are required for answer generation")

        try:
            # Create prompt with context
            context_text = "\n\n".join(
                [f"Document: {chunk['document_name']}\nContent: {chunk['text']}" for chunk in context_chunks]
            )

            history_section = ""
            if conversation_history:
                history_lines = [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history[-6:]]
                history_section = f"\n\nPrior conversation:\n" + "\n".join(history_lines) + "\n\n"

            prompt = f"""Based on the following context from uploaded documents, please answer the question.
{history_section}Context:
{context_text}

Question: {question}

Answer:"""

            # Generate answer using LLM
            answer = self.llm_provider.generate_answer(prompt)

            logger.info("Generated answer", question=question, context_chunks=len(context_chunks), answer_length=len(answer))

            return answer.strip()

        except Exception as e:
            logger.error("Error during answer generation", question=question, error=str(e))
            raise RuntimeError(f"Failed to generate answer: {str(e)}") from e

    def ask_question(self, question: str, top_k: int = 5, similarity_threshold: float = 0.7) -> dict[str, Any]:
        """Ask a question and get an answer with sources.

        Args:
            question: The question to ask
            top_k: Maximum number of chunks to retrieve
            similarity_threshold: Minimum similarity score for results

        Returns:
            Dictionary containing answer, sources, and metadata

        Raises:
            ValueError: If question is empty
            RuntimeError: If Q&A process fails
        """
        if not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            # Retrieve relevant chunks
            chunks = self.retrieve_relevant_chunks(question, top_k, similarity_threshold)

            if not chunks:
                return {
                    "answer": "I couldn't find relevant information to answer your question.",
                    "sources": [],
                    "confidence": "low",
                    "chunks_retrieved": 0,
                }

            # Generate answer
            answer = self.generate_answer(question, chunks)

            # Prepare sources
            sources = [
                {
                    "document_name": chunk["document_name"],
                    "page_number": chunk["page_number"],
                    "similarity_score": chunk["similarity_score"],
                    "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                }
                for chunk in chunks
            ]

            # Determine confidence based on similarity scores
            avg_similarity = sum(chunk["similarity_score"] for chunk in chunks) / len(chunks)
            confidence = "high" if avg_similarity > 0.8 else "medium" if avg_similarity > 0.6 else "low"

            result = {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "chunks_retrieved": len(chunks),
                "average_similarity": avg_similarity,
            }

            logger.info(
                "Question answered successfully",
                question=question,
                answer_length=len(answer),
                sources_count=len(sources),
                confidence=confidence,
            )

            return result

        except Exception as e:
            logger.error("Error during question answering", question=question, error=str(e))
            raise RuntimeError(f"Failed to answer question: {str(e)}") from e
