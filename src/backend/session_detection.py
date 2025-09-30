"""
Work Session Detection Logic

This module implements business logic for detecting user work sessions based on
logon/logoff events with proper break handling and midnight crossing logic.

Business Requirements:
- WorkSessions are defined by user logon (7001) to logoff (7002) events
- Breaks < 15 minutes are ignored (continuous session)
- Breaks 15-90 minutes are marked as breaks within session
- Breaks > 90 minutes create new sessions
- Sessions crossing midnight are split at midnight

Future Enhancement: This module will be extended to support WorkItems integration,
where each WorkSession can contain references to WorkItems (Git commits, document
edits, code reviews) that occurred during the session period.
"""

from datetime import datetime, time
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging
import sys
from pathlib import Path

# Add business layer to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "docs" / "project" / "hours"))

from business import WorkSession, SystemEvent

logger = logging.getLogger(__name__)


# SystemEvent and WorkSession classes are now imported from business layer


def parse_datetime_flexible(dt_str: str) -> Optional[datetime]:
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

    logger.warning(f"Could not parse datetime: {dt_str}")
    return None


def calculate_break_duration(logoff_time: datetime, logon_time: datetime) -> int:
    """Calculate break duration in minutes between logoff and logon.

    Args:
        logoff_time: Time when user logged off
        logon_time: Time when user logged back on

    Returns:
        Break duration in minutes
    """
    duration = logon_time - logoff_time
    return int(duration.total_seconds() / 60)


def is_midnight_crossing(start_time: datetime, end_time: datetime) -> bool:
    """Check if session crosses midnight boundary.

    Args:
        start_time: Session start time
        end_time: Session end time

    Returns:
        True if session crosses midnight, False otherwise
    """
    return start_time.date() != end_time.date()


def split_session_at_midnight(start_time: datetime, end_time: datetime) -> Tuple[datetime, datetime]:
    """Split session at midnight boundary.

    Args:
        start_time: Original session start time
        end_time: Original session end time

    Returns:
        Tuple of (first_session_end, second_session_start) both at midnight
    """
    # First session ends at 23:59:59 of start date
    first_end = datetime.combine(start_time.date(), time(23, 59, 59))

    # Second session starts at 00:00:00 of end date
    second_start = datetime.combine(end_time.date(), time.min)

    return first_end, second_start


