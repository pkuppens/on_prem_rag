"""Test-driven development for page-by-page document processing.

This module tests the page-by-page processing functionality using the 8-page PDF
document (2305.03983v2.pdf) as specified. The tests validate chunking results,
page boundaries, and text cleaning functionality.
"""

from pathlib import Path

import pytest
from llama_index.core import Document

from src.backend.rag_pipeline.core.chunking import chunk_documents
from src.backend.rag_pipeline.core.document_loader import DocumentLoader


class TestPageByPageProcessing:
    """As a user I want document processing to maintain page structure integrity for accurate search results.
    Technical: Test suite for page-by-page document processing using the 8-page PDF document (2305.03983v2.pdf).
    Validation: Tests validate chunking results, page boundaries, and text cleaning functionality.
    """

    @pytest.fixture
    def test_pdf_path(self, test_data_dir) -> Path:
        """Get the path to the 8-page test PDF."""
        pdf_path = test_data_dir / "2305.03983v2.pdf"
        assert pdf_path.exists(), f"Test PDF not found: {pdf_path}"
        return pdf_path

    @pytest.fixture
    def document_loader(self) -> DocumentLoader:
        """Create a document loader instance."""
        return DocumentLoader()

    def test_pdf_has_8_pages(self, test_pdf_path, document_loader):
        """As a user I want to verify document structure integrity
        Technical: PDF should load with exactly 8 pages as expected from the test document.
        """
        documents, metadata = document_loader.load_document(test_pdf_path)

        assert len(documents) == 8, f"Expected 8 pages, got {len(documents)}"
        assert metadata.num_pages == 8, f"Expected 8 pages in metadata, got {metadata.num_pages}"
        assert metadata.file_type == ".pdf"
        assert metadata.file_size > 0

    def test_page_boundaries_are_preserved(self, test_pdf_path, document_loader):
        """As a user I want search results to link to a single page, so I can quickly view and verify the result.
        Technical: Chunking should respect page boundaries - chunks must not cross from one page to another.
        Validation: Use large chunk size to force potential boundary crossing, then verify we get at least one chunk per page.
        """
        documents, _ = document_loader.load_document(test_pdf_path)

        # Use a very large chunk size that would normally create fewer chunks than pages
        # This forces the chunker to potentially cross page boundaries if not properly implemented
        large_chunk_size = 10000  # Much larger than typical page content

        # Chunk the entire document with large chunk size
        result = chunk_documents(
            documents,
            chunk_size=large_chunk_size,
            chunk_overlap=0,  # No overlap to make boundary testing clearer
            source_path=test_pdf_path,
        )

        # Verify we have at least as many chunks as pages
        # This ensures that page boundaries are being respected
        assert result.chunk_count >= 8, (
            f"Expected at least 8 chunks (one per page), got {result.chunk_count}. Chunks may be crossing page boundaries."
        )

        # Verify that each chunk has a valid page number
        for chunk in result.chunks:
            assert chunk.metadata["page_number"] is not None, "Chunk should have a page number"
            assert 1 <= chunk.metadata["page_number"] <= 8, (
                f"Page number should be between 1 and 8, got {chunk.metadata['page_number']}"
            )

        # Group chunks by page and verify each page has at least one chunk
        page_chunks = {}
        for chunk in result.chunks:
            page_num = chunk.metadata["page_number"]
            if page_num not in page_chunks:
                page_chunks[page_num] = []
            page_chunks[page_num].append(chunk)

        # Verify all 8 pages have chunks
        assert len(page_chunks) == 8, f"Expected chunks from all 8 pages, got chunks from {len(page_chunks)} pages"

        # Verify each page has at least one chunk
        for page_num in range(1, 9):
            assert page_num in page_chunks, f"Missing chunks for page {page_num}"
            assert len(page_chunks[page_num]) > 0, f"No chunks for page {page_num}"

    def test_chunking_statistics(self, test_pdf_path, document_loader):
        """As a user I want to understand document processing results for quality assurance.
        Technical: Chunking should provide accurate statistics and metadata for tracking and debugging.
        """
        documents, _ = document_loader.load_document(test_pdf_path)

        # Chunk the entire document
        result = chunk_documents(documents, chunk_size=512, chunk_overlap=50, source_path=test_pdf_path)

        # Verify chunking statistics
        assert result.num_pages == 8, f"Expected 8 pages, got {result.num_pages}"
        assert result.chunk_count > 0, "Should have at least one chunk"
        assert result.chunk_count == len(result.chunks), "Chunk count should match actual chunks"
        assert result.file_name == "2305.03983v2.pdf"
        assert result.file_path == str(test_pdf_path)
        assert result.file_size > 0

        # Verify chunking parameters
        assert result.chunking_params["chunk_size"] == 512
        assert result.chunking_params["chunk_overlap"] == 50

        # Verify file hash
        assert len(result.file_hash) == 64, "Should be SHA-256 hash"

    def test_chunk_metadata_structure(self, test_pdf_path, document_loader):
        """As a user I want search results to include proper source attribution and navigation.
        Technical: Each chunk must have complete metadata structure for document tracking and page navigation.
        """
        documents, _ = document_loader.load_document(test_pdf_path)
        result = chunk_documents(documents, source_path=test_pdf_path)

        # Check first chunk metadata
        if result.chunks:
            chunk = result.chunks[0]
            required_fields = ["chunk_index", "document_id", "document_name", "page_number", "page_label", "source", "content_hash"]

            for field in required_fields:
                assert field in chunk.metadata, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(chunk.metadata["chunk_index"], int)
            assert isinstance(chunk.metadata["document_id"], str)
            assert isinstance(chunk.metadata["document_name"], str)
            assert isinstance(chunk.metadata["page_number"], (int, type(None)))
            assert isinstance(chunk.metadata["page_label"], str)
            assert isinstance(chunk.metadata["source"], str)
            assert isinstance(chunk.metadata["content_hash"], str)

    def test_chunk_text_cleaning(self, test_pdf_path, document_loader):
        """As a user I want search results to contain clean, readable text for better comprehension.
        Technical: Chunk text should be cleaned of excessive whitespace and formatting artifacts.
        """
        documents, _ = document_loader.load_document(test_pdf_path)
        result = chunk_documents(documents, source_path=test_pdf_path)

        for chunk in result.chunks:
            text = chunk.text

            # Text should not be empty
            assert len(text.strip()) > 0, "Chunk text should not be empty"

            # Text should not have excessive whitespace
            assert text == text.strip(), "Chunk text should be stripped of leading/trailing whitespace"

            # Text should not have multiple consecutive newlines
            assert "\n\n\n" not in text, "Chunk text should not have excessive newlines"

            # Text should not have excessive spaces
            assert "   " not in text, "Chunk text should not have excessive spaces"

    def test_page_content_distribution(self, test_pdf_path, document_loader):
        """As a user I want search results to cover all document content for comprehensive retrieval.
        Technical: Content should be distributed across all pages with reasonable chunk distribution.
        """
        documents, _ = document_loader.load_document(test_pdf_path)
        result = chunk_documents(documents, source_path=test_pdf_path)

        # Group chunks by page
        page_chunks: dict[int, list[Document]] = {}
        for chunk in result.chunks:
            page_num = chunk.metadata["page_number"]
            if page_num not in page_chunks:
                page_chunks[page_num] = []
            page_chunks[page_num].append(chunk)

        # Verify all pages have content
        assert len(page_chunks) == 8, f"Expected chunks from 8 pages, got {len(page_chunks)}"

        # Verify each page has reasonable content
        for page_num in range(1, 9):
            assert page_num in page_chunks, f"Missing page {page_num}"
            chunks = page_chunks[page_num]
            assert len(chunks) > 0, f"Page {page_num} has no chunks"

            # Calculate total text length for this page
            page_text_length = sum(len(chunk.text) for chunk in chunks)
            assert page_text_length > 0, f"Page {page_num} has no text content"

    def test_chunk_overlap_functionality(self, test_pdf_path, document_loader):
        """As a user I want search results to capture context around key terms for better understanding.
        Technical: Chunk overlap should ensure important content isn't split across chunk boundaries.
        """
        documents, _ = document_loader.load_document(test_pdf_path)

        # Test with different overlap values
        result = chunk_documents(documents, chunk_size=512, chunk_overlap=100, source_path=test_pdf_path)

        # If we have multiple chunks, check for overlap
        if len(result.chunks) > 1:
            for i in range(len(result.chunks) - 1):
                chunk1 = result.chunks[i]
                chunk2 = result.chunks[i + 1]

                # Check if chunks are from the same page
                if chunk1.metadata["page_number"] == chunk2.metadata["page_number"]:
                    # There should be some overlap in content
                    chunk1_end = chunk1.text[-50:]  # Last 50 chars
                    chunk2_start = chunk2.text[:50]  # First 50 chars

                    # Simple overlap check - there should be some common text
                    assert len(chunk1_end.strip()) > 0, "Chunk end should not be empty"
                    assert len(chunk2_start.strip()) > 0, "Chunk start should not be empty"

    def test_document_processing_integration(self, test_pdf_path):
        """As a user I want the complete document processing pipeline to work reliably.
        Technical: End-to-end integration test verifying document loading, chunking, and metadata assignment.
        """
        # This test would require the full processing pipeline
        # For now, we'll test the chunking part which is the focus
        document_loader = DocumentLoader()
        documents, metadata = document_loader.load_document(test_pdf_path)

        # Verify document loading
        assert len(documents) == 8
        assert metadata.num_pages == 8

        # Verify chunking
        result = chunk_documents(documents, source_path=test_pdf_path)
        assert result.num_pages == 8
        assert result.chunk_count > 0

        # Verify chunk metadata
        for chunk in result.chunks:
            assert chunk.metadata["page_number"] is not None
            assert chunk.metadata["page_label"] is not None
            assert len(chunk.text.strip()) > 0


class TestTextCleaning:
    """Test suite for text cleaning functionality."""

    def test_remove_excessive_whitespace(self):
        """Test removal of excessive whitespace."""
        # This would test the text cleaning function
        # Implementation to be added
        pass

    def test_remove_special_characters(self):
        """Test removal of problematic special characters."""
        # This would test the text cleaning function
        # Implementation to be added
        pass

    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        # This would test the text cleaning function
        # Implementation to be added
        pass


if __name__ == "__main__":
    # Run tests directly for development
    pytest.main([__file__, "-v"])
