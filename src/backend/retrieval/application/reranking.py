"""Re-ranking strategies: CrossEncoder, MMR.

CrossEncoderReranker uses a cross-encoder model for semantic relevance
re-ranking. MMR is in domain/services.py as a standalone function.
"""

from __future__ import annotations

from typing import Any


class CrossEncoderReranker:
    """Re-rank candidates using a cross-encoder model."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Re-rank candidates by cross-encoder relevance."""
        if not candidates:
            return []

        model = self._load_model()
        pairs = [(query, c.get("text", "")) for c in candidates]
        scores = model.predict(pairs)

        indexed = [(float(scores[i]), candidates[i]) for i in range(len(candidates))]
        indexed.sort(key=lambda x: -x[0])

        # Normalize scores to [0, 1]
        if indexed:
            min_s, max_s = (
                min(s[0] for s in indexed),
                max(s[0] for s in indexed),
            )
            norm = (max_s - min_s) or 1.0
        else:
            norm = 1.0

        results = []
        for raw_score, item in indexed[:top_k]:
            copy = dict(item)
            copy["similarity_score"] = min(
                1.0,
                max(
                    0.0,
                    (raw_score - min_s) / norm if norm else 0.0,
                ),
            )
            results.append(copy)

        return results
