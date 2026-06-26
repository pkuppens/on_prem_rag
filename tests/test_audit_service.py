"""Tests for Audit Trail BC application and infrastructure layers.

Covers:
- AuditService creates and stores all entry types
- InMemoryAuditStore round-trip and filtering
- WBSOReportGenerator produces correct summary
- Port interface compliance
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import UUID

import pytest

from backend.audit_trail.application.audit_service import AuditService
from backend.audit_trail.application.wbso_report_generator import WBSOReport, WBSOReportGenerator
from backend.audit_trail.domain.entities import (
    CloudQueryAuditEntry,
    GuardrailAction,
    GuardrailEventEntry,
    GuardrailType,
    PatientIsolationAuditEntry,
)
from backend.audit_trail.domain.value_objects import (
    ActorReference,
    AuditMetadata,
    ResourceReference,
)
from backend.audit_trail.infrastructure.audit_store import FileAuditStore, InMemoryAuditStore
from backend.audit_trail.ports.audit_store import AuditEntry, AuditQuery, IAuditStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def actor() -> ActorReference:
    """Return a test actor reference."""
    return ActorReference.from_user(user_id="user_42", role="gp", session_id="session_abc")


@pytest.fixture
def resource() -> ResourceReference:
    """Return a test resource reference."""
    return ResourceReference.from_patient(patient_id="patient_99")


@pytest.fixture
def metadata() -> AuditMetadata:
    """Return test audit metadata."""
    return AuditMetadata.create(
        original_query="what is diabetes",
        intent="medical_query",
        pii_categories=["name"],
        cloud_routed=True,
        latency_ms=150,
        confidence=0.95,
    )


@pytest.fixture
def in_memory_store() -> InMemoryAuditStore:
    """Return a fresh in-memory store."""
    return InMemoryAuditStore()


@pytest.fixture
def audit_service(in_memory_store: InMemoryAuditStore) -> AuditService:
    """Return an AuditService backed by an in-memory store."""
    return AuditService(store=in_memory_store)


# ---------------------------------------------------------------------------
# Port interface compliance
# ---------------------------------------------------------------------------


class TestIAuditStoreContract:
    """Verify that store implementations fulfill the IAuditStore contract."""

    def test_in_memory_store_is_instance(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to verify InMemoryAuditStore implements IAuditStore, so I can use it polymorphically.
        Technical: IAuditStore is an abstract base class.
        Validation: isinstance check against IAuditStore.
        """
        assert isinstance(in_memory_store, IAuditStore)

    def test_file_store_is_instance(self, tmp_path: Path):
        """As a developer I want to verify FileAuditStore implements IAuditStore, so I can use it polymorphically.
        Technical: FileAuditStore must inherit from IAuditStore ABC.
        Validation: isinstance check against IAuditStore.
        """
        store = FileAuditStore(file_path=tmp_path / "audit.jsonl")
        assert isinstance(store, IAuditStore)

    def test_store_accepts_all_entry_types(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want the store to accept all three audit entry types, so the interface is consistent.
        Technical: store() signature accepts AuditEntry = Union[CloudQueryAuditEntry, GuardrailEventEntry, PatientIsolationAuditEntry].
        Validation: Call store() with each type and verify no exception.
        """
        in_memory_store.store(CloudQueryAuditEntry())
        in_memory_store.store(GuardrailEventEntry())
        in_memory_store.store(PatientIsolationAuditEntry())
        stats = in_memory_store.get_stats()
        assert stats["entry_count"] == 3

    def test_query_returns_list(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want query() to return a list even when empty, so callers don't need None checks.
        Technical: Default AuditQuery returns all entries.
        Validation: Empty store returns [].
        """
        result = in_memory_store.query(AuditQuery())
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_stats_returns_dict(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want get_stats() to return a dict with at minimum entry_count, so I can monitor usage.
        Technical: The dict should be non-empty.
        Validation: Empty store returns dict with entry_count=0.
        """
        stats = in_memory_store.get_stats()
        assert isinstance(stats, dict)
        assert "entry_count" in stats
        assert stats["entry_count"] == 0


# ---------------------------------------------------------------------------
# InMemoryAuditStore round-trip
# ---------------------------------------------------------------------------


class TestInMemoryAuditStore:
    """Verify InMemoryAuditStore store, query, and stats operations."""

    def test_store_and_retrieve_cloud_query(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to store and retrieve a CloudQueryAuditEntry, so I can verify round-trip integrity.
        Technical: store() followed by query() should return the same entry.
        Validation: Compare entry_id of stored and retrieved entry.
        """
        entry = CloudQueryAuditEntry(cloud_query_text="test query", user_role="gp")
        in_memory_store.store(entry)
        results = in_memory_store.query(AuditQuery())
        assert len(results) == 1
        assert results[0].entry_id == entry.entry_id
        assert isinstance(results[0], CloudQueryAuditEntry)

    def test_store_and_retrieve_guardrail_event(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to store and retrieve a GuardrailEventEntry, so I can verify round-trip integrity.
        Technical: GuardrailEventEntry with non-default values.
        Validation: Compare action_taken and guardrail_type.
        """
        entry = GuardrailEventEntry(
            guardrail_type=GuardrailType.PII_SCREENING,
            action_taken=GuardrailAction.BLOCKED,
            reason_code="pii_detected",
        )
        in_memory_store.store(entry)
        results = in_memory_store.query(AuditQuery())
        assert len(results) == 1
        retrieved = results[0]
        assert isinstance(retrieved, GuardrailEventEntry)
        assert retrieved.guardrail_type == GuardrailType.PII_SCREENING
        assert retrieved.action_taken == GuardrailAction.BLOCKED

    def test_store_and_retrieve_isolation_check(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to store and retrieve a PatientIsolationAuditEntry, so I can verify round-trip integrity.
        Technical: PatientIsolationAuditEntry with isolation status.
        Validation: Compare isolation_maintained field.
        """
        entry = PatientIsolationAuditEntry(
            requesting_patient_hash="patient_hash_1",
            isolation_maintained=True,
        )
        in_memory_store.store(entry)
        results = in_memory_store.query(AuditQuery())
        assert len(results) == 1
        retrieved = results[0]
        assert isinstance(retrieved, PatientIsolationAuditEntry)
        assert retrieved.isolation_maintained is True

    def test_query_by_date_range(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to query entries within a date range, so I can filter by time period.
        Technical: AuditQuery.start_date and .end_date should filter correctly.
        Validation: Create entries with different timestamps and filter.
        """
        now = datetime.utcnow()
        early = CloudQueryAuditEntry(timestamp=now - timedelta(days=10))
        middle = CloudQueryAuditEntry(timestamp=now - timedelta(days=5))
        late = CloudQueryAuditEntry(timestamp=now)
        for e in [early, middle, late]:
            in_memory_store.store(e)

        # Query middle 7-day window
        filters = AuditQuery(
            start_date=now - timedelta(days=7),
            end_date=now - timedelta(days=1),
        )
        results = in_memory_store.query(filters)
        assert len(results) == 1
        assert results[0].entry_id == middle.entry_id

    def test_query_by_actor_hash(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to query entries by actor hash, so I can find all actions by a user.
        Technical: Filtering by actor_hash across entry types.
        Validation: Only entries matching the hash are returned.
        """
        entry_a = CloudQueryAuditEntry(session_hash="hash_abc")
        entry_b = CloudQueryAuditEntry(session_hash="hash_xyz")
        entry_c = GuardrailEventEntry(user_role="hash_abc")
        for e in [entry_a, entry_b, entry_c]:
            in_memory_store.store(e)

        results = in_memory_store.query(AuditQuery(actor_hash="hash_abc"))
        assert len(results) == 2
        ids = {r.entry_id for r in results}
        assert entry_a.entry_id in ids
        assert entry_c.entry_id in ids

    def test_query_by_guardrail_type(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to query guardrail events by type, so I can analyze specific guardrail categories.
        Technical: Filter with guardrail_type string matching GuardrailType.value.
        Validation: Only guardrail entries with matching type are returned.
        """
        entry_access = GuardrailEventEntry(guardrail_type=GuardrailType.ACCESS_CONTROL)
        entry_pii = GuardrailEventEntry(guardrail_type=GuardrailType.PII_SCREENING)
        in_memory_store.store(entry_access)
        in_memory_store.store(entry_pii)

        results = in_memory_store.query(AuditQuery(guardrail_type="pii"))
        assert len(results) == 1
        assert results[0].entry_id == entry_pii.entry_id

    def test_query_by_isolation_maintained(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want to query isolation checks by status, so I can find breaches.
        Technical: Filter with isolation_maintained boolean.
        Validation: Only matching PatientIsolationAuditEntry instances are returned.
        """
        passed = PatientIsolationAuditEntry(isolation_maintained=True)
        failed = PatientIsolationAuditEntry(isolation_maintained=False)
        in_memory_store.store(passed)
        in_memory_store.store(failed)

        results = in_memory_store.query(AuditQuery(isolation_maintained=False))
        assert len(results) == 1
        assert results[0].entry_id == failed.entry_id

    def test_get_stats_counts_by_type(self, in_memory_store: InMemoryAuditStore):
        """As a developer I want get_stats to show counts per entry type, so I can monitor the audit log composition.
        Technical: Stats dict includes CloudQueryAuditEntry, GuardrailEventEntry, PatientIsolationAuditEntry counts.
        Validation: store 2 cloud + 1 guardrail = correct counts.
        """
        in_memory_store.store(CloudQueryAuditEntry())
        in_memory_store.store(CloudQueryAuditEntry())
        in_memory_store.store(GuardrailEventEntry())

        stats = in_memory_store.get_stats()
        assert stats["entry_count"] == 3
        assert stats["CloudQueryAuditEntry"] == 2
        assert stats["GuardrailEventEntry"] == 1


# ---------------------------------------------------------------------------
# FileAuditStore round-trip
# ---------------------------------------------------------------------------


class TestFileAuditStore:
    """Verify FileAuditStore persistence and retrieval."""

    def test_store_and_read_back(self, tmp_path: Path):
        """As a developer I want FileAuditStore to persist entries to disk, so data survives restarts.
        Technical: Entries are serialized to JSON lines.
        Validation: Write then query — results should match.
        """
        file_path = tmp_path / "audit.jsonl"
        store = FileAuditStore(file_path=file_path)

        entry = CloudQueryAuditEntry(cloud_query_text="persistent query")
        store.store(entry)

        results = store.query(AuditQuery())
        assert len(results) == 1
        assert results[0].entry_id == entry.entry_id
        assert isinstance(results[0], CloudQueryAuditEntry)
        assert results[0].cloud_query_text == "persistent query"

    def test_file_contains_json_lines(self, tmp_path: Path):
        """As a developer I want the file format to be valid JSON lines, so I can inspect it manually.
        Technical: Each line must be valid JSON with a 'type' key.
        Validation: Read file and parse each line as JSON.
        """
        file_path = tmp_path / "audit.jsonl"
        store = FileAuditStore(file_path=file_path)

        store.store(CloudQueryAuditEntry(cloud_query_text="q1"))
        store.store(GuardrailEventEntry(reason_code="test"))

        lines = file_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        data1 = json.loads(lines[0])
        data2 = json.loads(lines[1])
        assert data1["type"] == "CloudQueryAuditEntry"
        assert data2["type"] == "GuardrailEventEntry"

    def test_read_empty_file(self, tmp_path: Path):
        """As a developer I want query on an empty file to return an empty list, so I don't get file errors.
        Technical: FileAuditStore handles missing or empty files gracefully.
        Validation: Non-existent file path returns [].
        """
        file_path = tmp_path / "nonexistent.jsonl"
        store = FileAuditStore(file_path=file_path)
        results = store.query(AuditQuery())
        assert results == []

    def test_get_stats_after_reload(self, tmp_path: Path):
        """As a developer I want stats to work across store instances, so I can monitor growth.
        Technical: Create store, add entries, create new store pointing to same file.
        Validation: get_stats returns same counts from both instances.
        """
        file_path = tmp_path / "audit.jsonl"
        store1 = FileAuditStore(file_path=file_path)
        store1.store(CloudQueryAuditEntry())
        store1.store(CloudQueryAuditEntry())
        store1.store(GuardrailEventEntry())

        store2 = FileAuditStore(file_path=file_path)
        stats = store2.get_stats()
        assert stats["entry_count"] == 3
        assert stats["CloudQueryAuditEntry"] == 2
        assert stats["GuardrailEventEntry"] == 1


# ---------------------------------------------------------------------------
# AuditService
# ---------------------------------------------------------------------------


class TestAuditService:
    """Verify AuditService creates and stores all entry types."""

    def test_log_cloud_query(
        self, audit_service: AuditService, actor: ActorReference, resource: ResourceReference, metadata: AuditMetadata
    ):
        """As a user I want to log a cloud query, so I can track what was sent to the cloud LLM.
        Technical: AuditService.log_cloud_query creates a CloudQueryAuditEntry and stores it.
        Validation: Returned entry has correct type and fields.
        """
        entry = audit_service.log_cloud_query(
            actor=actor,
            resource=resource,
            metadata=metadata,
            cloud_query_text="what is diabetes",
            cloud_provider="openai",
            response_received=True,
            latency_ms=150,
        )
        assert isinstance(entry, CloudQueryAuditEntry)
        assert entry.cloud_query_text == "what is diabetes"
        assert entry.cloud_provider == "openai"
        assert entry.user_role == "gp"
        assert entry.session_hash == actor.session_hash

        # Verify it was stored
        results = audit_service.query_entries()
        assert len(results) == 1

    def test_log_guardrail_event(self, audit_service: AuditService, actor: ActorReference, metadata: AuditMetadata):
        """As a user I want to log a guardrail event, so I can prove guardrails are active.
        Technical: AuditService.log_guardrail_event creates a GuardrailEventEntry.
        Validation: Returned entry has correct type and action.
        """
        entry = audit_service.log_guardrail_event(
            actor=actor,
            guardrail_type=GuardrailType.PII_SCREENING,
            action=GuardrailAction.BLOCKED,
            metadata=metadata,
            reason_code="pii_detected",
            confidence_score=0.98,
        )
        assert isinstance(entry, GuardrailEventEntry)
        assert entry.guardrail_type == GuardrailType.PII_SCREENING
        assert entry.action_taken == GuardrailAction.BLOCKED
        assert entry.reason_code == "pii_detected"
        assert entry.user_role == "gp"

    def test_log_isolation_check(self, audit_service: AuditService, actor: ActorReference, metadata: AuditMetadata):
        """As a user I want to log a patient isolation check, so I can prove data isolation is enforced.
        Technical: AuditService.log_isolation_check creates a PatientIsolationAuditEntry.
        Validation: Returned entry has correct patient hash and isolation status.
        """
        entry = audit_service.log_isolation_check(
            actor=actor,
            patient_id="patient_99",
            metadata=metadata,
            isolation_maintained=True,
        )
        assert isinstance(entry, PatientIsolationAuditEntry)
        # The patient ID should be hashed
        assert entry.requesting_patient_hash != "patient_99"
        assert len(entry.requesting_patient_hash) > 0
        assert entry.isolation_maintained is True

    def test_log_isolation_with_breach(self, audit_service: AuditService, actor: ActorReference, metadata: AuditMetadata):
        """As an auditor I want to detect isolation breaches, so I can verify cross-patient leakage is blocked.
        Technical: When isolation_maintained=False, mismatch_detected should be True.
        Validation: mismatch_detected reflects the breach.
        """
        entry = audit_service.log_isolation_check(
            actor=actor,
            patient_id="patient_99",
            metadata=metadata,
            isolation_maintained=False,
            blocked_count=3,
        )
        assert entry.isolation_maintained is False
        assert entry.mismatch_detected is True
        assert entry.blocked_count == 3

    def test_query_entries_with_filters(self, audit_service: AuditService, actor: ActorReference, metadata: AuditMetadata):
        """As a user I want to query entries with filters, so I can find specific audit records.
        Technical: AuditService.query_entries passes AuditQuery to the store.
        Validation: Multiple entries created, filter narrows results.
        """
        # Create two entries at different times
        audit_service.log_cloud_query(actor=actor, resource=ResourceReference.from_patient("p1"), metadata=metadata)
        # Wait briefly to ensure different timestamps
        audit_service.log_guardrail_event(
            actor=actor,
            guardrail_type=GuardrailType.ACCESS_CONTROL,
            action=GuardrailAction.ALLOWED,
            metadata=metadata,
        )

        # Query with no filters = all entries
        all_entries = audit_service.query_entries()
        assert len(all_entries) == 2

        # Query by actor_hash
        filtered = audit_service.query_entries(AuditQuery(actor_hash=actor.session_hash))
        assert len(filtered) >= 1

    def test_generate_wbso_report(
        self, audit_service: AuditService, actor: ActorReference, resource: ResourceReference, metadata: AuditMetadata
    ):
        """As a WBSO auditor I want to generate a report for a date range, so I can prove system effectiveness.
        Technical: generate_wbso_report queries entries and runs WBSOReportGenerator.
        Validation: Report has expected counts and structure.
        """
        # Create entries
        now = datetime.utcnow()
        audit_service.log_cloud_query(actor=actor, resource=resource, metadata=metadata, cloud_query_text="q1")
        audit_service.log_cloud_query(actor=actor, resource=resource, metadata=metadata, cloud_query_text="q2")
        audit_service.log_guardrail_event(
            actor=actor,
            guardrail_type=GuardrailType.PII_SCREENING,
            action=GuardrailAction.BLOCKED,
            metadata=metadata,
        )

        start = now - timedelta(days=1)
        end = now + timedelta(days=1)
        report = audit_service.generate_wbso_report(start, end)

        assert isinstance(report, WBSOReport)
        assert report.total_entries == 3
        assert report.cloud_query_count == 2
        assert report.guardrail_event_count == 1
        assert report.isolation_check_count == 0

        # Verify JSON and Markdown serialization
        json_str = report.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["summary"]["total_entries"] == 3

        md = report.to_markdown()
        assert "## Summary" in md
        assert "| Total Entries | 3 |" in md


# ---------------------------------------------------------------------------
# WBSOReportGenerator
# ---------------------------------------------------------------------------


class TestWBSOReportGenerator:
    """Verify WBSOReportGenerator produces correct reports."""

    def test_empty_entries(self):
        """As a developer I want the report to handle empty entry lists gracefully, so it doesn't crash.
        Technical: Zero entries should produce zero counts.
        Validation: All counts are 0, rates are 0 or 1 as appropriate.
        """
        now = datetime.utcnow()
        generator = WBSOReportGenerator(
            entries=[],
            start_date=now - timedelta(days=1),
            end_date=now,
        )
        report = generator.generate()
        assert report.total_entries == 0
        assert report.cloud_query_count == 0
        assert report.guardrail_event_count == 0
        assert report.isolation_check_count == 0
        assert report.guardrail_block_rate == 0.0
        assert report.isolation_success_rate == 1.0  # default when no entries

    def test_cloud_query_section(self):
        """As an auditor I want the cloud query section to show unique users and resources, so I can assess cloud usage.
        Technical: Multiple queries from same user should count as 1 unique user.
        Validation: 3 queries, 2 unique users, 1 unique resource.
        """
        now = datetime.utcnow()
        entries: List[AuditEntry] = [
            CloudQueryAuditEntry(session_hash="user_a", cloud_provider="openai"),
            CloudQueryAuditEntry(session_hash="user_a", cloud_provider="openai"),
            CloudQueryAuditEntry(session_hash="user_b", cloud_provider="openai"),
        ]
        generator = WBSOReportGenerator(entries, start_date=now - timedelta(days=1), end_date=now)
        report = generator.generate()
        assert report.cloud_query_count == 3
        assert report.unique_users_count == 2
        assert report.unique_resources_count == 1

    def test_guardrail_section(self):
        """As an auditor I want guardrail events to show counts by type and action, so I can assess guardrail activity.
        Technical: Blocked events should be counted separately from allowed.
        Validation: 2 PII blocked + 1 access allowed = correct breakdown.
        """
        now = datetime.utcnow()
        entries: List[AuditEntry] = [
            GuardrailEventEntry(guardrail_type=GuardrailType.PII_SCREENING, action_taken=GuardrailAction.BLOCKED),
            GuardrailEventEntry(guardrail_type=GuardrailType.PII_SCREENING, action_taken=GuardrailAction.BLOCKED),
            GuardrailEventEntry(guardrail_type=GuardrailType.ACCESS_CONTROL, action_taken=GuardrailAction.ALLOWED),
        ]
        generator = WBSOReportGenerator(entries, start_date=now - timedelta(days=1), end_date=now)
        report = generator.generate()
        assert report.guardrail_event_count == 3
        assert report.guardrail_by_type["pii"] == 2
        assert report.guardrail_by_type["access"] == 1
        assert report.guardrail_by_action["blocked"] == 2
        assert report.guardrail_by_action["allowed"] == 1
        assert report.guardrail_block_rate == pytest.approx(2 / 3)

    def test_isolation_section(self):
        """As an auditor I want isolation checks to show success rate per patient, so I can verify data isolation.
        Technical: Checks with isolation_maintained=True count as success.
        Validation: 2 passed + 1 failed = 66.7% success rate.
        """
        now = datetime.utcnow()
        entries: List[AuditEntry] = [
            PatientIsolationAuditEntry(requesting_patient_hash="patient_a", isolation_maintained=True),
            PatientIsolationAuditEntry(requesting_patient_hash="patient_a", isolation_maintained=True),
            PatientIsolationAuditEntry(requesting_patient_hash="patient_b", isolation_maintained=False),
        ]
        generator = WBSOReportGenerator(entries, start_date=now - timedelta(days=1), end_date=now)
        report = generator.generate()
        assert report.isolation_check_count == 3
        assert report.isolation_success_count == 2
        assert report.isolation_success_rate == pytest.approx(2 / 3)
        assert report.isolation_by_patient["patient_a"] == 2
        assert report.isolation_by_patient["patient_b"] == 1

    def test_report_to_json(self):
        """As a developer I want the report to serialize to valid JSON, so it can be consumed by other tools.
        Technical: to_json() returns parseable JSON string.
        Validation: JSON has expected top-level keys.
        """
        now = datetime.utcnow()
        entries: List[AuditEntry] = [
            CloudQueryAuditEntry(session_hash="u1", cloud_provider="openai"),
        ]
        generator = WBSOReportGenerator(entries, start_date=now - timedelta(days=1), end_date=now)
        report = generator.generate()
        parsed = json.loads(report.to_json())
        assert "summary" in parsed
        assert "report_period" in parsed
        assert "cloud_queries" in parsed
        assert "guardrail_events" in parsed
        assert "patient_isolation" in parsed

    def test_report_to_markdown(self):
        """As an auditor I want the report as readable Markdown, so I can include it in WBSO documentation.
        Technical: to_markdown() returns a formatted Markdown string.
        Validation: Contains expected section headers and data.
        """
        now = datetime.utcnow()
        entries: List[AuditEntry] = [
            CloudQueryAuditEntry(session_hash="u1", cloud_provider="openai"),
            GuardrailEventEntry(guardrail_type=GuardrailType.PII_SCREENING, action_taken=GuardrailAction.BLOCKED),
            PatientIsolationAuditEntry(requesting_patient_hash="p1", isolation_maintained=True),
        ]
        generator = WBSOReportGenerator(entries, start_date=now - timedelta(days=1), end_date=now)
        report = generator.generate()
        md = report.to_markdown()
        assert "# WBSO Audit Report" in md
        assert "## Summary" in md
        assert "## Cloud Query Details" in md
        assert "## Guardrail Events" in md
        assert "## Patient Isolation Checks" in md
        assert "| Total Entries | 3 |" in md


# ---------------------------------------------------------------------------
# Integration: AuditService + FileAuditStore
# ---------------------------------------------------------------------------


class TestAuditServiceWithFileStore:
    """Verify AuditService works end-to-end with FileAuditStore."""

    def test_file_store_integration(
        self, tmp_path: Path, actor: ActorReference, resource: ResourceReference, metadata: AuditMetadata
    ):
        """As a developer I want AuditService to work with FileAuditStore, so it can be used in production.
        Technical: AuditService accepts any IAuditStore implementation.
        Validation: Create entries, then query from a fresh store instance pointing to the same file.
        """
        file_path = tmp_path / "audit.jsonl"
        store = FileAuditStore(file_path=file_path)
        service = AuditService(store=store)

        service.log_cloud_query(actor=actor, resource=resource, metadata=metadata, cloud_query_text="test")
        service.log_guardrail_event(
            actor=actor,
            guardrail_type=GuardrailType.ACCESS_CONTROL,
            action=GuardrailAction.ALLOWED,
            metadata=metadata,
        )

        # Create new store from same file — should see persisted entries
        store2 = FileAuditStore(file_path=file_path)
        results = store2.query(AuditQuery())
        assert len(results) == 2
        types = [type(e).__name__ for e in results]
        assert "CloudQueryAuditEntry" in types
        assert "GuardrailEventEntry" in types
