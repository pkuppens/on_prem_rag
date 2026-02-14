"""Tests for the embeddings module.

As a developer I want fast unit tests and integration tests for embeddings,
so I can verify storage, dedup, metadata, and pipeline logic without real models.
Technical: unit tests mock the embedding model; integration tests (slow) use real models.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("llama_index")

from llama_index.core import Document
from llama_index.core.schema import TextNode

from backend.rag_pipeline.config.parameter_sets import TEST_PARAMS
from backend.rag_pipeline.core.embeddings import (
    create_clean_metadata,
    embed_chunks,
    embed_text_nodes,
    process_document,
    process_pdf,
    query_embeddings,
    store_embeddings,
)

# --- Fast unit tests (no real embedding model required) ---


class TestCreateCleanMetadata:
    """Unit tests for create_clean_metadata — pure function, no mocking needed."""

    def test_basic_metadata(self):
        """Test clean metadata creation from a TextNode."""
        node = TextNode(text="Hello world", metadata={"page_number": 1, "page_label": "1"})
        result = create_clean_metadata(node, Path("test.pdf"), chunk_index=0)

        assert result["text"] == "Hello world"
        assert result["document_name"] == "test.pdf"
        assert result["document_id"] == "test_0"
        assert result["chunk_index"] == 0
        assert result["source"] == "test.pdf"
        assert result["page_number"] == 1

    def test_metadata_defaults(self):
        """Test that defaults are applied when metadata fields are missing."""
        node = TextNode(text="content")
        result = create_clean_metadata(node, Path("doc.txt"), chunk_index=5)

        assert result["page_number"] == "unknown"
        assert result["page_label"] == "unknown"
        assert result["content_hash"] == ""

    def test_non_serializable_metadata_excluded(self):
        """Test that non-serializable metadata values are excluded."""
        node = TextNode(text="text", metadata={"good_key": "value", "_private": "skip"})
        result = create_clean_metadata(node, Path("f.pdf"), chunk_index=0)

        assert result["good_key"] == "value"
        assert "_private" not in result

    def test_list_metadata_preserved(self):
        """Test that list metadata with basic types is preserved."""
        node = TextNode(text="text", metadata={"tags": ["a", "b"]})
        result = create_clean_metadata(node, Path("f.pdf"), chunk_index=0)
        assert result["tags"] == ["a", "b"]

    def test_dict_metadata_preserved(self):
        """Test that dict metadata with basic type values is preserved."""
        node = TextNode(text="text", metadata={"info": {"key": "val"}})
        result = create_clean_metadata(node, Path("f.pdf"), chunk_index=0)
        assert result["info"] == {"key": "val"}


class TestEmbedTextNodesMocked:
    """Unit tests for embed_text_nodes with mocked embedding model."""

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_basic_embedding(self, mock_get_model):
        """Test embedding generation with mocked model."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_model.return_value = mock_model

        nodes = [TextNode(text="Hello"), TextNode(text="World")]
        result = embed_text_nodes(nodes, "test-model")

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert mock_model.get_text_embedding.call_count == 2

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_empty_nodes_skipped(self, mock_get_model):
        """Test that nodes with empty text are skipped."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        nodes = [TextNode(text=""), TextNode(text="valid")]
        result = embed_text_nodes(nodes, "test-model")

        assert len(result) == 1
        assert mock_model.get_text_embedding.call_count == 1

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_embedding_error_continues(self, mock_get_model):
        """Test that embedding errors for one node don't stop processing."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.side_effect = [RuntimeError("fail"), [0.5]]
        mock_get_model.return_value = mock_model

        nodes = [TextNode(text="bad"), TextNode(text="good")]
        result = embed_text_nodes(nodes, "test-model")

        assert len(result) == 1
        assert result[0] == [0.5]

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_empty_input(self, mock_get_model):
        """Test embedding empty list returns empty list."""
        result = embed_text_nodes([], "test-model")
        assert result == []

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_whitespace_only_text_skipped(self, mock_get_model):
        """Test that nodes with whitespace-only text are skipped."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        nodes = [TextNode(text="   \n\t  "), TextNode(text="valid")]
        result = embed_text_nodes(nodes, "test-model")

        assert len(result) == 1


class TestQueryEmbeddingsMocked:
    """Unit tests for query_embeddings with mocked vector store and embedding model."""

    @patch("backend.rag_pipeline.core.embeddings.ChromaVectorStoreManager")
    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_query_returns_results(self, mock_get_model, mock_manager_cls, test_case_dir):
        """Test query_embeddings returns properly formatted results."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1, 0.2]
        mock_get_model.return_value = mock_model

        mock_manager = MagicMock()
        mock_manager.query.return_value = (["id1", "id2"], [0.1, 0.3])
        mock_manager._collection.get.return_value = {
            "metadatas": [
                {"document_id": "doc1", "document_name": "f.pdf", "chunk_index": 0, "page_number": 1, "page_label": "1"},
                {"document_id": "doc2", "document_name": "f.pdf", "chunk_index": 1, "page_number": 2, "page_label": "2"},
            ],
            "documents": ["First chunk text", "Second chunk text"],
        }
        mock_manager_cls.return_value = mock_manager

        result = query_embeddings("test query", "model", persist_dir=test_case_dir, collection_name="col", top_k=2)

        assert result["primary_result"] == "First chunk text"
        assert len(result["all_results"]) == 2
        assert result["all_results"][0]["similarity_score"] == pytest.approx(0.9)
        assert result["all_results"][0]["document_name"] == "f.pdf"

    @patch("backend.rag_pipeline.core.embeddings.ChromaVectorStoreManager")
    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_query_empty_results(self, mock_get_model, mock_manager_cls, test_case_dir):
        """Test query_embeddings with no results."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        mock_manager = MagicMock()
        mock_manager.query.return_value = ([], [])
        mock_manager_cls.return_value = mock_manager

        result = query_embeddings("test query", "model", persist_dir=test_case_dir, collection_name="col", top_k=2)

        assert result["primary_result"] == ""
        assert result["all_results"] == []


class TestChunkPdfMocked:
    """Unit tests for chunk_pdf with mocked document loader."""

    @patch("backend.rag_pipeline.core.embeddings.DocumentLoader")
    def test_chunk_pdf_basic(self, mock_loader_cls, tmp_path):
        """Test chunk_pdf returns a ChunkingResult."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"dummy")

        mock_loader = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.file_size = 100
        mock_metadata.file_type = ".pdf"
        mock_loader.load_document.return_value = (
            [Document(text="Page one content for chunking test.")],
            mock_metadata,
        )
        mock_loader_cls.return_value = mock_loader

        from backend.rag_pipeline.core.embeddings import chunk_pdf

        result = chunk_pdf(test_file, chunk_size=512, chunk_overlap=50)

        assert result.chunk_count > 0
        assert result.file_name == "test.pdf"


