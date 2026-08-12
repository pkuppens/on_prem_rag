"""Tests for backend.ingestion.infrastructure.chunking — the production chunking path.

Covers the chunk_documents function used by IngestionService. Mirrors the scenario
coverage of tests/test_chunking.py (legacy rag_pipeline.core.chunking, retained
because backend.rag_pipeline.core.embeddings still depends on it — see #178).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("llama_index")

from backend.ingestion.domain.value_objects import Chunk, IngestionDocument
from backend.ingestion.infrastructure.chunking import chunk_documents, generate_content_hash


class TestChunkDocuments:
    """Test the production chunk_documents functionality."""

    def test_chunk_documents_basic(self):
        """Test basic document chunking functionality."""
        documents = [
            IngestionDocument(text="This is the first document content."),
            IngestionDocument(text="This is the second document with more content to test chunking."),
        ]

        chunks = chunk_documents(documents, chunk_size=50, chunk_overlap=10)

        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(len(c.content_hash) == 64 for c in chunks)  # SHA-256 hash

    def test_chunk_documents_with_source_path(self, test_data_dir):
        """Test chunking with source path metadata."""
        documents = [IngestionDocument(text="Test document content for path testing.")]
        pdf_path = test_data_dir / "2303.18223v16.pdf"

        chunks = chunk_documents(documents, source_path=pdf_path)

        assert chunks
        chunk = chunks[0]
        assert chunk.document_name == pdf_path.name
        assert chunk.source == str(pdf_path)
        assert chunk.metadata["document_name"] == pdf_path.name
        assert "chunk_index" in chunk.metadata
        assert "document_id" in chunk.metadata

    def test_chunk_documents_empty_input(self):
        """Test chunking with empty document list."""
        chunks = chunk_documents([])

        assert chunks == []

    def test_chunk_size_parameters(self):
        """Test different chunk size parameters."""
        long_text = "This is a test document. " * 100
        documents = [IngestionDocument(text=long_text)]

        small_chunks = chunk_documents(documents, chunk_size=200, chunk_overlap=50)
        large_chunks = chunk_documents(documents, chunk_size=1000, chunk_overlap=100)

        assert len(small_chunks) >= len(large_chunks)
        assert len(small_chunks) > 0
        assert len(large_chunks) > 0
        if len(long_text) > 1000:
            assert len(small_chunks) > 1

    def test_chunking_strategies(self):
        """Test character, semantic, and recursive chunking strategies."""
        text = "Paragraph one. First sentence. Second sentence.\n\nParagraph two. More text here."
        documents = [IngestionDocument(text=text)]

        char_chunks = chunk_documents(documents, chunk_size=40, chunk_overlap=5, strategy="character")
        sem_chunks = chunk_documents(documents, chunk_size=40, chunk_overlap=5, strategy="semantic")
        rec_chunks = chunk_documents(documents, chunk_size=40, chunk_overlap=5, strategy="recursive")

        assert len(char_chunks) > 0
        assert len(sem_chunks) > 0
        assert len(rec_chunks) > 0

        # Recursive should respect paragraph boundaries (split on \n\n)
        assert len(rec_chunks) >= 2, "Recursive should split on paragraph boundaries"
        assert "Paragraph one" in rec_chunks[0].text
        assert "Paragraph two" in rec_chunks[-1].text or any("Paragraph two" in c.text for c in rec_chunks)

    def test_generate_content_hash(self):
        """Test content hash generation."""
        text1 = "This is test content"
        text2 = "This is test content"
        text3 = "This is different content"

        hash1 = generate_content_hash(text1)
        hash2 = generate_content_hash(text2)
        hash3 = generate_content_hash(text3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64

    def test_generate_content_hash_unicode_handling(self):
        """Test content hash generation with Unicode surrogate characters."""
        text_with_surrogates = "Normal text with \ud835 surrogate characters"

        try:
            hash_result = generate_content_hash(text_with_surrogates)
            assert len(hash_result) == 64
            assert isinstance(hash_result, str)
        except UnicodeEncodeError:
            pytest.fail("generate_content_hash should handle Unicode surrogate characters")

        unicode_text = "Text with émojis 🚀 and accénts"
        hash_unicode = generate_content_hash(unicode_text)
        assert len(hash_unicode) == 64
        assert isinstance(hash_unicode, str)

    def test_chunking_preserves_metadata(self):
        """Test that original document metadata is preserved in chunks."""
        doc = IngestionDocument(text="Test content", metadata={"original_key": "original_value"})

        chunks = chunk_documents([doc])

        assert chunks
        chunk = chunks[0]
        assert chunk.metadata["original_key"] == "original_value"
        assert "chunk_index" in chunk.metadata
        assert "document_id" in chunk.metadata

    def test_chunking_with_document_loader_integration(self, test_data_dir):
        """Test integration between the production document loader and chunking."""
        from backend.ingestion.infrastructure.document_loader import DocumentLoader

        loader = DocumentLoader()
        pdf_path = test_data_dir / "2005.11401v4.pdf"

        documents, doc_metadata = loader.load_document(pdf_path)

        chunks = chunk_documents(documents, source_path=pdf_path)

        assert len(chunks) > 0
        assert chunks[0].document_name == pdf_path.name
        assert doc_metadata["num_pages"] == len(documents)

    def test_chunk_metadata_consistency(self):
        """Test that chunk metadata is consistent across different chunking operations."""
        documents = [
            IngestionDocument(text="This is the first page content."),
            IngestionDocument(text="This is the second page content."),
        ]

        chunks1 = chunk_documents(documents, source_path=Path("test.pdf"))
        chunks2 = chunk_documents(documents, source_path=Path("test.pdf"))

        assert len(chunks1) == len(chunks2)
        for chunk1, chunk2 in zip(chunks1, chunks2, strict=False):
            assert chunk1.page_number == chunk2.page_number
            assert chunk1.document_name == chunk2.document_name

    def test_chunk_ids_unique_across_uneven_pages(self):
        """Regression test for #207: chunk_index must not double-count position.

        A document whose pages produce different chunk counts (e.g. 7, 6, 2)
        previously produced duplicate document_id/chunk_index values across
        page boundaries (chunk_index = len(all_chunks) + i), which crashed
        ChromaDB's collection.add() with DuplicateIDError and silently
        dropped the whole document from the vector store.
        """
        documents = [
            IngestionDocument(text=". ".join(f"Sentence {i} on page one" for i in range(60))),
            IngestionDocument(text=". ".join(f"Sentence {i} on page two" for i in range(50))),
            IngestionDocument(text=". ".join(f"Sentence {i} on page three" for i in range(15))),
        ]

        chunks = chunk_documents(documents, source_path=Path("test.pdf"), chunk_size=50, chunk_overlap=5)

        document_ids = [c.document_id for c in chunks]
        assert len(document_ids) == len(set(document_ids)), f"Duplicate document_id values: {document_ids}"

        chunk_indices = [c.chunk_index for c in chunks]
        assert chunk_indices == list(range(len(chunks))), f"chunk_index must be a contiguous sequence, got {chunk_indices}"

    def test_empty_page_handling(self):
        """Test that empty pages are properly marked and preserved for page numbering."""
        documents = [
            IngestionDocument(text="This is the first page with content."),
            IngestionDocument(text=""),  # Empty page
            IngestionDocument(text="This is the third page with content."),
        ]

        chunks = chunk_documents(documents, source_path=Path("test.pdf"), enable_text_cleaning=True)

        assert len(chunks) > 0, "Should have chunks even with empty pages"

        empty_pages = [c for c in chunks if c.is_empty]
        non_empty_pages = [c for c in chunks if not c.is_empty]

        assert len(empty_pages) == 1, f"Expected 1 empty page, got {len(empty_pages)}"
        assert len(non_empty_pages) == 2, f"Expected 2 non-empty pages, got {len(non_empty_pages)}"

        page_numbers = sorted(c.page_number for c in chunks)
        assert page_numbers == [1, 2, 3], f"Expected sequential page numbers [1, 2, 3], got {page_numbers}"

        for chunk in chunks:
            if chunk.is_empty:
                assert chunk.text == "", "Empty pages should have empty text"
                assert chunk.page_number in [1, 2, 3], "Empty pages should have valid page numbers"
