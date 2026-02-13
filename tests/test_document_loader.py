"""Tests for the document loader module."""

import pytest

pytest.importorskip("pypdf")
pytest.importorskip("llama_index")

from rag_pipeline.core.document_loader import DocumentLoader, DocumentMetadata


class TestDocumentLoader:
    """Test the DocumentLoader class functionality."""

    def test_load_pdf_document(self, test_data_dir):
        """Test loading a PDF document returns expected structure."""
        loader = DocumentLoader()
        pdf_path = test_data_dir / "2303.18223v16.pdf"

        documents, metadata = loader.load_document(pdf_path)

        # Verify documents were loaded
        assert len(documents) > 0
        assert all(hasattr(doc, "text") for doc in documents)
        assert all(hasattr(doc, "metadata") for doc in documents)

        # Verify metadata structure
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.file_path == str(pdf_path)
        assert metadata.file_type == ".pdf"
        assert metadata.file_size > 0
        assert metadata.num_pages is not None
        assert metadata.num_pages > 0
        assert metadata.processing_status == "success"
        assert metadata.error_message is None
        assert len(metadata.file_hash) == 64  # SHA-256 hash length

        # Verify file information matches expected
        assert metadata.file_size == pdf_path.stat().st_size
        assert metadata.num_pages == len(documents)

    def test_load_small_pdf_expected_pages(self, test_data_dir):
        """Test specific PDF returns expected number of pages."""
        loader = DocumentLoader()
        pdf_path = test_data_dir / "2005.11401v4.pdf"  # Smaller test file

        documents, metadata = loader.load_document(pdf_path)

        # This file should have a reasonable number of pages
        assert len(documents) > 0
        assert metadata.num_pages == len(documents)
        # Verify it's not an unreasonably large number
        assert metadata.num_pages < 100  # Reasonable upper bound

    def test_duplicate_detection(self, test_data_dir):
        """Test that duplicate file detection works."""
        loader = DocumentLoader()
        pdf_path = test_data_dir / "2303.18223v16.pdf"

        # Load the same file twice
        documents1, metadata1 = loader.load_document(pdf_path, params_key="fast")
        documents2, metadata2 = loader.load_document(pdf_path, params_key="fast")
        documents3, metadata3 = loader.load_document(pdf_path, params_key="slow")

        assert len(documents1) > 0
        assert len(documents2) == 0
        assert len(documents3) > 0  # different params_key should process

        # Metadata should be the same
        assert metadata1.file_hash == metadata2.file_hash
        assert metadata1.file_hash == metadata3.file_hash

    def test_file_validation_errors(self, test_case_dir):
        """Test file validation error handling."""
        loader = DocumentLoader()

        # Test non-existent file
        with pytest.raises(ValueError, match="File not found"):
            loader.load_document(test_case_dir / "nonexistent.pdf")

        # Test unsupported file type
        unsupported_file = test_case_dir / "test.xyz"
        unsupported_file.write_text("test content")
        with pytest.raises(ValueError, match="Unsupported file format"):
            loader.load_document(unsupported_file)

    def test_supported_file_types(self, test_case_dir):
        """Test that supported file types are handled correctly."""
        loader = DocumentLoader()

        # Test TXT file
        txt_file = test_case_dir / "test.txt"
        txt_file.write_text("This is a test document content.")

        documents, metadata = loader.load_document(txt_file)
        assert len(documents) > 0
        assert documents[0].text.strip() == "This is a test document content."
        assert metadata.file_type == ".txt"
        assert metadata.num_pages is None  # TXT files don't have pages

        # Test MD file
        md_file = test_case_dir / "test.md"
        md_file.write_text("# Test Document\n\nThis is markdown content.")

        documents, metadata = loader.load_document(md_file)
        assert len(documents) > 0
        assert "Test Document" in documents[0].text
        assert metadata.file_type == ".md"

    def test_file_size_limits(self, test_case_dir):
        """Test file size validation."""
        loader = DocumentLoader()

        # Create a file that exceeds the size limit
        large_file = test_case_dir / "large.txt"
        # Create content larger than MAX_FILE_SIZE (100MB)
        # We'll mock this by temporarily changing the limit
        original_limit = loader.MAX_FILE_SIZE
        loader.MAX_FILE_SIZE = 10  # 10 bytes

        try:
            large_file.write_text("This content is longer than 10 bytes")
            with pytest.raises(ValueError, match="File too large"):
                loader.load_document(large_file)
        finally:
            loader.MAX_FILE_SIZE = original_limit

    def test_metadata_consistency(self, test_data_dir):
        """Test that metadata is consistent across multiple loads."""
        loader1 = DocumentLoader()
        loader2 = DocumentLoader()
        pdf_path = test_data_dir / "2303.18223v16.pdf"

        # Load with different loader instances
        documents1, metadata1 = loader1.load_document(pdf_path)
        # Reset processed files to allow second load
        loader2.processed_files = set()
        documents2, metadata2 = loader2.load_document(pdf_path)

        # Metadata should be identical
        assert metadata1.file_hash == metadata2.file_hash
        assert metadata1.file_size == metadata2.file_size
        assert metadata1.num_pages == metadata2.num_pages
        assert len(documents1) == len(documents2)