class TestProcessPdfWrapper:
    """Test that process_pdf delegates to process_document."""

    @patch("backend.rag_pipeline.core.embeddings.process_document")
    def test_process_pdf_delegates(self, mock_process_doc, tmp_path, test_case_dir):
        """Test process_pdf is a thin wrapper around process_document."""
        mock_process_doc.return_value = (10, 8)

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"dummy")

        chunks, records = process_pdf(test_file, "test-model", persist_dir=test_case_dir, collection_name="col", chunk_size=128)

        assert chunks == 10
        assert records == 8
        mock_process_doc.assert_called_once()


class TestStoreEmbeddingsUnit:
    """Additional unit tests for store_embeddings deduplication logic."""

    def test_dedup_by_content_hash(self, test_case_dir):
        """Test deduplication uses content_hash field when available."""
        ids = ["a", "b", "c"]
        embeddings = [[0.1], [0.2], [0.3]]
        metadatas = [
            {"text": "different text 1", "content_hash": "hash_x"},
            {"text": "different text 2", "content_hash": "hash_y"},
            {"text": "different text 3", "content_hash": "hash_x"},  # same hash as first
        ]

        manager = store_embeddings(ids, embeddings, metadatas, test_case_dir, "test_hash_dedup", deduplicate=True)
        assert manager._collection.count() == 2

    def test_dedup_disabled(self, test_case_dir):
        """Test that deduplicate=False stores all entries including duplicates."""
        ids = ["a", "b"]
        embeddings = [[0.1], [0.2]]
        metadatas = [{"text": "same"}, {"text": "same"}]

        manager = store_embeddings(ids, embeddings, metadatas, test_case_dir, "test_no_dedup", deduplicate=False)
        assert manager._collection.count() == 2

    def test_no_metadatas(self, test_case_dir):
        """Test storing embeddings without metadata."""
        ids = ["a", "b"]
        embeddings = [[0.1], [0.2]]

        manager = store_embeddings(ids, embeddings, None, test_case_dir, "test_no_meta", deduplicate=False)
        assert manager._collection.count() == 2

    def test_empty_embeddings(self, test_case_dir):
        """Test storing empty embeddings list."""
        manager = store_embeddings([], [], None, test_case_dir, "test_empty", deduplicate=False)
        assert manager._collection.count() == 0


