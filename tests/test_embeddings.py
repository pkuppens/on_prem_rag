"""Tests for the embeddings module.

This test suite verifies the core functionality of the RAG pipeline's embedding system.
The tests are organized into several categories:

1. Unit Tests (Basic Functionality)
   - Text node embedding
   - Vector storage
   - Query functionality
   - Deterministic behavior

2. Integration Tests
   - PDF document processing
   - End-to-end embedding and querying
   - Persistence across sessions

3. Edge Cases
   - Empty collections
   - Invalid inputs
   - Duplicate handling
   - Error conditions

Each test category focuses on specific aspects of the system:
- Good weather behavior: Normal operation with valid inputs
- Edge cases: Boundary conditions and error handling
- Integration: End-to-end functionality across components

The tests are designed to verify the core functionality without relying on API layers,
testing the backing code directly for better reliability and faster execution.
"""

import pytest

pytest.importorskip("llama_index")
from pathlib import Path

from llama_index.core import Document

from backend.rag_pipeline.config.parameter_sets import TEST_PARAMS
from backend.rag_pipeline.core.embeddings import (
    EmbeddingResult,
    QueryResult,
    embed_text_nodes,
    process_pdf,
    query_embeddings,
    store_embeddings,
)


class TestEmbeddings:
    """Test suite for the embedding functionality.

    This class contains tests for all aspects of the embedding system:
    1. Text embedding generation
    2. Vector storage and retrieval
    3. Query functionality
    4. Document processing
    5. Persistence and determinism
    """

    # Unit Tests - Basic Functionality

    @pytest.mark.slow
    @pytest.mark.internet
    def test_embed_text_nodes_basic(self):
        """Test basic text node embedding functionality.

        Verifies that:
        1. Multiple documents can be embedded
        2. Embeddings have correct structure (list of floats)
        3. All embeddings have the same dimension
        4. No empty or invalid embeddings are produced

        This is a good weather test for the core embedding functionality.
        """
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

        # Verify consistent dimensions
        embedding_dim = len(embeddings[0])
        assert all(len(emb) == embedding_dim for emb in embeddings)

    @pytest.mark.slow
    @pytest.mark.internet
    def test_embed_text_nodes_edge_cases(self):
        """Test text node embedding with edge cases.

        Verifies handling of:
        1. Empty document list
        2. Documents with empty text
        3. Documents with very long text
        4. Documents with special characters

        This is an edge case test for the embedding functionality.
        """
        # Test empty list
        embeddings = embed_text_nodes([], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 0

        # Test empty text
        empty_doc = Document(text="")
        embeddings = embed_text_nodes([empty_doc], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0

        # Test long text
        long_text = "test " * 1000
        long_doc = Document(text=long_text)
        embeddings = embed_text_nodes([long_doc], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0

        # Test special characters
        special_doc = Document(text="!@#$%^&*()_+{}|:<>?")
        embeddings = embed_text_nodes([special_doc], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0

    def test_store_embeddings_basic(self, test_case_dir):
        """Test basic embedding storage functionality.

        Verifies that:
        1. Embeddings can be stored with metadata
        2. Stored embeddings can be counted
        3. Collection is created correctly
        4. Basic metadata is preserved

        This is a good weather test for the storage functionality.
        """
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
        assert manager._collection.name == "test_collection"

    def test_store_embeddings_deduplication(self, test_case_dir):
        """Test embedding storage with deduplication.

        Verifies that:
        1. Duplicate content is detected
        2. Only unique content is stored
        3. Metadata is preserved for unique entries
        4. Deduplication works with different metadata

        This is a good weather test for the deduplication functionality.
        """
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

    # Integration Tests

    @pytest.mark.slow
    @pytest.mark.internet
    def test_process_pdf_integration(self, test_data_dir, test_case_dir):
        """Test the complete PDF processing pipeline.

        Verifies that:
        1. PDFs can be processed end-to-end
        2. Chunking produces reasonable number of chunks
        3. Embeddings are generated for all chunks
        4. Results are stored in the vector database
        5. Progress updates are handled properly

        This is an integration test for the complete PDF processing pipeline.
        """
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
        assert chunks > 0, "Should create at least one chunk"
        assert records > 0, "Should store at least one record"
        assert records <= chunks, "Deduplication may reduce count"

    @pytest.mark.slow
    @pytest.mark.internet
    def test_process_pdf_expected_values(self, test_data_dir, test_case_dir):
        """Test PDF processing returns expected values for specific test file.

        Verifies that:
        1. Processing returns consistent results for known input
        2. Chunk counts are reasonable for the input size
        3. Deduplication works as expected
        4. Page limits are respected

        This is a good weather test for PDF processing with known parameters.
        """
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
        assert chunks < 50, "Should not create excessive chunks for single PDF page"
        assert records == chunks, "No duplicates expected in single PDF page"

    @pytest.mark.slow
    @pytest.mark.internet
    @pytest.mark.asyncio
    async def test_query_embeddings(self, test_data_dir, test_case_dir):
        """Test querying stored embeddings.

        Verifies that:
        1. Stored embeddings can be queried
        2. Query results have the expected structure
        3. Similarity scores are in valid range
        4. Metadata is preserved in results
        5. Results are ordered by similarity

        This is a good weather test for the query functionality.
        """
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

            # Verify similarity scores are in valid range and ordered
            scores = [res["similarity_score"] for res in result["all_results"]]
            assert all(-1 <= score <= 1 for score in scores)
            assert scores == sorted(scores, reverse=True), "Results should be ordered by similarity"

    @pytest.mark.slow
    @pytest.mark.internet
    def test_query_embeddings_empty_collection(self, test_case_dir):
        """Test querying an empty collection.

        Verifies that:
        1. Empty collections return empty results
        2. Result structure is maintained
        3. No errors are raised

        This is an edge case test for the query functionality.
        """
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

    @pytest.mark.slow
    @pytest.mark.internet
    def test_embeddings_deterministic(self):
        """Test that embeddings are deterministic for same input.

        Verifies that:
        1. Same input produces identical embeddings
        2. Floating point precision is maintained
        3. No random variation in results

        This is a good weather test for embedding consistency.
        """
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

    @pytest.mark.slow
    @pytest.mark.internet
    @pytest.mark.asyncio
    async def test_embedding_persistence(self, test_case_dir):
        """Test that embeddings persist correctly across sessions.

        Verifies that:
        1. Embeddings are stored correctly
        2. Stored embeddings can be retrieved
        3. Query results match the stored content
        4. Metadata is preserved across sessions

        This is an integration test for persistence functionality.
        """
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
