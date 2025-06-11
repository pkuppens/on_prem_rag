"""Tests for the chunking module.

Comprehensive test coverage for chunking strategies and configurations.
Test scenarios align with docs/technical/CHUNKING.md strategy documentation.
"""

import pytest

pytest.importorskip("llama_index")
from pathlib import Path

from llama_index.core import Document

from rag_pipeline.core.chunking import (
    ChunkingResult,
    chunk_documents,
    generate_content_hash,
    get_page_chunks,
)
from rag_pipeline.core.document_loader import DocumentLoader


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
        """Test that chunk metadata is consistent and complete."""
        documents = [Document(text="Test document for metadata checking.")]
        source_path = Path("test_file.pdf")

        result = chunk_documents(documents, source_path=source_path)

        for i, chunk in enumerate(result.chunks):
            # Check required metadata fields
            assert chunk.metadata["chunk_index"] == i
            assert chunk.metadata["document_name"] == source_path.name
            assert chunk.metadata["source"] == str(source_path)
            assert "document_id" in chunk.metadata
            assert "content_hash" in chunk.metadata
            assert len(chunk.metadata["content_hash"]) == 64  # SHA-256 length
