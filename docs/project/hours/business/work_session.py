"""
Work Session Business Model

This module defines the WorkSession business entity for representing
work sessions with comprehensive tracking capabilities.

Business Domain: Work Session Management
Entity: WorkSession
Purpose: Unified model for work session tracking, hours calculation, and work item association
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, time, timedelta
import random


@dataclass
class WorkSession:
    """Represents a unified work session with comprehensive tracking capabilities.

    This business entity models a work session that can be used across different
    contexts: session detection, hours calculation, and work item tracking.
    It combines attributes from session detection and hours calculation contexts
    to provide a unified business model.

    Business Rules:
    - Sessions must have valid start and end times
    - Duration calculations must be consistent
    - Work items are referenced by ID to maintain separation of concerns
    - Break handling: Only lunch_break and dinner_break are tracked
    - Lunch break: Sessions starting before 10:00 and ending after 14:00
    - Dinner break: Sessions starting before 16:00 and ending after 20:00
    - Session splitting: Only for gaps > 90 minutes

    Core Attributes (Session Detection):
        session_id: Unique session identifier (format: session_XXX)
        start_time: Session start timestamp (string format for flexibility)
        end_time: Session end timestamp (string format for flexibility)
        total_duration_minutes: Total session duration including breaks
        work_duration_minutes: Actual work time excluding breaks
        date: Primary date for the session (YYYY-MM-DD format)
        crosses_midnight: Whether session was split due to midnight crossing

    Break Attributes:
        lunch_break: Lunch break information (30 min, 12:00-12:40 start)
        dinner_break: Dinner break information (45 min, 17:50-18:30 start)

    Hours Calculation Attributes:
        block_id: Alternative session identifier (format: cos_XXX)
        duration_hours: Total session duration in hours
        confidence_score: Confidence in session detection (0.0-1.0)
        evidence: List of evidence strings supporting this session
        session_type: Type of session (e.g., "work", "break")
        work_hours: Calculated work hours for this session

    Future WorkItems Integration:
        work_items: List of WorkItem IDs that occurred during this session
        work_item_count: Number of work items in this session
        work_item_types: Summary of work item types and counts
    """

    # Core session identification and timing
    session_id: str  # Format: session_XXX, unique identifier for this work session
    start_time: str  # Session start timestamp (flexible string format)
    end_time: str  # Session end timestamp (flexible string format)

    # Duration calculations (minutes-based for session detection)
    total_duration_minutes: int  # Total session time including breaks
    work_duration_minutes: int  # Actual work time excluding breaks

    # Session metadata
    date: str  # Primary date for session (YYYY-MM-DD format)
    crosses_midnight: bool  # Whether session was split due to midnight crossing

    # Break attributes (lunch and dinner only)
    lunch_break: Optional[str] = None  # Lunch break information (30 min, 12:00-12:40 start)
    dinner_break: Optional[str] = None  # Dinner break information (45 min, 17:50-18:30 start)

    # Hours calculation attributes
    block_id: Optional[str] = None  # Alternative session identifier (format: cos_XXX)
    duration_hours: Optional[float] = None  # Total session duration in hours
    confidence_score: Optional[float] = None  # Confidence in session detection (0.0-1.0)
    evidence: Optional[List[str]] = None  # List of evidence strings supporting this session
    session_type: Optional[str] = None  # Type of session (e.g., "work", "break")
    work_hours: Optional[float] = None  # Calculated work hours for this session

    # Future: WorkItems integration
    work_items: Optional[List[str]] = None  # List of WorkItem IDs (Git commits, etc.)
    work_item_count: Optional[int] = None  # Number of work items in this session
    work_item_types: Optional[Dict[str, int]] = None  # Summary of work item types and counts

    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Ensure block_id is set if not provided
        if self.block_id is None:
            self.block_id = self.session_id.replace("session_", "cos_")

        # Calculate duration_hours if not provided
        if self.duration_hours is None:
            self.duration_hours = self.total_duration_minutes / 60.0

        # Initialize work item tracking if not provided
        if self.work_items is None:
            self.work_items = []
        if self.work_item_count is None:
            self.work_item_count = len(self.work_items)
        if self.work_item_types is None:
            self.work_item_types = {}

        # Initialize evidence list if not provided
        if self.evidence is None:
            self.evidence = []

        # Set default confidence score if not provided
        if self.confidence_score is None:
            self.confidence_score = 1.0

        # Set default session type if not provided
        if self.session_type is None:
            self.session_type = "work"

        # Calculate breaks and work hours
        self._calculate_breaks_and_work_hours()

    def _calculate_breaks_and_work_hours(self) -> None:
        """Calculate lunch and dinner breaks based on session timing.

        Business Rules:
        - Lunch break: Sessions starting before 10:00 and ending after 14:00
        - Dinner break: Sessions starting before 16:00 and ending after 20:00
        - Lunch break: 30 minutes, random start between 12:00-12:40
        - Dinner break: 45 minutes, random start between 17:50-18:30
        """
        try:
            start_dt = self._parse_datetime(self.start_time)
            end_dt = self._parse_datetime(self.end_time)

            if not start_dt or not end_dt:
                return

            total_break_minutes = 0

            # Check for lunch break eligibility
            if start_dt.time() < time(10, 0) and end_dt.time() > time(14, 0):
                if not self.lunch_break:
                    # Generate random lunch break start time between 12:00-12:40
                    lunch_start_minute = random.randint(0, 40)  # 0-40 minutes past 12:00
                    lunch_start = time(12, lunch_start_minute)
                    lunch_end = time(12, lunch_start_minute + 30)
                    self.lunch_break = f"{lunch_start.strftime('%H:%M')}-{lunch_end.strftime('%H:%M')}"
                total_break_minutes += 30

            # Check for dinner break eligibility
            if start_dt.time() < time(16, 0) and end_dt.time() > time(20, 0):
                if not self.dinner_break:
                    # Generate random dinner break start time between 17:50-18:30
                    dinner_start_minute = random.randint(50, 80)  # 50-80 minutes past 17:00
                    dinner_start_hour = 17 + (dinner_start_minute // 60)
                    dinner_start_minute = dinner_start_minute % 60
                    dinner_start = time(dinner_start_hour, dinner_start_minute)
                    dinner_end_minute = dinner_start_minute + 45
                    dinner_end_hour = dinner_start_hour + (dinner_end_minute // 60)
                    dinner_end_minute = dinner_end_minute % 60
                    dinner_end = time(dinner_end_hour, dinner_end_minute)
                    self.dinner_break = f"{dinner_start.strftime('%H:%M')}-{dinner_end.strftime('%H:%M')}"
                total_break_minutes += 45

            # Calculate work hours excluding breaks
            self.work_duration_minutes = self.total_duration_minutes - total_break_minutes
            self.work_hours = self.work_duration_minutes / 60.0

        except Exception:
            # If parsing fails, keep existing values
            pass

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string with multiple format support.

        Args:
            dt_str: DateTime string in various formats

        Returns:
            datetime object or None if parsing fails
        """
        if not dt_str or dt_str.strip() == "":
            return None

        # Clean the datetime string
        clean_datetime = dt_str.strip()
        if clean_datetime.startswith('"'):
            clean_datetime = clean_datetime[1:]
        if clean_datetime.endswith('"'):
            clean_datetime = clean_datetime[:-1]
        # Remove BOM if present
        if clean_datetime.startswith("\ufeff"):
            clean_datetime = clean_datetime[1:]

        if not clean_datetime:
            return None

        formats = [
            "%m/%d/%Y %I:%M:%S %p",  # 5/9/2025 8:08:14 PM
            "%Y/%m/%d %H:%M:%S",  # 2025/06/24 07:30:54
            "%Y-%m-%d %H:%M:%S",  # 2025-06-24 07:30:54
            "%Y-%m-%dT%H:%M:%S",  # 2025-06-24T07:30:54
        ]

        for fmt in formats:
            try:
                return datetime.strptime(clean_datetime, fmt)
            except ValueError:
                continue

        return None

    def add_work_item(self, work_item_id: str, work_item_type: str = "commit") -> None:
        """Add a work item to this session.

        Args:
            work_item_id: Unique identifier for the work item
            work_item_type: Type of work item (e.g., "commit", "review", "document")
        """
        if self.work_items is None:
            self.work_items = []
        if self.work_item_types is None:
            self.work_item_types = {}

        self.work_items.append(work_item_id)
        self.work_item_count = len(self.work_items)

        # Update work item type count
        if work_item_type in self.work_item_types:
            self.work_item_types[work_item_type] += 1
        else:
            self.work_item_types[work_item_type] = 1

    def add_evidence(self, evidence_text: str) -> None:
        """Add evidence supporting this session.

        Args:
            evidence_text: Evidence string to add
        """
        if self.evidence is None:
            self.evidence = []
        self.evidence.append(evidence_text)

    def get_work_efficiency(self) -> float:
        """Calculate work efficiency as percentage of work time vs total time.

        Returns:
            Work efficiency as a percentage (0.0-1.0)
        """
        if self.total_duration_minutes == 0:
            return 0.0
        return self.work_duration_minutes / self.total_duration_minutes

    def get_break_efficiency(self) -> float:
        """Calculate break efficiency as percentage of break time vs total time.

        Returns:
            Break efficiency as a percentage (0.0-1.0)
        """
        if self.total_duration_minutes == 0:
            return 0.0

        total_break_minutes = 0
        if self.lunch_break:
            total_break_minutes += 30
        if self.dinner_break:
            total_break_minutes += 45

        return total_break_minutes / self.total_duration_minutes

    def to_dict(self) -> Dict[str, Any]:
        """Convert WorkSession to dictionary representation.

        Returns:
            Dictionary representation of the WorkSession
        """
        return {
            "session_id": self.session_id,
            "block_id": self.block_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_minutes": self.total_duration_minutes,
            "work_duration_minutes": self.work_duration_minutes,
            "duration_hours": self.duration_hours,
            "work_hours": self.work_hours,
            "date": self.date,
            "crosses_midnight": self.crosses_midnight,
            "confidence_score": self.confidence_score,
            "evidence": self.evidence,
            "session_type": self.session_type,
            "lunch_break": self.lunch_break,
            "dinner_break": self.dinner_break,
            "work_items": self.work_items,
            "work_item_count": self.work_item_count,
            "work_item_types": self.work_item_types,
            "work_efficiency": self.get_work_efficiency(),
            "break_efficiency": self.get_break_efficiency(),
        }
