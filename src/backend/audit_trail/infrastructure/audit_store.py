"""Concrete audit store implementations.

Provides two implementations of IAuditStore:
- InMemoryAuditStore: list-based, suitable for testing
- FileAuditStore: JSON-lines file, suitable for production
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import UUID

from backend.audit_trail.domain.entities import (
    CloudQueryAuditEntry,
    GuardrailAction,
    GuardrailEventEntry,
    GuardrailType,
    PatientIsolationAuditEntry,
)
from backend.audit_trail.ports.audit_store import AuditEntry, AuditQuery, IAuditStore


class InMemoryAuditStore(IAuditStore):
    """In-memory implementation of IAuditStore for testing."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def store(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def query(self, filters: AuditQuery) -> List[AuditEntry]:
        result: List[AuditEntry] = list(self._entries)
        if filters.start_date is not None:
            result = [e for e in result if e.timestamp >= filters.start_date]
        if filters.end_date is not None:
            result = [e for e in result if e.timestamp <= filters.end_date]
        if filters.actor_hash is not None:
            result = [e for e in result if self._matches_actor(e, filters.actor_hash)]
        if filters.guardrail_type is not None:
            result = [e for e in result if self._matches_guardrail_type(e, filters.guardrail_type)]
        if filters.isolation_maintained is not None:
            result = [e for e in result if self._matches_isolation(e, filters.isolation_maintained)]
        return result

    def get_stats(self) -> Dict[str, int]:
        counts: Dict[str, int] = Counter(type(e).__name__ for e in self._entries)
        counts["entry_count"] = len(self._entries)
        return dict(counts)

    @staticmethod
    def _matches_actor(entry: AuditEntry, actor_hash: str) -> bool:
        if isinstance(entry, CloudQueryAuditEntry):
            return entry.session_hash == actor_hash
        if isinstance(entry, GuardrailEventEntry):
            return entry.user_role == actor_hash
        if isinstance(entry, PatientIsolationAuditEntry):
            return entry.requesting_patient_hash == actor_hash
        return False

    @staticmethod
    def _matches_guardrail_type(entry: AuditEntry, guardrail_type: str) -> bool:
        if isinstance(entry, GuardrailEventEntry):
            return entry.guardrail_type.value == guardrail_type
        return False

    @staticmethod
    def _matches_isolation(entry: AuditEntry, maintained: bool) -> bool:
        if isinstance(entry, PatientIsolationAuditEntry):
            return entry.isolation_maintained == maintained
        return False


class FileAuditStore(IAuditStore):
    """File-based implementation of IAuditStore using JSON lines format.

    Each line in the file is a JSON object representing one audit entry.
    The file is append-only for new entries.
    """

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def store(self, entry: AuditEntry) -> None:
        data = _entry_to_dict(entry)
        line = json.dumps(data, default=str, sort_keys=False) + "\n"
        with open(self._file_path, "a", encoding="utf-8") as f:
            f.write(line)

    def query(self, filters: AuditQuery) -> List[AuditEntry]:
        entries = self._read_all()
        temp_store = InMemoryAuditStore()
        temp_store._entries = entries
        return temp_store.query(filters)

    def get_stats(self) -> Dict[str, int]:
        entries = self._read_all()
        temp_store = InMemoryAuditStore()
        temp_store._entries = entries
        return temp_store.get_stats()

    def _read_all(self) -> List[AuditEntry]:
        if not self._file_path.exists():
            return []
        entries: List[AuditEntry] = []
        with open(self._file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(_dict_to_entry(data))
        return entries


def _entry_to_dict(entry: AuditEntry) -> dict:
    """Serialize an audit entry to a dictionary for JSON storage."""
    base = {
        "type": type(entry).__name__,
        "entry_id": str(entry.entry_id),
        "timestamp": entry.timestamp.isoformat() if isinstance(entry.timestamp, datetime) else str(entry.timestamp),
    }
    if isinstance(entry, CloudQueryAuditEntry):
        base.update(
            {
                "cloud_query_text": entry.cloud_query_text,
                "original_query_hash": entry.original_query_hash,
                "pii_categories_detected": entry.pii_categories_detected,
                "pii_count": entry.pii_count,
                "transformations_applied": entry.transformations_applied,
                "user_role": entry.user_role,
                "session_hash": entry.session_hash,
                "cloud_provider": entry.cloud_provider,
                "response_received": entry.response_received,
                "latency_ms": entry.latency_ms,
            }
        )
    elif isinstance(entry, GuardrailEventEntry):
        base.update(
            {
                "guardrail_type": entry.guardrail_type.value,
                "action_taken": entry.action_taken.value,
                "reason_code": entry.reason_code,
                "query_hash": entry.query_hash,
                "user_role": entry.user_role,
                "processing_time_ms": entry.processing_time_ms,
                "confidence_score": entry.confidence_score,
            }
        )
    elif isinstance(entry, PatientIsolationAuditEntry):
        base.update(
            {
                "requesting_patient_hash": entry.requesting_patient_hash,
                "requested_scope_hashes": entry.requested_scope_hashes,
                "response_scope_hashes": entry.response_scope_hashes,
                "isolation_maintained": entry.isolation_maintained,
                "mismatch_detected": entry.mismatch_detected,
                "blocked_count": entry.blocked_count,
            }
        )
    return base


def _dict_to_entry(data: dict) -> AuditEntry:
    """Deserialize a dictionary back to an audit entry."""
    entry_type = data.get("type", "")
    timestamp_raw = data.get("timestamp", "")
    timestamp = datetime.fromisoformat(timestamp_raw) if isinstance(timestamp_raw, str) else datetime.utcnow()
    entry_id_raw = data.get("entry_id", "")
    entry_id = UUID(entry_id_raw) if isinstance(entry_id_raw, str) else None

    if entry_type == "CloudQueryAuditEntry":
        return CloudQueryAuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            cloud_query_text=data.get("cloud_query_text", ""),
            original_query_hash=data.get("original_query_hash", ""),
            pii_categories_detected=data.get("pii_categories_detected", []),
            pii_count=data.get("pii_count", 0),
            transformations_applied=data.get("transformations_applied", []),
            user_role=data.get("user_role", ""),
            session_hash=data.get("session_hash", ""),
            cloud_provider=data.get("cloud_provider", ""),
            response_received=data.get("response_received", False),
            latency_ms=data.get("latency_ms", 0),
        )
    if entry_type == "GuardrailEventEntry":
        return GuardrailEventEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            guardrail_type=GuardrailType(data.get("guardrail_type", "access")),
            action_taken=GuardrailAction(data.get("action_taken", "allowed")),
            reason_code=data.get("reason_code", ""),
            query_hash=data.get("query_hash", ""),
            user_role=data.get("user_role", ""),
            processing_time_ms=data.get("processing_time_ms", 0),
            confidence_score=data.get("confidence_score", 1.0),
        )
    if entry_type == "PatientIsolationAuditEntry":
        return PatientIsolationAuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            requesting_patient_hash=data.get("requesting_patient_hash", ""),
            requested_scope_hashes=data.get("requested_scope_hashes", []),
            response_scope_hashes=data.get("response_scope_hashes", []),
            isolation_maintained=data.get("isolation_maintained", True),
            mismatch_detected=data.get("mismatch_detected", False),
            blocked_count=data.get("blocked_count", 0),
        )
    raise ValueError(f"Unknown audit entry type: {entry_type}")
