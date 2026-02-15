"""Tests for retrieval strategies: dense, sparse, hybrid, re-ranking, MMR.

Use case tests per issue #79 plan. Unit tests use mocks; integration tests
requiring ingested medical documents are marked @pytest.mark.slow.

See tmp/github/issue-plans/issue-79-hybrid-retrieval.md for design.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.rag_pipeline.core.retrieval import (
    CrossEncoderReranker,
    DenseRetriever,
    HybridRetriever,
    QueryEmbeddingsDenseRetriever,
    _cosine_similarity,
    _reciprocal_rank_fusion,
    mmr_rerank,
)


class TestReciprocalRankFusion:
    """Tests for RRF merge used in hybrid retrieval."""

    def test_rrf_merges_two_lists(self):
        """As a user I want hybrid to combine dense and sparse results, so I get both semantic and keyword matches.
        Technical: RRF merges ranked lists without score calibration.
        """
        dense = [
            {"record_id": "a", "text": "A", "similarity_score": 0.9},
            {"record_id": "b", "text": "B", "similarity_score": 0.8},
            {"record_id": "c", "text": "C", "similarity_score": 0.7},
        ]
        sparse = [
            {"record_id": "c", "text": "C", "similarity_score": 0.95},
            {"record_id": "a", "text": "A", "similarity_score": 0.85},
            {"record_id": "d", "text": "D", "similarity_score": 0.75},
        ]
        merged = _reciprocal_rank_fusion([dense, sparse])
        ids = [m["record_id"] for m in merged]
        # Items in both lists should rank higher; c appears in both at good ranks
        assert len(merged) == 4
        assert "a" in ids and "b" in ids and "c" in ids and "d" in ids

    def test_rrf_returns_empty_for_empty_input(self):
        """Technical: RRF with empty list returns empty."""
        assert _reciprocal_rank_fusion([]) == []


class TestCosineSimilarity:
    """Tests for cosine similarity helper."""

    def test_identical_vectors_score_one(self):
        """Technical: Identical vectors have similarity 1.0."""
        v = [1.0, 2.0, 3.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        """Technical: Orthogonal vectors have similarity 0."""
        assert _cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_empty_vectors_return_zero(self):
        """Technical: Empty or mismatched length return 0."""
        assert _cosine_similarity([], [1, 2]) == 0.0
        assert _cosine_similarity([1], [1, 2]) == 0.0


class TestHybridRetriever:
    """Tests for hybrid dense+sparse retrieval."""

    def test_hybrid_merges_dense_and_sparse(self):
        """As a user I want hybrid retrieval to combine semantic and keyword results, so I get better coverage.
        Technical: HybridRetriever uses RRF over dense and sparse outputs.
        """
        mock_dense = MagicMock(spec=DenseRetriever)
        mock_dense.retrieve.return_value = [
            {"record_id": "1", "text": "dense one", "similarity_score": 0.9},
        ]
        mock_sparse = MagicMock()
        mock_sparse.retrieve.return_value = [
            {"record_id": "2", "text": "sparse two", "similarity_score": 0.8},
        ]
        hybrid = HybridRetriever(mock_dense, mock_sparse)
        results = hybrid.retrieve("test query", top_k=5)
        assert len(results) <= 5
        mock_dense.retrieve.assert_called_once_with("test query", top_k=10)
        mock_sparse.retrieve.assert_called_once_with("test query", top_k=10)


class TestMMRRerank:
    """Tests for MMR diversity re-ranking."""

    def test_mmr_returns_top_k(self):
        """As a user I want diverse results for broad queries, so I see different aspects.
        Technical: MMR returns exactly top_k items.
        """
        candidates = [
            {"text": "chunk A", "similarity_score": 0.9},
            {"text": "chunk B", "similarity_score": 0.85},
            {"text": "chunk C", "similarity_score": 0.8},
        ]
        query_emb = [1.0, 0.0, 0.0]
        def emb_fn(t: str) -> list[float]:
            return [1.0, 0.0, 0.0] if "A" in t else [0.9, 0.1, 0.0]
        result = mmr_rerank(candidates, query_emb, emb_fn, lambda_param=0.7, top_k=2)
        assert len(result) == 2

    def test_mmr_empty_candidates_returns_empty(self):
        """Technical: MMR with no candidates returns empty list."""
        assert mmr_rerank([], [1.0], lambda t: [1.0], top_k=5) == []


class TestCrossEncoderReranker:
    """Tests for cross-encoder re-ranking."""

    @pytest.mark.slow
    def test_reranker_returns_top_k(self):
        """As a user I want re-ranking to improve relevance order, so safety-critical chunks rank higher.
        Technical: CrossEncoderReranker returns top_k from candidates.
        """
        reranker = CrossEncoderReranker()
        candidates = [
            {"text": "Drug X is contraindicated in pregnancy.", "similarity_score": 0.7},
            {"text": "Drug X is safe in pregnancy.", "similarity_score": 0.8},
        ]
        result = reranker.rerank("Is drug X safe in pregnancy?", candidates, top_k=2)
        assert len(result) == 2
        assert all("text" in r and "similarity_score" in r for r in result)

    def test_reranker_empty_returns_empty(self):
        """Technical: Reranker with no candidates returns empty."""
        reranker = CrossEncoderReranker()
        assert reranker.rerank("query", [], top_k=5) == []


class TestRetrievalService:
    """Tests for RetrievalService strategy orchestration."""

    @patch("backend.rag_pipeline.core.retrieval.BM25SparseRetriever")
    @patch("backend.rag_pipeline.core.retrieval.BM25Store")
    def test_dense_strategy_uses_dense_retriever(self, mock_store, mock_sparse):
        """As a user I want dense-only retrieval as default, so behaviour is unchanged.
        Technical: strategy=dense delegates to DenseRetriever.
        """
        from backend.rag_pipeline.core.retrieval import RetrievalService, create_retrieval_service

        service = create_retrieval_service(
            strategy="dense",
            model_name="BAAI/bge-small-en-v1.5",
            persist_dir="data/chroma",
        )
        assert service.strategy == "dense"
