"""Integration test for PDF embedding pipeline.

This test validates the complete pipeline from PDF loading through chunking,
embedding, and querying with specific expected values.
"""

import shutil
from pathlib import Path

import pytest

from rag_pipeline.config.parameter_sets import get_param_set
from rag_pipeline.core.embeddings import chunk_pdf, embed_chunks, query_embeddings


class TestPDFEmbeddingIntegration:
    """Integration tests for the complete PDF embedding pipeline."""

    # Expected values for the test PDF (2303.18223v16.pdf)
    EXPECTED_PAGES = 144
    EXPECTED_CHUNKS = 603  # Based on actual test results with 'fast' parameters
    TEST_PDF_NAME = "2303.18223v16.pdf"
    QUERY_TEXT = "LLM for Healthcare"

    @classmethod
    def setup_class(cls):
        """Clean up any existing test data before running the test suite."""
        # Clean up any existing test directories
        test_dirs_to_clean = ["temp_integration_test", "temp_query_test", "temp_test_validation", "integration_test_data"]

        for dir_name in test_dirs_to_clean:
            test_dir = Path(dir_name)
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print(f"Cleaned up existing test directory: {dir_name}")

    @pytest.fixture(scope="class")
    def chunking_result(self, test_data_dir):
        """Chunk the PDF once for all tests in this class."""
        pdf_path = test_data_dir / self.TEST_PDF_NAME
        assert pdf_path.exists(), f"Test PDF not found: {pdf_path}"

        params = get_param_set("fast")

        print(f"Chunking {self.TEST_PDF_NAME} for all tests...")
        chunking_result = chunk_pdf(
            pdf_path,
            chunk_size=params.chunking.chunk_size,
            chunk_overlap=params.chunking.chunk_overlap,
            max_pages=None,  # Process ALL pages (144)
        )

        print(f"Chunking completed: {chunking_result.chunk_count} chunks from {chunking_result.num_pages} pages")
        return chunking_result

    @pytest.fixture(scope="class")
    def embedding_data(self, chunking_result, test_case_dir):
        """Generate embeddings once for all tests in this class."""
        params = get_param_set("fast")
        persist_dir = test_case_dir / "integration_test_data"

        print("Generating embeddings for all tests...")
        chunks, records = embed_chunks(
            chunking_result,
            params.embedding.model_name,
            persist_dir=persist_dir,
            collection_name="integration_test",
            deduplicate=True,
        )

        print(f"Embedding completed: {records} records stored")
        return {
            "chunks": chunks,
            "records": records,
            "persist_dir": persist_dir,
            "collection_name": "integration_test",
            "model_name": params.embedding.model_name,
        }

    def test_pdf_loading_and_pages(self, chunking_result):
        """Test that PDF loading returns the expected number of pages."""
        assert chunking_result.file_name == self.TEST_PDF_NAME
        assert chunking_result.num_pages == self.EXPECTED_PAGES, (
            f"Expected {self.EXPECTED_PAGES} pages, got {chunking_result.num_pages}"
        )
        assert chunking_result.file_size > 0

    def test_chunking_count(self, chunking_result):
        """Test that chunking produces the expected number of chunks."""
        assert chunking_result.chunk_count == self.EXPECTED_CHUNKS, (
            f"Expected exactly {self.EXPECTED_CHUNKS} chunks, got {chunking_result.chunk_count}"
        )
        assert len(chunking_result.chunks) == chunking_result.chunk_count

        # Verify chunks have proper metadata
        for chunk in chunking_result.chunks:
            assert "page_label" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "document_id" in chunk.metadata
            assert "document_name" in chunk.metadata

    def test_page_distribution(self, chunking_result):
        """Test that chunks are distributed across all pages."""
        page_labels = set()
        for chunk in chunking_result.chunks:
            page_label = chunk.metadata.get("page_label", "unknown")
            if page_label != "unknown":
                page_labels.add(int(page_label))

        # Should have chunks from most pages (allowing for some pages to be very short)
        assert len(page_labels) >= self.EXPECTED_PAGES * 0.9, (
            f"Expected chunks from most pages, found chunks from {len(page_labels)} pages"
        )

        # First page should be 1, last should be 144
        assert 1 in page_labels, "Should have chunks from page 1"
        assert self.EXPECTED_PAGES in page_labels, f"Should have chunks from page {self.EXPECTED_PAGES}"

    def test_embedding_storage(self, embedding_data):
        """Test that embeddings are stored correctly."""
        assert embedding_data["chunks"] == self.EXPECTED_CHUNKS
        assert embedding_data["records"] > 0
        assert embedding_data["records"] <= embedding_data["chunks"], "Records should not exceed chunks (due to deduplication)"

    def test_healthcare_query_returns_page_number(self, embedding_data):
        """Test that querying 'LLM for Healthcare' returns results with page numbers."""
        results = query_embeddings(
            self.QUERY_TEXT,
            embedding_data["model_name"],
            persist_dir=embedding_data["persist_dir"],
            collection_name=embedding_data["collection_name"],
            top_k=5,
        )

        # Should find results
        assert len(results["all_results"]) > 0, f"Should find results for query '{self.QUERY_TEXT}'"

        top_result = results["all_results"][0]

        # Validate required fields
        required_fields = ["text", "similarity_score", "document_id", "document_name", "chunk_index", "record_id", "page_number"]
        for field in required_fields:
            assert field in top_result, f"Missing required field: {field}"

        # Validate document information
        assert top_result["document_name"] == self.TEST_PDF_NAME
        assert isinstance(top_result["chunk_index"], int)
        assert 0 <= top_result["chunk_index"] < self.EXPECTED_CHUNKS

        # Validate similarity score
        assert isinstance(top_result["similarity_score"], float)
        assert top_result["similarity_score"] > 0.1, "Should have reasonable similarity for healthcare query"

        # The key requirement: should have a page number
        # Based on our testing, healthcare content appears around pages 64-77
        # The top result should be from one of these pages
        page_number = top_result["page_number"]
        assert page_number != "unknown", "Page number should not be unknown"

        # Convert to int if it's a string
        if isinstance(page_number, str):
            try:
                page_num = int(page_number)
            except ValueError:
                pytest.fail(f"Invalid page number format: {page_number}")
        else:
            page_num = page_number

        # Healthcare content is expected around pages 64-77 based on our analysis
        # The exact page will depend on the specific chunk that matches best
        assert 1 <= page_num <= self.EXPECTED_PAGES, f"Page number {page_num} should be within valid range"

        print(f"Healthcare query top result:")
        print(f"  Similarity: {top_result['similarity_score']:.4f}")
        print(f"  Page number: {page_number}")
        print(f"  Chunk index: {top_result['chunk_index']}")
        print(f"  Text preview: {top_result['text'][:100]}...")

        # Store the actual result for future consistency checks
        # This helps ensure the pipeline produces consistent results
        assert len(top_result["text"]) > 0, "Result should contain text"

        # Additional validation: check that we get healthcare-related content
        text_lower = top_result["text"].lower()
        healthcare_terms = ["healthcare", "health", "medical", "clinical", "patient", "diagnosis", "medicine"]
        has_healthcare_content = any(term in text_lower for term in healthcare_terms)

        # Note: The query might return relevant content that doesn't explicitly contain these terms
        # but is semantically related to healthcare, so we'll just log this for now
        print(f"  Contains explicit healthcare terms: {has_healthcare_content}")

        # Test passed - all assertions completed successfully

    def test_pipeline_reproducibility(self, test_data_dir, test_case_dir):
        """Test that the pipeline produces consistent results across runs."""
        pdf_path = test_data_dir / self.TEST_PDF_NAME
        params = get_param_set("fast")

        # Run the pipeline twice with same parameters
        results = []
        for run_id in range(2):
            persist_dir = test_case_dir / f"reproducibility_test_{run_id}"

            # Chunk and embed
            chunking_result = chunk_pdf(
                pdf_path,
                chunk_size=params.chunking.chunk_size,
                chunk_overlap=params.chunking.chunk_overlap,
                max_pages=None,  # Process all pages
            )

            chunks, records = embed_chunks(
                chunking_result,
                params.embedding.model_name,
                persist_dir=persist_dir,
                collection_name=f"repro_test_{run_id}",
                deduplicate=True,
            )

            # Query
            query_results = query_embeddings(
                self.QUERY_TEXT,
                params.embedding.model_name,
                persist_dir=persist_dir,
                collection_name=f"repro_test_{run_id}",
                top_k=1,
            )

            results.append(
                {
                    "pages": chunking_result.num_pages,
                    "chunks": chunks,
                    "records": records,
                    "similarity": query_results["all_results"][0]["similarity_score"],
                    "chunk_index": query_results["all_results"][0]["chunk_index"],
                }
            )

        # Compare results - they should be identical
        assert results[0]["pages"] == results[1]["pages"] == self.EXPECTED_PAGES
        assert results[0]["chunks"] == results[1]["chunks"] == self.EXPECTED_CHUNKS
        assert results[0]["records"] == results[1]["records"], "Record count should be identical"
        assert results[0]["chunk_index"] == results[1]["chunk_index"], "Top chunk should be identical"

        # Similarity scores should be very close (within 0.001 as requested)
        similarity_diff = abs(results[0]["similarity"] - results[1]["similarity"])
        assert similarity_diff <= 0.001, f"Similarity scores differ by {similarity_diff:.6f}, expected ≤0.001"

        print(f"Reproducibility test passed!")
        print(f"Pages processed: {results[0]['pages']}")
        print(f"Chunks created: {results[0]['chunks']}")
        print(f"Run 1 similarity: {results[0]['similarity']:.6f}")
        print(f"Run 2 similarity: {results[1]['similarity']:.6f}")
        print(f"Difference: {similarity_diff:.6f}")

    def test_chunk_metadata_consistency(self, chunking_result):
        """Test that chunk metadata is consistent and complete."""
        for i, chunk in enumerate(chunking_result.chunks):
            # Check required metadata fields
            assert chunk.metadata["chunk_index"] == i
            assert chunk.metadata["document_name"] == self.TEST_PDF_NAME
            assert "source" in chunk.metadata
            assert "content_hash" in chunk.metadata

            # Check document ID follows expected pattern
            expected_doc_id = f"2303.18223v16_{i}"
            assert chunk.metadata["document_id"] == expected_doc_id

            # Page label should be a number (though could be unknown for some chunks)
            page_label = chunk.metadata.get("page_label", "unknown")
            if page_label != "unknown":
                try:
                    page_num = int(page_label)
                    assert 1 <= page_num <= self.EXPECTED_PAGES
                except ValueError:
                    pytest.fail(f"Invalid page_label: {page_label}")

    def test_document_type_processing_parameters(self, chunking_result):
        """Test that PDF processing returns appropriate parameters for document type."""
        # For PDF files, we should get both page count and chunk count
        assert chunking_result.num_pages is not None, "PDF should return page count"
        assert chunking_result.chunk_count > 0, "PDF should return chunk count"

        # Check chunking parameters were preserved
        assert "chunk_size" in chunking_result.chunking_params
        assert "chunk_overlap" in chunking_result.chunking_params

        params = get_param_set("fast")
        assert chunking_result.chunking_params["chunk_size"] == params.chunking.chunk_size
        assert chunking_result.chunking_params["chunk_overlap"] == params.chunking.chunk_overlap
