"""IAuditStore port interface for audit trail persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Union

from backend.audit_trail.domain.entities import (
    CloudQueryAuditEntry,
    GuardrailEventEntry,
    PatientIsolationAuditEntry,
)

AuditEntry = Union[CloudQueryAuditEntry, GuardrailEventEntry, PatientIsolationAuditEntry]


@dataclass
class AuditQuery:
    """Query filter for retrieving audit entries.

    All fields are optional — only provided filters are applied.
    """

    start_date: datetime | None = None
    end_date: datetime | None = None
    actor_hash: str | None = None
    guardrail_type: str | None = None
    isolation_maintained: bool | None = None


class IAuditStore(ABC):
    """Port interface for audit entry persistence.

    Implementations must handle all three audit entry types:
    - CloudQueryAuditEntry
    - GuardrailEventEntry
    - PatientIsolationAuditEntry
    """

    @abstractmethod
    def store(self, entry: AuditEntry) -> None:
        """Persist an audit entry."""

    @abstractmethod
    def query(self, filters: AuditQuery) -> List[AuditEntry]:
        """Retrieve entries matching the given filters.

        Returns all entries when an empty/default AuditQuery is provided.
        """

    @abstractmethod
    def get_stats(self) -> dict:
        """Return usage statistics about stored entries.

        Returns a dict with at minimum an 'entry_count' key and
        per-type counts.
        """
