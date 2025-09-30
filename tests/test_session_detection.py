"""
Test Work Session Detection Logic

This module tests the work session detection logic based on logon/logoff events
with proper break handling and midnight crossing logic.

Business Requirements:
- WorkSessions are defined by user logon (7001) to logoff (7002) events
- Breaks < 15 minutes are ignored (continuous session)
- Breaks 15-90 minutes are marked as breaks within session
- Breaks > 90 minutes create new sessions
- Sessions crossing midnight are split at midnight

Future Enhancement: Tests will be extended to validate WorkItems integration
with WorkSessions, ensuring proper association of Git commits and other work
items with detected work sessions.
"""

from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Add business layer to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "docs" / "project" / "hours"))

from backend.session_detection import SessionDetector, parse_datetime_flexible, calculate_break_duration
from business import WorkSession, SystemEvent


class TestSessionDetection:
    """Test work session detection logic with logon/logoff events.

    This test class validates WorkSession detection, break handling, and midnight
    crossing logic. Future tests will validate WorkItems integration with WorkSessions.
    """

    def test_parse_datetime_flexible(self):
        """As a user I want datetime parsing to handle various formats, so I can process different event sources.
        Technical: parse_datetime_flexible should handle common datetime formats from system events.
        Validation: Test multiple datetime string formats return correct datetime objects.
        """
        # Test various datetime formats
        test_cases = [
            ("5/9/2025 8:08:14 PM", datetime(2025, 5, 9, 20, 8, 14)),
            ("5/9/2025 8:12:12 PM", datetime(2025, 5, 9, 20, 12, 12)),
            ("5/30/2025 6:25:55 PM", datetime(2025, 5, 30, 18, 25, 55)),
            ("5/31/2025 12:41:08 AM", datetime(2025, 5, 31, 0, 41, 8)),
        ]

        for dt_str, expected in test_cases:
            result = parse_datetime_flexible(dt_str)
            assert result == expected, f"Failed to parse {dt_str}: got {result}, expected {expected}"

    def test_calculate_break_duration(self):
        """As a user I want break durations calculated correctly, so I can determine session continuity.
        Technical: calculate_break_duration should return minutes between logoff and next logon.
        Validation: Test various break durations return correct minute values.
        """
        # Test break duration calculation
        logoff_time = datetime(2025, 5, 9, 20, 8, 14)  # 8:08:14 PM
        logon_time = datetime(2025, 5, 9, 20, 12, 12)  # 8:12:12 PM

        duration = calculate_break_duration(logoff_time, logon_time)
        assert duration == 3, f"Expected 3 minutes (3m58s), got {duration}"

    def test_short_break_ignored(self):
        """As a user I want short breaks (< 90 minutes) to be merged, so I can maintain session continuity.
        Technical: Breaks less than 90 minutes should merge sessions.
        Validation: Test that 4-minute break on 5/9/2025 8:08-8:12 PM is merged.
        """
        # Create test events for 5/9/2025 case
        events = [
            SystemEvent(
                datetime="5/9/2025 8:08:14 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39100",
            ),
            SystemEvent(
                datetime="5/9/2025 8:12:12 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39325",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 continuous session, not 2 separate sessions
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        # No lunch or dinner break should be assigned (session is too short)
        assert sessions[0].lunch_break is None, "Short session should not have lunch break"
        assert sessions[0].dinner_break is None, "Short session should not have dinner break"

    def test_medium_break_merged(self):
        """As a user I want medium breaks (15-90 minutes) to be merged, so I can maintain session continuity.
        Technical: Breaks between 15-90 minutes should merge sessions.
        Validation: Test that 30-minute break creates merged session.
        """
        # Create test events with 30-minute break
        events = [
            SystemEvent(
                datetime="5/9/2025 8:00:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39000",
            ),
            SystemEvent(
                datetime="5/9/2025 8:15:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39001",
            ),
            SystemEvent(
                datetime="5/9/2025 8:45:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39002",
            ),
            SystemEvent(
                datetime="5/9/2025 9:00:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39003",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 merged session
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        # No lunch or dinner break should be assigned (session is too short)
        assert sessions[0].lunch_break is None, "Short session should not have lunch break"
        assert sessions[0].dinner_break is None, "Short session should not have dinner break"

    def test_long_break_creates_new_session(self):
        """As a user I want long breaks (> 90 minutes) to create new sessions, so I can separate distinct work periods.
        Technical: Breaks longer than 90 minutes should create separate sessions.
        Validation: Test that 2-hour break creates two separate sessions.
        """
        # Create test events with 2-hour break
        events = [
            SystemEvent(
                datetime="5/9/2025 8:00:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39000",
            ),
            SystemEvent(
                datetime="5/9/2025 8:30:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39001",
            ),
            SystemEvent(
                datetime="5/9/2025 10:30:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39002",
            ),
            SystemEvent(
                datetime="5/9/2025 11:00:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39003",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 2 separate sessions
        assert len(sessions) == 2, f"Expected 2 sessions, got {len(sessions)}"
        # No lunch or dinner break should be assigned (sessions are too short)
        assert sessions[0].lunch_break is None, "First session should not have lunch break"
        assert sessions[0].dinner_break is None, "First session should not have dinner break"
        assert sessions[1].lunch_break is None, "Second session should not have lunch break"
        assert sessions[1].dinner_break is None, "Second session should not have dinner break"

    def test_midnight_crossing_split(self):
        """As a user I want sessions crossing midnight to be split, so I can track daily work hours accurately.
        Technical: Sessions crossing midnight should be split at midnight boundary.
        Validation: Test that 5/30 6:25 PM to 5/31 12:41 AM session is split at midnight.
        """
        # Create test events crossing midnight
        events = [
            SystemEvent(
                datetime="5/30/2025 6:25:55 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="47047",
            ),
            SystemEvent(
                datetime="5/31/2025 12:41:08 AM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="47179",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 2 sessions split at midnight
        assert len(sessions) == 2, f"Expected 2 sessions, got {len(sessions)}"

        # First session should end at 23:59:59
        first_session_end = parse_datetime_flexible(sessions[0].end_time)
        assert first_session_end.hour == 23 and first_session_end.minute == 59, (
            f"First session should end at 23:59:59, got {sessions[0].end_time}"
        )

        # Second session should start at midnight
        second_session_start = parse_datetime_flexible(sessions[1].start_time)
        assert second_session_start.hour == 0 and second_session_start.minute == 0, (
            f"Second session should start at midnight, got {sessions[1].start_time}"
        )

    def test_real_data_5_9_2025_case(self):
        """As a user I want the 5/9/2025 8:08-8:12 PM case to be handled correctly, so I can validate against real data.
        Technical: Test the specific real-world case with 4-minute break that should be merged.
        Validation: Verify that the actual 5/9/2025 events create one continuous session.
        """
        # Real events from the CSV file
        events = [
            SystemEvent(
                datetime="5/9/2025 8:08:14 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification for Customer Experience Improvement Program",
                record_id="39100",
            ),
            SystemEvent(
                datetime="5/9/2025 8:12:12 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification for Customer Experience Improvement Program",
                record_id="39325",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 session (break merged)
        assert len(sessions) == 1, f"Expected 1 session for 5/9/2025 case, got {len(sessions)}"
        # No lunch or dinner break should be assigned (session is too short)
        assert sessions[0].lunch_break is None, "Short session should not have lunch break"
        assert sessions[0].dinner_break is None, "Short session should not have dinner break"

    def test_real_data_5_30_5_31_midnight_case(self):
        """As a user I want the 5/30-5/31 midnight crossing case to be handled correctly, so I can validate against real data.
        Technical: Test the specific real-world case with session crossing midnight.
        Validation: Verify that the actual 5/30-5/31 events are split at midnight.
        """
        # Real events from the CSV file
        events = [
            SystemEvent(
                datetime="5/30/2025 6:25:55 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification for Customer Experience Improvement Program",
                record_id="47047",
            ),
            SystemEvent(
                datetime="5/31/2025 12:41:08 AM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification for Customer Experience Improvement Program",
                record_id="47179",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 2 sessions split at midnight
        assert len(sessions) == 2, f"Expected 2 sessions for 5/30-5/31 case, got {len(sessions)}"

        # Verify midnight split
        first_end = parse_datetime_flexible(sessions[0].end_time)
        second_start = parse_datetime_flexible(sessions[1].start_time)

        assert first_end.date() == datetime(2025, 5, 30).date(), "First session should end on 5/30"
        assert second_start.date() == datetime(2025, 5, 31).date(), "Second session should start on 5/31"
        assert first_end.hour == 23 and first_end.minute == 59, "First session should end at 23:59:59"
        assert second_start.hour == 0 and second_start.minute == 0, "Second session should start at midnight"

    def test_session_duration_calculation(self):
        """As a user I want session durations calculated correctly, so I can track work time accurately.
        Technical: Session duration should be calculated from start to end time excluding breaks.
        Validation: Test that session duration calculation handles breaks correctly.
        """
        # Create session with break
        events = [
            SystemEvent(
                datetime="5/9/2025 8:00:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39000",
            ),
            SystemEvent(
                datetime="5/9/2025 8:15:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39001",
            ),
            SystemEvent(
                datetime="5/9/2025 8:45:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39002",
            ),
            SystemEvent(
                datetime="5/9/2025 9:00:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39003",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 session with 1 hour total duration (15 min + 15 min)
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        assert sessions[0].total_duration_minutes == 60, f"Expected 60 minutes total, got {sessions[0].total_duration_minutes}"
        # Work duration should equal total duration since no lunch/dinner breaks are assigned
        assert sessions[0].work_duration_minutes == 60, (
            f"Expected 60 minutes work (no lunch/dinner breaks), got {sessions[0].work_duration_minutes}"
        )

    def test_lunch_break_assignment(self):
        """As a user I want lunch breaks assigned for long sessions, so I can track work time accurately.
        Technical: Sessions starting before 10:00 and ending after 14:00 should get lunch breaks.
        Validation: Test that a 9:00-15:00 session gets a lunch break.
        """
        # Create session that spans lunch time
        events = [
            SystemEvent(
                datetime="5/9/2025 9:00:00 AM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39000",
            ),
            SystemEvent(
                datetime="5/9/2025 3:00:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39001",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 session with lunch break
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        assert sessions[0].lunch_break is not None, "Session should have lunch break"
        assert sessions[0].dinner_break is None, "Session should not have dinner break"
        # Work duration should be total duration minus 30 minutes for lunch
        assert sessions[0].work_duration_minutes == 330, (
            f"Expected 330 minutes work (360 - 30 lunch), got {sessions[0].work_duration_minutes}"
        )

    def test_dinner_break_assignment(self):
        """As a user I want dinner breaks assigned for long sessions, so I can track work time accurately.
        Technical: Sessions starting before 16:00 and ending after 20:00 should get dinner breaks.
        Validation: Test that a 15:00-21:00 session gets a dinner break.
        """
        # Create session that spans dinner time
        events = [
            SystemEvent(
                datetime="5/9/2025 3:00:00 PM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39000",
            ),
            SystemEvent(
                datetime="5/9/2025 9:00:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39001",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 session with dinner break
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        assert sessions[0].lunch_break is None, "Session should not have lunch break"
        assert sessions[0].dinner_break is not None, "Session should have dinner break"
        # Work duration should be total duration minus 45 minutes for dinner
        assert sessions[0].work_duration_minutes == 315, (
            f"Expected 315 minutes work (360 - 45 dinner), got {sessions[0].work_duration_minutes}"
        )

    def test_both_lunch_and_dinner_breaks(self):
        """As a user I want both lunch and dinner breaks assigned for very long sessions, so I can track work time accurately.
        Technical: Sessions starting before 10:00 and ending after 20:00 should get both breaks.
        Validation: Test that a 9:00-21:00 session gets both lunch and dinner breaks.
        """
        # Create session that spans both lunch and dinner time
        events = [
            SystemEvent(
                datetime="5/9/2025 9:00:00 AM",
                event_id="7001",
                event_type="User logon notification",
                username="piete",
                message="User Logon Notification",
                record_id="39000",
            ),
            SystemEvent(
                datetime="5/9/2025 9:00:00 PM",
                event_id="7002",
                event_type="User logoff notification",
                username="piete",
                message="User Logoff Notification",
                record_id="39001",
            ),
        ]

        detector = SessionDetector()
        sessions = detector.detect_sessions(events)

        # Should have 1 session with both breaks
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        assert sessions[0].lunch_break is not None, "Session should have lunch break"
        assert sessions[0].dinner_break is not None, "Session should have dinner break"
        # Work duration should be total duration minus 75 minutes for both breaks
        assert sessions[0].work_duration_minutes == 645, (
            f"Expected 645 minutes work (720 - 30 lunch - 45 dinner), got {sessions[0].work_duration_minutes}"
        )
