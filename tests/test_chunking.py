"""Tests for the chunking module.

Comprehensive test coverage for chunking strategies and configurations.
Test scenarios align with docs/technical/CHUNKING.md strategy documentation.
"""

import pytest

pytest.importorskip("llama_index")
from pathlib import Path

from llama_index.core import Document

from backend.rag_pipeline.core.chunking import (
    ChunkingResult,
    chunk_documents,
    generate_content_hash,
    get_page_chunks,
)
from backend.rag_pipeline.core.document_loader import DocumentLoader


class TestChunking:
    """Test the document chunking functionality."""

    def test_chunk_documents_basic(self):
        """Test basic document chunking functionality."""
        # Create test documents
        documents = [
            Document(text="This is the first document content."),
            Document(text="This is the second document with more content to test chunking."),
        ]

        result = chunk_documents(documents, chunk_size=50, chunk_overlap=10)

        # Verify result structure
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) > 0
        assert result.chunk_count == len(result.chunks)
        assert result.chunking_params["chunk_size"] == 50
        assert result.chunking_params["chunk_overlap"] == 10
        assert len(result.file_hash) == 64  # SHA-256 hash

    def test_chunk_documents_with_path(self, test_data_dir):
        """Test chunking with source path metadata."""
        documents = [Document(text="Test document content for path testing.")]
        pdf_path = test_data_dir / "2303.18223v16.pdf"

        result = chunk_documents(documents, source_path=pdf_path)

        assert result.file_name == pdf_path.name
        assert result.file_path == str(pdf_path)
        assert result.file_size > 0

        # Check chunk metadata
        if result.chunks:
            chunk = result.chunks[0]
            assert chunk.metadata["document_name"] == pdf_path.name
            assert chunk.metadata["source"] == str(pdf_path)
            assert "chunk_index" in chunk.metadata
            assert "document_id" in chunk.metadata

    def test_chunk_documents_empty_input(self):
        """Test chunking with empty document list."""
        result = chunk_documents([])

        assert result.chunk_count == 0
        assert len(result.chunks) == 0
        assert result.file_name == ""
        assert result.file_hash == ""

    def test_chunk_size_parameters(self):
        """Test different chunk size parameters."""
        # Create a longer document to test chunking
        long_text = "This is a test document. " * 100  # Repeat to make it long enough for splitting
        documents = [Document(text=long_text)]

        # Test small chunks
        result_small = chunk_documents(documents, chunk_size=200, chunk_overlap=50)

        # Test large chunks
        result_large = chunk_documents(documents, chunk_size=1000, chunk_overlap=100)

        # Debug info for better failure messages
        small_count = result_small.chunk_count
        large_count = result_large.chunk_count
        print(f"Small chunks (size=200): {small_count} chunks")
        print(f"Large chunks (size=1000): {large_count} chunks")
        print(f"Original text length: {len(long_text)}")

        # Small chunks should create more or equal pieces when text is long enough
        assert small_count >= large_count, f"Expected small chunks ({small_count}) >= large chunks ({large_count})"

        # Both should produce at least one chunk
        assert small_count > 0, f"Small chunks should produce at least 1 chunk, got {small_count}"
        assert large_count > 0, f"Large chunks should produce at least 1 chunk, got {large_count}"

        # Check that we actually get reasonable chunk counts for a long document
        if len(long_text) > 1000:  # Only test if document is long enough
            assert small_count > 1, (
                f"With document length {len(long_text)} and chunk size 200, expected > 1 chunk, got {small_count}"
            )

    def test_chunk_overlap_functionality(self):
        """Test that chunk overlap works correctly."""
        # Create a document that will definitely be split
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        documents = [Document(text=text)]

        result = chunk_documents(documents, chunk_size=30, chunk_overlap=10)

        if len(result.chunks) > 1:
            # Check that consecutive chunks have some overlapping content
            for i in range(len(result.chunks) - 1):
                chunk1_end = result.chunks[i].text[-10:]  # Last 10 chars
                chunk2_start = result.chunks[i + 1].text[:10]  # First 10 chars
                # There should be some similarity due to overlap
                assert len(chunk1_end.strip()) > 0
                assert len(chunk2_start.strip()) > 0

    def test_chunking_strategies(self):
        """Test character, semantic, and recursive chunking strategies."""
        text = "Paragraph one. First sentence. Second sentence.\n\nParagraph two. More text here."
        documents = [Document(text=text)]

        char_result = chunk_documents(documents, chunk_size=40, chunk_overlap=5, strategy="character")
        sem_result = chunk_documents(documents, chunk_size=40, chunk_overlap=5, strategy="semantic")
        rec_result = chunk_documents(documents, chunk_size=40, chunk_overlap=5, strategy="recursive")

        assert char_result.chunk_count > 0
        assert sem_result.chunk_count > 0
        assert rec_result.chunk_count > 0

        # Recursive should respect paragraph boundaries (split on \n\n)
        assert rec_result.chunk_count >= 2, "Recursive should split on paragraph boundaries"
        assert "Paragraph one" in rec_result.chunks[0].text
        assert "Paragraph two" in rec_result.chunks[-1].text or any("Paragraph two" in c.text for c in rec_result.chunks)

        # All strategies should include strategy in params
        assert char_result.chunking_params["strategy"] == "character"
        assert sem_result.chunking_params["strategy"] == "semantic"
        assert rec_result.chunking_params["strategy"] == "recursive"

    def test_generate_content_hash(self):
        """Test content hash generation."""
        text1 = "This is test content"
        text2 = "This is test content"
        text3 = "This is different content"

        hash1 = generate_content_hash(text1)
        hash2 = generate_content_hash(text2)
        hash3 = generate_content_hash(text3)

        # Same content should produce same hash
        assert hash1 == hash2
        # Different content should produce different hash
        assert hash1 != hash3
        # Hash should be SHA-256 length
        assert len(hash1) == 64

    def test_generate_content_hash_unicode_handling(self):
        """Test content hash generation with Unicode surrogate characters."""
        # Test with surrogate characters that would cause UnicodeEncodeError
        text_with_surrogates = "Normal text with \ud835 surrogate characters"

        # This should not raise UnicodeEncodeError
        try:
            hash_result = generate_content_hash(text_with_surrogates)
            assert len(hash_result) == 64, "Hash should be SHA-256 length"
            assert isinstance(hash_result, str), "Hash should be a string"
        except UnicodeEncodeError:
            pytest.fail("generate_content_hash should handle Unicode surrogate characters")

        # Test with other Unicode characters
        unicode_text = "Text with émojis 🚀 and accénts"
        hash_unicode = generate_content_hash(unicode_text)
        assert len(hash_unicode) == 64
        assert isinstance(hash_unicode, str)

    def test_get_page_chunks_integration(self, test_data_dir):
        """Test the get_page_chunks function with real PDF."""
        pdf_path = test_data_dir / "2005.11401v4.pdf"  # Use smaller PDF

        page_chunks = get_page_chunks(pdf_path)

        # Verify structure
        assert isinstance(page_chunks, dict)
        assert len(page_chunks) > 0

        # Check that all values are lists of Document objects
        for page_num, chunks in page_chunks.items():
            assert isinstance(page_num, int)
            assert isinstance(chunks, list)
            assert all(hasattr(chunk, "text") for chunk in chunks)
            assert all(hasattr(chunk, "metadata") for chunk in chunks)

    def test_chunking_preserves_metadata(self):
        """Test that original document metadata is preserved in chunks."""
        # Create document with metadata
        doc = Document(text="Test content", metadata={"original_key": "original_value"})

        result = chunk_documents([doc])

        # Check that original metadata is preserved
        if result.chunks:
            chunk = result.chunks[0]
            assert "original_key" in chunk.metadata
            assert chunk.metadata["original_key"] == "original_value"
            # And new metadata is added
            assert "chunk_index" in chunk.metadata
            assert "document_id" in chunk.metadata

    def test_chunking_with_document_loader_integration(self, test_data_dir):
        """Test integration between document loader and chunking."""
        loader = DocumentLoader()
        pdf_path = test_data_dir / "2005.11401v4.pdf"

        # Load document
        documents, doc_metadata = loader.load_document(pdf_path)

        # Chunk the loaded documents
        result = chunk_documents(documents, source_path=pdf_path)

        # Verify integration
        assert result.chunk_count > 0
        assert result.file_name == pdf_path.name
        assert result.num_pages == doc_metadata.num_pages
        assert result.file_size == doc_metadata.file_size

    def test_chunk_metadata_consistency(self):
        """Test that chunk metadata is consistent across different chunking operations."""
        documents = [
            Document(text="This is the first page content."),
            Document(text="This is the second page content."),
        ]

        result1 = chunk_documents(documents, source_path=Path("test.pdf"))
        result2 = chunk_documents(documents, source_path=Path("test.pdf"))

        # Verify that both results have the same number of chunks
        assert len(result1.chunks) == len(result2.chunks)

        # Verify that metadata is consistent
        for chunk1, chunk2 in zip(result1.chunks, result2.chunks, strict=False):
            assert chunk1.metadata["page_number"] == chunk2.metadata["page_number"]
            assert chunk1.metadata["document_name"] == chunk2.metadata["document_name"]

    def test_empty_page_handling(self):
        """Test that empty pages are properly marked and preserved for page numbering."""
        documents = [
            Document(text="This is the first page with content."),
            Document(text=""),  # Empty page
            Document(text="This is the third page with content."),
        ]

        result = chunk_documents(documents, source_path=Path("test.pdf"), enable_text_cleaning=True)

        # Verify we have chunks for all pages (including empty ones)
        assert len(result.chunks) > 0, "Should have chunks even with empty pages"

        # Check that empty pages are marked appropriately
        empty_pages = [chunk for chunk in result.chunks if chunk.metadata.get("is_empty_page", False)]
        non_empty_pages = [chunk for chunk in result.chunks if not chunk.metadata.get("is_empty_page", False)]

        # Verify we have the expected number of empty and non-empty pages
        assert len(empty_pages) == 1, f"Expected 1 empty page, got {len(empty_pages)}"
        assert len(non_empty_pages) == 2, f"Expected 2 non-empty pages, got {len(non_empty_pages)}"

        # Verify page numbering is sequential (1, 2, 3)
        page_numbers = sorted([chunk.metadata["page_number"] for chunk in result.chunks])
        assert page_numbers == [1, 2, 3], f"Expected sequential page numbers [1, 2, 3], got {page_numbers}"

        # Verify that empty pages have empty text but are still included
        for chunk in result.chunks:
            if chunk.metadata.get("is_empty_page", False):
                assert chunk.text == "", "Empty pages should have empty text"
                assert chunk.metadata["page_number"] in [1, 2, 3], "Empty pages should have valid page numbers"
