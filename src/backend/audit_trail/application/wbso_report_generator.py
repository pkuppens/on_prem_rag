"""WBSOReportGenerator — generates WBSO evidence reports from audit entries.

Produces structured reports suitable for WBSO (Research & Development)
documentation, proving that the guardrail and privacy systems are active.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from typing import Dict, List

from backend.audit_trail.domain.entities import (
    CloudQueryAuditEntry,
    GuardrailAction,
    GuardrailEventEntry,
    PatientIsolationAuditEntry,
)
from backend.audit_trail.ports.audit_store import AuditEntry


class WBSOReport:
    """Structured WBSO evidence report.

    Contains grouped statistics and metadata about audit entries
    in a given date range, formatted for WBSO documentation.
    """

    def __init__(
        self,
        total_entries: int,
        cloud_query_count: int,
        guardrail_event_count: int,
        isolation_check_count: int,
        unique_users_count: int,
        unique_resources_count: int,
        guardrail_by_type: Dict[str, int],
        guardrail_by_action: Dict[str, int],
        guardrail_block_rate: float,
        guardrail_warning_rate: float,
        isolation_by_patient: Dict[str, int],
        isolation_success_count: int,
        isolation_success_rate: float,
        start_date: date,
        end_date: date,
    ) -> None:
        self.total_entries = total_entries
        self.cloud_query_count = cloud_query_count
        self.guardrail_event_count = guardrail_event_count
        self.isolation_check_count = isolation_check_count
        self.unique_users_count = unique_users_count
        self.unique_resources_count = unique_resources_count
        self.guardrail_by_type = guardrail_by_type
        self.guardrail_by_action = guardrail_by_action
        self.guardrail_block_rate = guardrail_block_rate
        self.guardrail_warning_rate = guardrail_warning_rate
        self.isolation_by_patient = isolation_by_patient
        self.isolation_success_count = isolation_success_count
        self.isolation_success_rate = isolation_success_rate
        self.start_date = start_date
        self.end_date = end_date

    def to_json(self) -> str:
        """Return the report as a JSON string."""
        return json.dumps(self._to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        """Return the report as a Markdown string."""
        lines: List[str] = []
        lines.append("# WBSO Audit Report")
        lines.append("")
        lines.append(f"**Period:** {self.start_date} to {self.end_date}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Entries | {self.total_entries} |")
        lines.append(f"| Cloud Queries | {self.cloud_query_count} |")
        lines.append(f"| Guardrail Events | {self.guardrail_event_count} |")
        lines.append(f"| Isolation Checks | {self.isolation_check_count} |")
        lines.append(f"| Unique Users | {self.unique_users_count} |")
        lines.append(f"| Unique Resources | {self.unique_resources_count} |")
        lines.append("")
        lines.append("## Cloud Query Details")
        lines.append("")
        lines.append(f"- **Total Cloud Queries:** {self.cloud_query_count}")
        lines.append(f"- **Unique Users:** {self.unique_users_count}")
        lines.append(f"- **Unique Resources:** {self.unique_resources_count}")
        lines.append("")
        lines.append("## Guardrail Events")
        lines.append("")
        lines.append("### By Guardrail Type")
        lines.append("")
        for gt, count in sorted(self.guardrail_by_type.items()):
            lines.append(f"- **{gt}:** {count}")
        lines.append("")
        lines.append("### By Action Taken")
        lines.append("")
        for action, count in sorted(self.guardrail_by_action.items()):
            lines.append(f"- **{action}:** {count}")
        lines.append("")
        lines.append(f"### Effectiveness")
        lines.append("")
        lines.append(f"- **Block Rate:** {self.guardrail_block_rate:.1%}")
        lines.append(f"- **Warning Rate:** {self.guardrail_warning_rate:.1%}")
        lines.append("")
        lines.append("## Patient Isolation Checks")
        lines.append("")
        lines.append(f"- **Total Checks:** {self.isolation_check_count}")
        lines.append(f"- **Isolation Maintained:** {self.isolation_success_count}")
        lines.append(f"- **Success Rate:** {self.isolation_success_rate:.1%}")
        lines.append("")
        lines.append("### By Patient")
        lines.append("")
        if self.isolation_by_patient:
            for patient_hash, count in sorted(self.isolation_by_patient.items()):
                lines.append(f"- `{patient_hash}`: {count} checks")
        else:
            lines.append("No isolation checks recorded.")
        return "\n".join(lines)

    def _to_dict(self) -> dict:
        return {
            "report_period": {
                "start": str(self.start_date),
                "end": str(self.end_date),
            },
            "summary": {
                "total_entries": self.total_entries,
                "cloud_queries": self.cloud_query_count,
                "guardrail_events": self.guardrail_event_count,
                "isolation_checks": self.isolation_check_count,
                "unique_users": self.unique_users_count,
                "unique_resources": self.unique_resources_count,
            },
            "cloud_queries": {
                "count": self.cloud_query_count,
                "unique_users": self.unique_users_count,
                "unique_resources": self.unique_resources_count,
            },
            "guardrail_events": {
                "count": self.guardrail_event_count,
                "by_type": self.guardrail_by_type,
                "by_action": self.guardrail_by_action,
                "block_rate": self.guardrail_block_rate,
                "warning_rate": self.guardrail_warning_rate,
            },
            "patient_isolation": {
                "count": self.isolation_check_count,
                "isolation_maintained": self.isolation_success_count,
                "success_rate": self.isolation_success_rate,
                "by_patient": self.isolation_by_patient,
            },
        }


class WBSOReportGenerator:
    """Generates WBSO evidence reports from audit entry lists.

    Takes a list of AuditEntry objects (from a date range),
    groups and analyzes them by type, and produces a WBSOReport.
    """

    def __init__(
        self,
        entries: List[AuditEntry],
        start_date: date | datetime | None = None,
        end_date: date | datetime | None = None,
    ) -> None:
        self._entries = entries
        self._start_date = start_date
        self._end_date = end_date

    def generate(self) -> WBSOReport:
        """Analyze entries and produce a structured report."""
        cloud_entries = [e for e in self._entries if isinstance(e, CloudQueryAuditEntry)]
        guardrail_entries = [e for e in self._entries if isinstance(e, GuardrailEventEntry)]
        isolation_entries = [e for e in self._entries if isinstance(e, PatientIsolationAuditEntry)]

        total = len(self._entries)
        cloud_count = len(cloud_entries)
        guardrail_count = len(guardrail_entries)
        isolation_count = len(isolation_entries)

        unique_users = len({e.session_hash for e in cloud_entries if e.session_hash})
        unique_resources = len({e.cloud_provider for e in cloud_entries if e.cloud_provider})

        guardrail_by_type = dict(Counter(e.guardrail_type.value for e in guardrail_entries))
        guardrail_by_action = dict(Counter(e.action_taken.value for e in guardrail_entries))

        guardrail_total = guardrail_count or 1
        blocked = sum(1 for e in guardrail_entries if e.action_taken == GuardrailAction.BLOCKED)
        warnings_count = sum(1 for e in guardrail_entries if e.action_taken == GuardrailAction.WARNING)
        guardrail_block_rate = blocked / guardrail_total
        guardrail_warning_rate = warnings_count / guardrail_total

        isolation_by_patient: Dict[str, int] = {}
        isolation_success = 0
        for e in isolation_entries:
            patient = e.requesting_patient_hash
            isolation_by_patient[patient] = isolation_by_patient.get(patient, 0) + 1
            if e.isolation_maintained:
                isolation_success += 1

        if isolation_count > 0:
            isolation_success_rate = isolation_success / isolation_count
        else:
            isolation_success_rate = 1.0

        start = self._start_date.date() if isinstance(self._start_date, datetime) else (self._start_date or date.today())
        end = self._end_date.date() if isinstance(self._end_date, datetime) else (self._end_date or date.today())

        return WBSOReport(
            total_entries=total,
            cloud_query_count=cloud_count,
            guardrail_event_count=guardrail_count,
            isolation_check_count=isolation_count,
            unique_users_count=unique_users,
            unique_resources_count=unique_resources,
            guardrail_by_type=guardrail_by_type,
            guardrail_by_action=guardrail_by_action,
            guardrail_block_rate=guardrail_block_rate,
            guardrail_warning_rate=guardrail_warning_rate,
            isolation_by_patient=isolation_by_patient,
            isolation_success_count=isolation_success,
            isolation_success_rate=isolation_success_rate,
            start_date=start,
            end_date=end,
        )
