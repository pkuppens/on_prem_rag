#!/usr/bin/env python3
"""
WBSO Calendar Event Data Models

This module provides data models for WBSO calendar events, including validation,
conversion to Google Calendar format, and comprehensive data management.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Date: 2025-10-18
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from .logging_config import get_logger

logger = get_logger("calendar_event")


@dataclass
class ValidationResult:
    """Validation report for data models."""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    session_id: str = ""
    validation_timestamp: datetime = field(default_factory=datetime.now)

    def add_error(self, error: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "session_id": self.session_id,
            "validation_timestamp": self.validation_timestamp.isoformat(),
        }


@dataclass
class WBSOSession:
    """Represents a work session with validation."""

    session_id: str
    start_time: datetime
    end_time: datetime
    work_hours: float
    duration_hours: float
    date: str
    session_type: str
    is_wbso: bool
    wbso_category: str
    is_synthetic: bool
    commit_count: int
    source_type: str
    repository_name: str = ""
    wbso_justification: str = ""
    assigned_commits: List[str] = field(default_factory=list)
    confidence_score: float = 1.0

    def validate(self) -> ValidationResult:
        """Validate session data and return result."""
        result = ValidationResult(session_id=self.session_id)

        # Required field validation
        if not self.session_id:
            result.add_error("session_id is required")
        if not self.start_time:
            result.add_error("start_time is required")
        if not self.end_time:
            result.add_error("end_time is required")
        if self.work_hours is None:
            result.add_error("work_hours is required")
        if not self.date:
            result.add_error("date is required")
        if not self.session_type:
            result.add_error("session_type is required")
        if self.is_wbso is None:
            result.add_error("is_wbso is required")
        if not self.wbso_category:
            result.add_error("wbso_category is required")
        if self.is_synthetic is None:
            result.add_error("is_synthetic is required")
        if self.commit_count is None:
            result.add_error("commit_count is required")
        if not self.source_type:
            result.add_error("source_type is required")

        # Time validation
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                result.add_error("start_time must be before end_time")
            duration = self.end_time - self.start_time
            if duration.total_seconds() > 24 * 3600:  # 24 hours
                result.add_error("session duration cannot exceed 24 hours")

        # Hours validation
        if self.work_hours is not None:
            if self.work_hours < 0:
                result.add_error("work_hours cannot be negative")
            if self.work_hours > 24:
                result.add_error("work_hours cannot exceed 24")
            if self.duration_hours and self.work_hours > self.duration_hours:
                result.add_error("work_hours cannot exceed duration_hours")

        # WBSO validation
        if self.is_wbso:
            valid_categories = ["AI_FRAMEWORK", "ACCESS_CONTROL", "PRIVACY_CLOUD", "AUDIT_LOGGING", "DATA_INTEGRITY", "GENERAL_RD"]
            if self.wbso_category not in valid_categories:
                result.add_error(f"Invalid WBSO category: {self.wbso_category}")
            if not self.wbso_justification:
                result.add_error("WBSO justification is required for WBSO sessions")

        # Session type validation
        valid_types = ["morning", "afternoon", "evening", "full_day", "short_session"]
        if self.session_type not in valid_types:
            result.add_warning(f"Unknown session type: {self.session_type}")

        # Source type validation
        valid_sources = ["real", "synthetic"]
        if self.source_type not in valid_sources:
            result.add_error(f"Invalid source_type: {self.source_type}")

        # Commit count validation
        if self.commit_count is not None:
            if self.commit_count < 0:
                result.add_error("commit_count cannot be negative")
            if len(self.assigned_commits) != self.commit_count:
                result.add_warning(
                    f"commit_count ({self.commit_count}) doesn't match assigned_commits length ({len(self.assigned_commits)})"
                )

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "work_hours": self.work_hours,
            "duration_hours": self.duration_hours,
            "date": self.date,
            "session_type": self.session_type,
            "is_wbso": self.is_wbso,
            "wbso_category": self.wbso_category,
            "is_synthetic": self.is_synthetic,
            "commit_count": self.commit_count,
            "source_type": self.source_type,
            "repository_name": self.repository_name,
            "wbso_justification": self.wbso_justification,
            "assigned_commits": self.assigned_commits,
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WBSOSession":
        """Create from dictionary format."""
        # Parse datetime fields
        start_time = None
        if data.get("start_time"):
            if isinstance(data["start_time"], str):
                start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
            else:
                start_time = data["start_time"]

        end_time = None
        if data.get("end_time"):
            if isinstance(data["end_time"], str):
                end_time = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
            else:
                end_time = data["end_time"]

        return cls(
            session_id=data.get("session_id", ""),
            start_time=start_time,
            end_time=end_time,
            work_hours=data.get("work_hours", 0.0),
            duration_hours=data.get("duration_hours", 0.0),
            date=data.get("date", ""),
            session_type=data.get("session_type", ""),
            is_wbso=data.get("is_wbso", False),
            wbso_category=data.get("wbso_category", ""),
            is_synthetic=data.get("is_synthetic", False),
            commit_count=data.get("commit_count", 0),
            source_type=data.get("source_type", ""),
            repository_name=data.get("repository_name", ""),
            wbso_justification=data.get("wbso_justification", ""),
            assigned_commits=data.get("assigned_commits", []),
            confidence_score=data.get("confidence_score", 1.0),
        )

    def get_duration(self) -> timedelta:
        """Get session duration as timedelta."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return timedelta(0)