class TestEmbedChunksMocked:
    """Unit tests for embed_chunks with mocked embedding model."""

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_embed_chunks_basic(self, mock_get_model, test_case_dir):
        """Test the full embed_chunks pipeline with mocked model."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_model.return_value = mock_model

        chunks = [TextNode(text="chunk one", metadata={"page_number": 1}), TextNode(text="chunk two", metadata={"page_number": 1})]
        chunking_result = MagicMock(spec=["chunks", "file_path", "file_name"])
        chunking_result.chunks = chunks
        chunking_result.file_path = str(Path(test_case_dir) / "test.pdf")
        chunking_result.file_name = "test.pdf"

        total_chunks, records_stored = embed_chunks(
            chunking_result, "test-model", persist_dir=test_case_dir, collection_name="test_embed", deduplicate=False
        )

        assert total_chunks == 2
        assert records_stored == 2

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_embed_chunks_skips_empty_pages(self, mock_get_model, test_case_dir):
        """Test that empty page markers are skipped during embedding."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        chunks = [
            TextNode(text="real content", metadata={"page_number": 1}),
            TextNode(text="", metadata={"page_number": 2, "is_empty_page": True}),
        ]
        chunking_result = MagicMock(spec=["chunks", "file_path", "file_name"])
        chunking_result.chunks = chunks
        chunking_result.file_path = str(Path(test_case_dir) / "test.pdf")

        total_chunks, records_stored = embed_chunks(
            chunking_result, "test-model", persist_dir=test_case_dir, collection_name="test_skip", deduplicate=False
        )

        assert total_chunks == 2  # total includes empty page
        assert records_stored == 1  # but only 1 stored

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    def test_embed_chunks_with_progress(self, mock_get_model, test_case_dir):
        """Test that progress callback is invoked during embed_chunks."""
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        progress_values = []

        def track_progress(value):
            progress_values.append(value)

        chunks = [TextNode(text=f"chunk {i}", metadata={"page_number": 1}) for i in range(3)]
        chunking_result = MagicMock(spec=["chunks", "file_path", "file_name"])
        chunking_result.chunks = chunks
        chunking_result.file_path = str(Path(test_case_dir) / "test.pdf")

        embed_chunks(
            chunking_result,
            "test-model",
            persist_dir=test_case_dir,
            collection_name="test_progress",
            deduplicate=False,
            progress_callback=track_progress,
        )

        assert len(progress_values) > 0
        assert progress_values[-1] == 1.0


class TestProcessDocumentMocked:
    """Unit tests for process_document with mocked dependencies."""

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    @patch("backend.rag_pipeline.core.embeddings.DocumentLoader")
    def test_process_text_document(self, mock_loader_cls, mock_get_model, test_case_dir, tmp_path):
        """Test process_document pipeline with a mocked text file."""
        # Create a real temp file so Path operations work
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is test content for processing.")

        # Mock document loader
        mock_loader = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.file_size = 100
        mock_metadata.file_type = ".txt"
        mock_loader.load_document.return_value = ([Document(text="This is test content for processing.")], mock_metadata)
        mock_loader_cls.return_value = mock_loader

        # Mock embedding model
        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_model.return_value = mock_model

        chunks, records = process_document(
            test_file,
            "test-model",
            persist_dir=test_case_dir,
            collection_name="test_process",
            chunk_size=512,
            chunk_overlap=50,
            deduplicate=True,
        )

        assert chunks > 0
        assert records > 0

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    @patch("backend.rag_pipeline.core.embeddings.DocumentLoader")
    def test_process_document_with_progress(self, mock_loader_cls, mock_get_model, test_case_dir, tmp_path):
        """Test that progress callback is invoked throughout process_document."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content for progress testing.")

        mock_loader = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.file_size = 50
        mock_metadata.file_type = ".txt"
        mock_loader.load_document.return_value = ([Document(text="Content for progress testing.")], mock_metadata)
        mock_loader_cls.return_value = mock_loader

        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        progress_values = []

        def track_progress(filename, value):
            progress_values.append(value)

        chunks, records = process_document(
            test_file,
            "test-model",
            persist_dir=test_case_dir,
            collection_name="test_progress_doc",
            deduplicate=False,
            progress_callback=track_progress,
        )

        assert progress_values[0] == 0.0
        assert progress_values[-1] == 1.0
        assert chunks > 0

    @patch("backend.rag_pipeline.core.embeddings.get_embedding_model")
    @patch("backend.rag_pipeline.core.embeddings.DocumentLoader")
    def test_process_document_max_pages(self, mock_loader_cls, mock_get_model, test_case_dir, tmp_path):
        """Test that max_pages limits processing."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"dummy")

        mock_loader = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.file_size = 100
        mock_metadata.file_type = ".pdf"
        pages = [Document(text=f"Page {i} content for testing.") for i in range(5)]
        mock_loader.load_document.return_value = (pages, mock_metadata)
        mock_loader_cls.return_value = mock_loader

        mock_model = MagicMock()
        mock_model.get_text_embedding.return_value = [0.1]
        mock_get_model.return_value = mock_model

        chunks, records = process_document(
            test_file, "test-model", persist_dir=test_case_dir, collection_name="test_maxpages", max_pages=2, deduplicate=False
        )

        assert chunks > 0
        assert records > 0


class TestEmbeddings:
    """Integration test suite for the embedding functionality (slow, requires real models)."""

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

        # Test (only) empty text in array, should be skipped and thus return an empty list
        empty_doc = Document(text="")
        embeddings = embed_text_nodes([empty_doc], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 0, "Empty document should be skipped and thus return an empty list"

        # Test long text
        long_text = "test " * 1000
        long_doc = Document(text=long_text)
        embeddings = embed_text_nodes([long_doc], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 1, "Long document should be embedded"
        assert len(embeddings[0]) > 0, "Embedding should have non-zero length"

        # Test special characters
        special_doc = Document(text="!@#$%^&*()_+{}|:<>?")
        embeddings = embed_text_nodes([special_doc], TEST_PARAMS.embedding.model_name)
        assert len(embeddings) == 1, "Document with special characters should be embedded"
        assert len(embeddings[0]) > 0, "Embedding should have non-zero length"

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
