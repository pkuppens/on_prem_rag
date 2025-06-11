"""Tests for the embeddings module."""

from pathlib import Path

import pytest
from llama_index.core import Document
from rag_pipeline.config.parameter_sets import TEST_PARAMS
from rag_pipeline.core.embeddings import (
    EmbeddingResult,
    QueryResult,
    embed_text_nodes,
    process_pdf,
    query_embeddings,
    store_embeddings,
)


class TestEmbeddings:
    """Test the embedding functionality."""

    def test_embed_text_nodes(self):
        """Test embedding text nodes."""
        documents = [
            Document(text="This is a test document."),
            Document(text="This is another test document."),
        ]

        embeddings = embed_text_nodes(documents, TEST_PARAMS.embedding.model_name)

        # Verify embeddings structure
        assert len(embeddings) == len(documents)
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) > 0 for emb in embeddings)
        assert all(isinstance(val, float) for emb in embeddings for val in emb)

    def test_store_embeddings_basic(self, test_case_dir):
        """Test basic embedding storage functionality."""
        # Create test embeddings
        ids = ["doc1", "doc2"]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        metadatas = [
            {"text": "First document", "source": "test1.txt"},
            {"text": "Second document", "source": "test2.txt"},
        ]

        manager = store_embeddings(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            persist_dir=test_case_dir,
            collection_name="test_collection",
            deduplicate=False,
        )

        # Verify storage
        assert manager._collection.count() == 2

    def test_store_embeddings_deduplication(self, test_case_dir):
        """Test embedding storage with deduplication."""
        # Create embeddings with duplicate content
        ids = ["doc1", "doc2", "doc3"]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        metadatas = [
            {"text": "Same content", "source": "test1.txt"},
            {"text": "Different content", "source": "test2.txt"},
            {"text": "Same content", "source": "test3.txt"},  # Duplicate
        ]

        manager = store_embeddings(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            persist_dir=test_case_dir,
            collection_name="test_dedup",
            deduplicate=True,
        )

        # Should only store 2 items (one duplicate removed)
        assert manager._collection.count() == 2

    def test_process_pdf_integration(self, test_data_dir, test_case_dir):
        """Test the complete PDF processing pipeline."""
        pdf_path = test_data_dir / "2005.11401v4.pdf"  # Use smaller PDF

        chunks, records = process_pdf(
            pdf_path=pdf_path,
            model_name=TEST_PARAMS.embedding.model_name,
            persist_dir=test_case_dir,
            collection_name="test_pdf",
            chunk_size=TEST_PARAMS.chunking.chunk_size,
            chunk_overlap=TEST_PARAMS.chunking.chunk_overlap,
            max_pages=2,  # Limit to 2 pages for faster testing
            deduplicate=True,
        )

        # Verify results
        assert chunks > 0
        assert records > 0
        assert records <= chunks  # Deduplication may reduce count

    def test_process_pdf_expected_values(self, test_data_dir, test_case_dir):
        """Test PDF processing returns expected values for specific test file."""
        pdf_path = test_data_dir / "2005.11401v4.pdf"

        # Process with known parameters
        chunks, records = process_pdf(
            pdf_path=pdf_path,
            model_name=TEST_PARAMS.embedding.model_name,
            persist_dir=test_case_dir,
            collection_name="expected_test",
            chunk_size=128,  # Small chunks for predictable results
            chunk_overlap=0,  # No overlap for simpler testing
            max_pages=1,  # Single page
            deduplicate=True,
        )

        # Test specific expectations
        assert chunks > 0, "Should create at least one chunk"
        assert chunks < 50, "Should not create excessive chunks for single page"
        assert records == chunks, "No duplicates expected in single PDF page"

    def test_query_embeddings(self, test_data_dir, test_case_dir):
        """Test querying stored embeddings."""
        pdf_path = test_data_dir / "2005.11401v4.pdf"

        # First, store some embeddings
        process_pdf(
            pdf_path=pdf_path,
            model_name=TEST_PARAMS.embedding.model_name,
            persist_dir=test_case_dir,
            collection_name="query_test",
            max_pages=1,
            deduplicate=True,
        )

        # Query the embeddings
        result = query_embeddings(
            query="test research paper",
            model_name=TEST_PARAMS.embedding.model_name,
            persist_dir=test_case_dir,
            collection_name="query_test",
            top_k=3,
        )

        # Verify query result structure
        assert isinstance(result, dict)
        assert "primary_result" in result
        assert "all_results" in result
        assert isinstance(result["all_results"], list)

        if result["all_results"]:
            # Check structure of individual results
            first_result = result["all_results"][0]
            assert "text" in first_result
            assert "similarity_score" in first_result
            assert "document_id" in first_result
            assert "document_name" in first_result
            assert "chunk_index" in first_result
            assert "record_id" in first_result

            # Verify similarity scores are in valid range
            for res in result["all_results"]:
                assert -1 <= res["similarity_score"] <= 1

    def test_query_embeddings_empty_collection(self, test_case_dir):
        """Test querying an empty collection."""
        result = query_embeddings(
            query="test query",
            model_name=TEST_PARAMS.embedding.model_name,
            persist_dir=test_case_dir,
            collection_name="empty_test",
            top_k=3,
        )

        # Should return empty results
        assert result["primary_result"] == ""
        assert result["all_results"] == []

    def test_embeddings_deterministic(self):
        """Test that embeddings are deterministic for same input."""
        document = Document(text="Consistent test content for deterministic testing.")

        # Generate embeddings twice
        embeddings1 = embed_text_nodes([document], TEST_PARAMS.embedding.model_name)
        embeddings2 = embed_text_nodes([document], TEST_PARAMS.embedding.model_name)

        # Should be identical (within floating point precision)
        assert len(embeddings1) == len(embeddings2)
        for emb1, emb2 in zip(embeddings1, embeddings2, strict=False):
            assert len(emb1) == len(emb2)
            for val1, val2 in zip(emb1, emb2, strict=False):
                assert abs(val1 - val2) < 1e-6  # Very small tolerance

    def test_embedding_persistence(self, test_case_dir):
        """Test that embeddings persist correctly across sessions."""
        # Create test documents and generate real embeddings to match dimensions
        documents = [
            Document(text="Persistent content 1"),
            Document(text="Persistent content 2"),
        ]

        # Generate real embeddings with correct dimensions
        embeddings = embed_text_nodes(documents, TEST_PARAMS.embedding.model_name)

        ids = ["persist_test_1", "persist_test_2"]
        metadatas = [
            {"text": "Persistent content 1", "source": "test1.txt"},
            {"text": "Persistent content 2", "source": "test2.txt"},
        ]

        print(f"Generated embeddings with dimensions: {len(embeddings[0])}")

        # Store embeddings
        store_embeddings(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            persist_dir=test_case_dir,
            collection_name="persistence_test",
            deduplicate=False,
        )

        # Query to verify persistence
        result = query_embeddings(
            query="persistent content",
            model_name=TEST_PARAMS.embedding.model_name,
            persist_dir=test_case_dir,
            collection_name="persistence_test",
            top_k=2,
        )

        # Should find the stored content
        result_count = len(result["all_results"])
        assert result_count == 2, f"Expected 2 results, got {result_count}. Results: {result['all_results']}"
        stored_texts = [res["text"] for res in result["all_results"]]
        assert "Persistent content 1" in stored_texts, f"Expected 'Persistent content 1' in {stored_texts}"
        assert "Persistent content 2" in stored_texts, f"Expected 'Persistent content 2' in {stored_texts}"