@dataclass
class CalendarEvent:
    """Google Calendar API compatible event."""

    summary: str
    description: str
    start: Dict[str, str]
    end: Dict[str, str]
    color_id: str = "1"
    extended_properties: Dict[str, Any] = field(default_factory=dict)
    location: str = "Home Office"
    transparency: str = "opaque"

    def validate(self) -> ValidationResult:
        """Validate event data."""
        result = ValidationResult()

        # Required field validation
        if not self.summary:
            result.add_error("summary is required")
        if not self.description:
            result.add_error("description is required")
        if not self.start:
            result.add_error("start is required")
        if not self.end:
            result.add_error("end is required")

        # Start/end validation
        if self.start and self.end:
            if "dateTime" not in self.start:
                result.add_error("start must contain dateTime")
            if "dateTime" not in self.end:
                result.add_error("end must contain dateTime")
            if "timeZone" not in self.start:
                result.add_error("start must contain timeZone")
            if "timeZone" not in self.end:
                result.add_error("end must contain timeZone")

            # Parse and validate datetime
            try:
                start_dt = datetime.fromisoformat(self.start["dateTime"].replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(self.end["dateTime"].replace("Z", "+00:00"))
                if start_dt >= end_dt:
                    result.add_error("start time must be before end time")
            except ValueError as e:
                result.add_error(f"Invalid datetime format: {e}")

        # Extended properties validation
        if self.extended_properties:
            required_wbso_fields = ["wbso_project", "wbso_category", "session_id", "work_hours"]
            for field in required_wbso_fields:
                if field not in self.extended_properties.get("private", {}):
                    result.add_warning(f"Missing WBSO field: {field}")

        return result

    def to_google_format(self) -> Dict[str, Any]:
        """Convert to Google Calendar API format."""
        return {
            "summary": self.summary,
            "description": self.description,
            "start": self.start,
            "end": self.end,
            "colorId": self.color_id,
            "extendedProperties": self.extended_properties,
            "location": self.location,
            "transparency": self.transparency,
        }

    @classmethod
    def from_wbso_session(cls, session: WBSOSession) -> "CalendarEvent":
        """Create from WBSOSession."""
        # Generate event title
        title = f"WBSO: {session.wbso_category.replace('_', ' ').title()} - {session.session_type.title()}"

        # Generate description
        description = f"""WBSO Project: WBSO-AICM-2025-01: AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving

Category: {session.wbso_category}
Activity: {session.wbso_category.replace("_", " ").title()}
Session Type: {session.session_type.title()}
Duration: {session.work_hours} hours

Description: {session.wbso_justification}

Technical Details:
- Source: {"Synthetic" if session.is_synthetic else "Real"} session
- Commits: {session.commit_count}
- Confidence: {session.confidence_score:.2f}
- Date: {session.date}

This work session qualifies for WBSO tax deduction under category {session.wbso_category}."""

        # Format datetime for Google Calendar
        start_dt = session.start_time.strftime("%Y-%m-%dT%H:%M:%S")
        end_dt = session.end_time.strftime("%Y-%m-%dT%H:%M:%S")

        # Extended properties for WBSO tracking
        extended_properties = {
            "private": {
                "wbso_project": "WBSO-AICM-2025-01",
                "wbso_category": session.wbso_category,
                "session_id": session.session_id,
                "work_hours": str(session.work_hours),
                "is_synthetic": str(session.is_synthetic),
                "commit_count": str(session.commit_count),
                "source_type": session.source_type,
                "confidence_score": str(session.confidence_score),
            }
        }

        return cls(
            summary=title,
            description=description,
            start={"dateTime": start_dt, "timeZone": "Europe/Amsterdam"},
            end={"dateTime": end_dt, "timeZone": "Europe/Amsterdam"},
            color_id="1",  # Blue color for WBSO events
            extended_properties=extended_properties,
            location="Home Office",
            transparency="opaque",
        )

    def has_required_wbso_fields(self) -> bool:
        """Check if event has required WBSO fields."""
        required_fields = ["wbso_project", "wbso_category", "session_id", "work_hours"]
        private_props = self.extended_properties.get("private", {})
        return all(field in private_props for field in required_fields)


class WBSODataset:
    """Collection of WBSO sessions with validation capabilities."""

    def __init__(self):
        self.sessions: List[WBSOSession] = []

    def load_from_json(self, file_path: Union[str, Path]) -> None:
        """Load sessions from JSON file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, dict):
            if "work_sessions" in data:
                sessions_data = data["work_sessions"]
            elif "sessions" in data:
                sessions_data = data["sessions"]
            elif "synthetic_sessions" in data:
                sessions_data = data["synthetic_sessions"]
            else:
                # Assume the dict itself contains session data
                sessions_data = [data]
        elif isinstance(data, list):
            sessions_data = data
        else:
            raise ValueError("Invalid JSON structure")

        # Convert to WBSOSession objects
        for session_data in sessions_data:
            try:
                session = WBSOSession.from_dict(session_data)
                self.sessions.append(session)
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")

        logger.info(f"Loaded {len(self.sessions)} sessions from {file_path}")

    def validate_all(self) -> List[ValidationResult]:
        """Validate all sessions and return results."""
        results = []
        for session in self.sessions:
            result = session.validate()
            results.append(result)
        return results

    def find_duplicates(self) -> Dict[str, List[str]]:
        """Find duplicate session_ids and datetime ranges."""
        duplicates = {"session_ids": {}, "datetime_ranges": {}}

        # Check for duplicate session_ids
        session_id_counts = {}
        for session in self.sessions:
            if session.session_id in session_id_counts:
                session_id_counts[session.session_id].append(session)
            else:
                session_id_counts[session.session_id] = [session]

        for session_id, sessions in session_id_counts.items():
            if len(sessions) > 1:
                duplicates["session_ids"][session_id] = [s.session_id for s in sessions]

        # Check for duplicate datetime ranges
        datetime_counts = {}
        for session in self.sessions:
            if session.start_time and session.end_time:
                dt_key = f"{session.start_time.isoformat()}-{session.end_time.isoformat()}"
                if dt_key in datetime_counts:
                    datetime_counts[dt_key].append(session)
                else:
                    datetime_counts[dt_key] = [session]

        for dt_key, sessions in datetime_counts.items():
            if len(sessions) > 1:
                duplicates["datetime_ranges"][dt_key] = [s.session_id for s in sessions]

        return duplicates

    def find_overlaps(self) -> List[Dict[str, Any]]:
        """Find overlapping sessions."""
        overlaps = []

        for i, session1 in enumerate(self.sessions):
            for j, session2 in enumerate(self.sessions[i + 1 :], i + 1):
                if session1.start_time and session1.end_time and session2.start_time and session2.end_time:
                    # Check for overlap
                    overlap_start = max(session1.start_time, session2.start_time)
                    overlap_end = min(session1.end_time, session2.end_time)

                    if overlap_start < overlap_end:
                        overlap_duration = overlap_end - overlap_start
                        overlap_hours = overlap_duration.total_seconds() / 3600

                        overlaps.append(
                            {
                                "session1_id": session1.session_id,
                                "session2_id": session2.session_id,
                                "overlap_start": overlap_start.isoformat(),
                                "overlap_end": overlap_end.isoformat(),
                                "overlap_hours": overlap_hours,
                                "severity": "critical" if overlap_hours > 1.0 else "warning",
                            }
                        )

        return overlaps

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[WBSOSession]:
        """Get sessions within date range."""
        filtered_sessions = []
        for session in self.sessions:
            if session.start_time and session.end_time:
                if start_date <= session.start_time <= end_date or start_date <= session.end_time <= end_date:
                    filtered_sessions.append(session)
        return filtered_sessions

    def export_to_json(self, file_path: Union[str, Path]) -> None:
        """Export sessions to JSON file."""
        file_path = Path(file_path)
        data = {
            "sessions": [session.to_dict() for session in self.sessions],
            "export_timestamp": datetime.now().isoformat(),
            "total_sessions": len(self.sessions),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(self.sessions)} sessions to {file_path}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics."""
        wbso_sessions = [s for s in self.sessions if s.is_wbso]
        real_sessions = [s for s in self.sessions if s.source_type == "real"]
        synthetic_sessions = [s for s in self.sessions if s.source_type == "synthetic"]

        # Calculate hours
        total_hours = sum(s.work_hours for s in self.sessions)
        wbso_hours = sum(s.work_hours for s in wbso_sessions)
        real_hours = sum(s.work_hours for s in real_sessions)
        synthetic_hours = sum(s.work_hours for s in synthetic_sessions)

        # Category breakdown
        category_breakdown = {}
        for session in wbso_sessions:
            if session.wbso_category in category_breakdown:
                category_breakdown[session.wbso_category]["count"] += 1
                category_breakdown[session.wbso_category]["hours"] += session.work_hours
            else:
                category_breakdown[session.wbso_category] = {"count": 1, "hours": session.work_hours}

        return {
            "total_sessions": len(self.sessions),
            "wbso_sessions": len(wbso_sessions),
            "real_sessions": len(real_sessions),
            "synthetic_sessions": len(synthetic_sessions),
            "total_hours": total_hours,
            "wbso_hours": wbso_hours,
            "real_hours": real_hours,
            "synthetic_hours": synthetic_hours,
            "wbso_percentage": (wbso_hours / total_hours * 100) if total_hours > 0 else 0,
            "category_breakdown": category_breakdown,
            "date_range": {
                "earliest": min(s.start_time for s in self.sessions if s.start_time).isoformat() if self.sessions else None,
                "latest": max(s.end_time for s in self.sessions if s.end_time).isoformat() if self.sessions else None,
            },
        }

    @property
    def total_hours(self) -> float:
        """Total hours across all sessions."""
        return sum(s.work_hours for s in self.sessions)

    @property
    def wbso_hours(self) -> float:
        """WBSO hours across all sessions."""
        return sum(s.work_hours for s in self.sessions if s.is_wbso)

    @property
    def session_count(self) -> int:
        """Total number of sessions."""
        return len(self.sessions)
