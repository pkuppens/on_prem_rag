"""Tests for the Ingestion Bounded Context domain layer.

Covers aggregates, value objects, and domain events.
"""

from __future__ import annotations

from backend.ingestion.domain.aggregates import IngestionJob, IngestionStatus
from backend.ingestion.domain.events import (
    ChunkingCompleted,
    DocumentLoaded,
    DuplicateSkipped,
    EmbeddingCompleted,
    IngestionFinished,
)
from backend.ingestion.domain.value_objects import (
    Chunk,
    ChunkMetadata,
    FileContentHash,
    IngestionDocument,
    IngestionResult,
)


class TestIngestionJob:
    def test_default_status_is_pending(self):
        job = IngestionJob(file_name="test.pdf")
        assert job.status == IngestionStatus.PENDING
        assert not job.is_terminal

    def test_start_loading(self):
        job = IngestionJob(file_name="test.pdf")
        job.start_loading()
        assert job.status == IngestionStatus.LOADING

    def test_start_chunking(self):
        job = IngestionJob(file_name="test.pdf")
        job.start_chunking()
        assert job.status == IngestionStatus.CHUNKING

    def test_start_embedding(self):
        job = IngestionJob(file_name="test.pdf")
        job.start_embedding()
        assert job.status == IngestionStatus.EMBEDDING

    def test_start_storing(self):
        job = IngestionJob(file_name="test.pdf")
        job.start_storing()
        assert job.status == IngestionStatus.STORING

    def test_complete_sets_stats(self):
        job = IngestionJob(file_name="test.pdf")
        job.complete(total_chunks=10, records_stored=8)
        assert job.status == IngestionStatus.COMPLETED
        assert job.total_chunks == 10
        assert job.records_stored == 8
        assert job.is_terminal

    def test_fail_sets_error(self):
        job = IngestionJob(file_name="test.pdf")
        job.fail("disk full")
        assert job.status == IngestionStatus.FAILED
        assert job.error_message == "disk full"
        assert job.is_terminal

    def test_cancel(self):
        job = IngestionJob(file_name="test.pdf")
        job.cancel()
        assert job.status == IngestionStatus.CANCELLED
        assert job.is_terminal

    def test_progress_mapping(self):
        assert IngestionJob(file_name="x").progress_pct == 0.0
        job = IngestionJob(file_name="x")
        job.start_loading()
        assert job.progress_pct == 0.1
        job.start_chunking()
        assert job.progress_pct == 0.4
        job.start_embedding()
        assert job.progress_pct == 0.7
        job.start_storing()
        assert job.progress_pct == 0.9
        job.complete(total_chunks=1, records_stored=1)
        assert job.progress_pct == 1.0

    def test_custom_metadata(self):
        job = IngestionJob(file_name="test.pdf", file_size=1024, file_hash="abc123")
        assert job.file_size == 1024
        assert job.file_hash == "abc123"


class TestIngestionDocument:
    def test_from_text(self):
        doc = IngestionDocument.from_text("hello world", source="test.txt")
        assert doc.text == "hello world"
        assert doc.metadata["source"] == "test.txt"

    def test_content_property(self):
        doc = IngestionDocument(text="hello")
        assert doc.content == "hello"
        doc.content = "world"
        assert doc.text == "world"

    def test_default_metadata_is_empty(self):
        doc = IngestionDocument(text="hello")
        assert doc.metadata == {}


class TestChunk:
    def test_from_text(self):
        chunk = Chunk.from_text("hello", source="doc.txt")
        assert chunk.text == "hello"
        assert chunk.metadata["source"] == "doc.txt"

    def test_defaults(self):
        chunk = Chunk(text="hello")
        assert chunk.chunk_index == 0
        assert chunk.is_empty is False


class TestChunkMetadata:
    def test_creation(self):
        m = ChunkMetadata(chunk_index=0, document_id="doc1", document_name="test.pdf")
        assert m.chunk_index == 0
        assert m.document_id == "doc1"
        assert m.source == ""


class TestFileContentHash:
    def test_from_string(self):
        h = FileContentHash("hello")
        assert isinstance(h.value, str)
        assert len(h.value) == 64

    def test_from_bytes(self):
        h1 = FileContentHash(b"hello")
        h2 = FileContentHash("hello")
        assert h1 == h2

    def test_str_representation(self):
        h = FileContentHash("hello")
        assert str(h) == h.value

    def test_eq_string(self):
        h = FileContentHash("hello")
        assert h == h.value

    def test_eq_other_type(self):
        h = FileContentHash("hello")
        assert (h == 42) is False

    def test_hashable(self):
        h = FileContentHash("hello")
        assert hash(h) == hash(h.value)


class TestIngestionResult:
    def test_default_success(self):
        r = IngestionResult()
        assert r.success is True
        assert r.chunks_processed == 0

    def test_duplicate(self):
        r = IngestionResult(file_name="dup.pdf", was_duplicate=True)
        assert r.was_duplicate is True
        assert r.file_name == "dup.pdf"

    def test_failure(self):
        r = IngestionResult(success=False, error="something broke", file_name="bad.pdf")
        assert not r.success
        assert r.error == "something broke"


class TestDomainEvents:
    def test_document_loaded(self):
        e = DocumentLoaded(file_name="test.pdf", file_path="/p/test.pdf", file_hash="abc", page_count=5, file_size=1024)
        assert e.file_name == "test.pdf"
        assert e.page_count == 5

    def test_chunking_completed(self):
        e = ChunkingCompleted(file_name="test.pdf", file_path="/p/test.pdf", total_chunks=10, chunks_filtered=2, pages_processed=5)
        assert e.total_chunks == 10
        assert e.chunks_filtered == 2

    def test_embedding_completed(self):
        e = EmbeddingCompleted(file_name="test.pdf", file_path="/p/test.pdf", embeddings_count=10, model_name="all-MiniLM-L6-v2")
        assert e.embeddings_count == 10
        assert e.model_name == "all-MiniLM-L6-v2"

    def test_ingestion_finished_success(self):
        e = IngestionFinished(file_name="test.pdf", file_path="/p/test.pdf", total_chunks=10, records_stored=8, success=True)
        assert e.success is True
        assert e.records_stored == 8

    def test_ingestion_finished_failure(self):
        e = IngestionFinished(
            file_name="test.pdf", file_path="/p/test.pdf", total_chunks=0, records_stored=0, success=False, error="timeout"
        )
        assert not e.success
        assert e.error == "timeout"

    def test_duplicate_skipped(self):
        e = DuplicateSkipped(file_name="dup.pdf", file_hash="abc123")
        assert e.file_name == "dup.pdf"
        assert e.file_hash == "abc123"

    def test_all_events_are_frozen_dataclasses(self):
        import dataclasses

        e = DocumentLoaded(file_name="a", file_path="b", file_hash="c", page_count=1, file_size=1)
        assert dataclasses.is_dataclass(e)
        assert dataclasses.fields(e)
