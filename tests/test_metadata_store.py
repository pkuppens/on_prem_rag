import pytest

pytest.importorskip("sqlalchemy")
"""Tests for metadata store."""

from rag_pipeline.core.metadata_store import MetadataStore


class TestMetadataStore:
    """Test metadata store functionality."""

    def test_add_document_and_mark_obsolete(self, test_case_dir):
        """Test adding documents and marking them as obsolete."""
        db_path = test_case_dir / "meta.db"
        store = MetadataStore(db_path=str(db_path))

        # Test adding a document
        doc = store.add_document("file.txt", "hash1", pages="1-2")
        assert doc.id > 0

        # Test adding same hash returns existing document
        doc2 = store.add_document("file.txt", "hash1", pages="1-2")
        assert doc.id == doc2.id

        # Test marking as obsolete
        store.mark_obsolete(doc.id)
        with store.Session() as session:
            fetched = session.get(type(doc), doc.id)
            assert fetched.obsolete
