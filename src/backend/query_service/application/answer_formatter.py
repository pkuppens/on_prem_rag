"""Answer post-processing logic.

Handles formatting of generated answers, extraction of citations,
and confidence scoring from retrieval results.
"""

from __future__ import annotations

from typing import Any

from backend.query_service.domain.entities import Answer, Citation
from backend.query_service.domain.value_objects import Confidence


class AnswerFormatter:
    """Formats and enriches generated answers.

    Post-processes raw LLM output to produce structured answers
    with citations and confidence metadata.
    """

    def format_answer(
        self,
        answer_text: str,
        chunks: list[dict[str, Any]],
    ) -> Answer:
        """Create a formatted Answer entity from raw LLM output and chunks.

        Args:
            answer_text: The raw generated answer text.
            chunks: Retrieved chunks used for context.

        Returns:
            Formatted Answer entity with citations and confidence.
        """
        citations = self._extract_citations(chunks)

        avg_similarity = self._calculate_average_similarity(chunks)
        confidence = Confidence.from_average_similarity(avg_similarity)

        return Answer(
            text=answer_text.strip(),
            citations=citations,
            confidence=confidence,
            chunks_retrieved=len(chunks),
            average_similarity=avg_similarity,
        )

    def _extract_citations(self, chunks: list[dict[str, Any]]) -> list[Citation]:
        """Extract citations from retrieval chunks.

        Args:
            chunks: List of retrieval result dicts.

        Returns:
            List of Citation entities.
        """
        citations = []
        seen_docs: set[str] = set()

        for chunk in chunks:
            doc_name = str(chunk.get("document_name", "unknown"))
            if doc_name not in seen_docs:
                seen_docs.add(doc_name)

            citation = Citation.from_chunk(chunk)
            citations.append(citation)

        return citations

    def _calculate_average_similarity(self, chunks: list[dict[str, Any]]) -> float:
        """Calculate the average similarity score from chunks.

        Args:
            chunks: List of retrieval result dicts.

        Returns:
            Average similarity score (0.0 if no chunks).
        """
        if not chunks:
            return 0.0
        scores = [float(chunk.get("similarity_score", 0.0)) for chunk in chunks]
        return sum(scores) / len(scores)