class SessionDetector:
    """Detects user work sessions from logon/logoff events.

    This class implements the business logic for WorkSession detection including:
    - Break handling (ignore < 15 min, mark 15-90 min, split > 90 min)
    - Midnight crossing detection and splitting
    - Session duration calculations

    Future Enhancement: This class will be extended to associate WorkItems
    (Git commits, document edits, code reviews) with detected WorkSessions
    based on timestamp correlation.
    """

    def __init__(self, short_break_threshold: int = 15, long_break_threshold: int = 90):
        """Initialize session detector with break thresholds.

        Args:
            short_break_threshold: Minutes below which breaks are ignored
            long_break_threshold: Minutes above which breaks create new sessions
        """
        self.short_break_threshold = short_break_threshold
        self.long_break_threshold = long_break_threshold

    def detect_sessions(self, events: List[SystemEvent]) -> List[WorkSession]:
        """Detect user sessions from logon/logoff events with simple business rules.

        Business Rules:
        1. If list starts with logoff, prepend logon at 00:00:00 same day
        2. If list ends with logon, append logoff at 23:59:59 same day
        3. Ignore logon when already logged on (extend current session)
        4. Ignore logoff when already logged off (extend current session)
        5. Create logon-logoff couples for session detection
        6. Breaks < 15min: ignore (continuous session)
        7. Breaks 15-90min: mark as break within session
        8. Breaks > 90min: create new session
        9. Sessions crossing midnight: split at midnight

        Args:
            events: List of system events sorted by datetime

        Returns:
            List of WorkSession objects
        """
        # Filter and sort logon/logoff events
        logon_logoff_events = [
            event
            for event in events
            if event.event_id in ["7001", "7002"]  # 7001=logon, 7002=logoff
        ]

        if not logon_logoff_events:
            logger.info("No logon/logoff events found")
            return []

        # Sort events by datetime
        logon_logoff_events.sort(key=lambda x: parse_datetime_flexible(x.datetime) or datetime.min)

        # Normalize event sequence: ensure proper logon-logoff couples
        normalized_events = self._normalize_event_sequence(logon_logoff_events)

        # Create sessions from logon-logoff couples
        sessions = []
        session_counter = 1

        for i in range(0, len(normalized_events), 2):
            if i + 1 >= len(normalized_events):
                break  # Skip incomplete couples

            logon_event = normalized_events[i]
            logoff_event = normalized_events[i + 1]

            # Check for midnight crossing
            logon_dt = parse_datetime_flexible(logon_event.datetime)
            logoff_dt = parse_datetime_flexible(logoff_event.datetime)

            if not logon_dt or not logoff_dt:
                continue

            if is_midnight_crossing(logon_dt, logoff_dt):
                # Split session at midnight
                first_end, second_start = split_session_at_midnight(logon_dt, logoff_dt)

                # Create first session (up to midnight)
                first_session = self._create_session(
                    session_counter,
                    logon_event.datetime,
                    first_end.strftime("%m/%d/%Y %I:%M:%S %p"),
                    [logon_event],
                    [],
                    crosses_midnight=True,
                )
                sessions.append(first_session)
                session_counter += 1

                # Create second session (from midnight)
                second_session = self._create_session(
                    session_counter,
                    second_start.strftime("%m/%d/%Y %I:%M:%S %p"),
                    logoff_event.datetime,
                    [logoff_event],
                    [],
                    crosses_midnight=True,
                )
                sessions.append(second_session)
                session_counter += 1
            else:
                # Single session
                session = self._create_session(
                    session_counter,
                    logon_event.datetime,
                    logoff_event.datetime,
                    [logon_event, logoff_event],
                    [],
                    crosses_midnight=False,
                )
                sessions.append(session)
                session_counter += 1

        # Handle breaks between sessions
        sessions = self._process_session_breaks(sessions)

        logger.info(f"Detected {len(sessions)} user sessions")
        return sessions

    def _normalize_event_sequence(self, events: List[SystemEvent]) -> List[SystemEvent]:
        """Normalize event sequence to ensure proper logon-logoff couples.

        Args:
            events: Sorted list of logon/logoff events

        Returns:
            Normalized list with proper logon-logoff couples
        """
        if not events:
            return []

        normalized = []
        current_state = "logged_off"  # Start assuming logged off

        for event in events:
            event_dt = parse_datetime_flexible(event.datetime)
            if not event_dt:
                continue

            if event.event_id == "7001":  # Logon
                if current_state == "logged_off":
                    # Valid logon - add to sequence
                    normalized.append(event)
                    current_state = "logged_on"
                # If already logged on, ignore (extend current session)

            elif event.event_id == "7002":  # Logoff
                if current_state == "logged_on":
                    # Valid logoff - add to sequence
                    normalized.append(event)
                    current_state = "logged_off"
                # If already logged off, ignore (extend current session)

        # Handle edge cases
        if normalized and normalized[0].event_id == "7002":
            # Started with logoff - prepend logon at 00:00:00
            first_event_dt = parse_datetime_flexible(normalized[0].datetime)
            if first_event_dt:
                midnight_logon = SystemEvent(
                    datetime=first_event_dt.replace(hour=0, minute=0, second=0).strftime("%m/%d/%Y %I:%M:%S %p"),
                    event_id="7001",
                    event_type="User logon notification (inferred)",
                    username=normalized[0].username,
                    message="User Logon Notification (inferred start of day)",
                    record_id="inferred_000",
                )
                normalized.insert(0, midnight_logon)

        if normalized and normalized[-1].event_id == "7001":
            # Ended with logon - append logoff at 23:59:59
            last_event_dt = parse_datetime_flexible(normalized[-1].datetime)
            if last_event_dt:
                end_of_day_logoff = SystemEvent(
                    datetime=last_event_dt.replace(hour=23, minute=59, second=59).strftime("%m/%d/%Y %I:%M:%S %p"),
                    event_id="7002",
                    event_type="User logoff notification (inferred)",
                    username=normalized[-1].username,
                    message="User Logoff Notification (inferred end of day)",
                    record_id="inferred_999",
                )
                normalized.append(end_of_day_logoff)

        return normalized

    def _process_session_breaks(self, sessions: List[WorkSession]) -> List[WorkSession]:
        """Process breaks between sessions - only split for gaps > 90 minutes.

        Args:
            sessions: List of sessions to process

        Returns:
            Processed sessions with break handling
        """
        if len(sessions) <= 1:
            return sessions

        processed_sessions = []
        i = 0

        while i < len(sessions):
            current_session = sessions[i]

            # Check if there's a next session to compare with
            if i + 1 < len(sessions):
                next_session = sessions[i + 1]

                # Don't merge sessions that were split at midnight
                if current_session.crosses_midnight or next_session.crosses_midnight:
                    processed_sessions.append(current_session)
                    i += 1
                    continue

                # Calculate break duration between sessions
                current_end = parse_datetime_flexible(current_session.end_time)
                next_start = parse_datetime_flexible(next_session.start_time)

                if current_end and next_start:
                    break_duration = calculate_break_duration(current_end, next_start)

                    if break_duration <= self.long_break_threshold:
                        # Break <= 90 minutes - merge sessions
                        merged_session = self._merge_sessions(current_session, next_session)
                        processed_sessions.append(merged_session)
                        i += 2  # Skip next session as it's merged
                        continue
                    # Break > 90 minutes - keep sessions separate

            # No break processing needed
            processed_sessions.append(current_session)
            i += 1

        return processed_sessions

    def _merge_sessions(self, session1: WorkSession, session2: WorkSession) -> WorkSession:
        """Merge two sessions into one.

        Args:
            session1: First session
            session2: Second session

        Returns:
            Merged session
        """
        start_dt = parse_datetime_flexible(session1.start_time)
        end_dt = parse_datetime_flexible(session2.end_time)

        if not start_dt or not end_dt:
            return session1

        total_duration = int((end_dt - start_dt).total_seconds() / 60)
        # Work duration will be recalculated by business layer based on lunch/dinner breaks
        work_duration = total_duration

        return WorkSession(
            session_id=session1.session_id,
            start_time=session1.start_time,
            end_time=session2.end_time,
            total_duration_minutes=total_duration,
            work_duration_minutes=work_duration,  # Will be recalculated by business layer
            date=session1.date,
            crosses_midnight=session1.crosses_midnight or session2.crosses_midnight,
            # Business layer will set defaults for optional parameters
            block_id=session1.block_id,
            duration_hours=None,
            confidence_score=None,
            evidence=None,
            session_type=None,
            work_hours=None,
            lunch_break=None,
            dinner_break=None,
            work_items=None,
            work_item_count=None,
            work_item_types=None,
        )

    def _create_session(
        self, session_id: int, start_time: str, end_time: str, events: List[SystemEvent], breaks: List[dict], crosses_midnight: bool
    ) -> WorkSession:
        """Create a WorkSession object from events and breaks.

        This method constructs a WorkSession with calculated durations and metadata.
        Future enhancement: This method will be extended to associate WorkItems
        (Git commits, document edits, etc.) that occurred during the session period.

        Args:
            session_id: Unique session identifier
            start_time: Session start timestamp
            end_time: Session end timestamp
            events: List of events in this session
            breaks: List of break periods
            crosses_midnight: Whether session was split at midnight

        Returns:
            WorkSession object with calculated durations and metadata
        """
        start_dt = parse_datetime_flexible(start_time)
        end_dt = parse_datetime_flexible(end_time)

        if not start_dt or not end_dt:
            raise ValueError(f"Invalid datetime: start={start_time}, end={end_time}")

        # Calculate durations
        total_duration = int((end_dt - start_dt).total_seconds() / 60)
        # Work duration will be recalculated by business layer based on lunch/dinner breaks
        work_duration = total_duration

        return WorkSession(
            session_id=f"session_{session_id:03d}",
            start_time=start_time,
            end_time=end_time,
            total_duration_minutes=total_duration,
            work_duration_minutes=work_duration,  # Will be recalculated by business layer
            date=start_dt.strftime("%Y-%m-%d"),
            crosses_midnight=crosses_midnight,
            # Business layer will set defaults for optional parameters
            block_id=None,
            duration_hours=None,
            confidence_score=None,
            evidence=None,
            session_type=None,
            work_hours=None,
            lunch_break=None,
            dinner_break=None,
            work_items=None,
            work_item_count=None,
            work_item_types=None,
        )
