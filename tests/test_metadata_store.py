"""Tests for metadata store."""

from tempfile import TemporaryDirectory
from pathlib import Path

from rag_pipeline.core.metadata_store import MetadataStore


def test_add_document_and_mark_obsolete() -> None:
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "meta.db"
        store = MetadataStore(db_path=str(db_path))
        doc = store.add_document("file.txt", "hash1", pages="1-2")
        assert doc.id > 0
        # adding same hash returns existing
        doc2 = store.add_document("file.txt", "hash1", pages="1-2")
        assert doc.id == doc2.id
        store.mark_obsolete(doc.id)
        with store.Session() as session:
            fetched = session.get(type(doc), doc.id)
            assert fetched.obsolete
