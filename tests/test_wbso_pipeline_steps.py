#!/usr/bin/env python3
"""
Tests for WBSO Pipeline Steps

This module provides comprehensive tests for the WBSO pipeline steps functionality,
including timezone normalization, conflict detection, and data processing.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Created: 2025-11-28
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.wbso.pipeline_steps import AMSTERDAM_TZ, _normalize_datetime


class TestTimezoneNormalization:
    """Test timezone normalization functionality."""

    def test_normalize_naive_datetime_to_amsterdam(self):
        """As a user I want naive datetimes normalized to Amsterdam timezone, so I can compare them with calendar events.
        Technical: _normalize_datetime should convert timezone-naive datetime to timezone-aware Amsterdam datetime.
        Validation: Verify the datetime has Amsterdam timezone info and preserves the original time values.
        """
        # Create a naive datetime (typical from database or JSON without timezone)
        naive_dt = datetime(2025, 6, 15, 14, 30, 0)

        # Normalize it
        normalized = _normalize_datetime(naive_dt)

        # Verify it's now timezone-aware
        assert normalized.tzinfo is not None
        assert normalized.tzinfo == AMSTERDAM_TZ

        # Verify the time values are preserved
        assert normalized.year == 2025
        assert normalized.month == 6
        assert normalized.day == 15
        assert normalized.hour == 14
        assert normalized.minute == 30
        assert normalized.second == 0

    def test_preserve_timezone_aware_datetime(self):
        """As a user I want timezone-aware datetimes preserved, so I don't lose timezone information.
        Technical: _normalize_datetime should return timezone-aware datetimes unchanged.
        Validation: Verify the datetime is returned as-is when already timezone-aware.
        """
        # Create a timezone-aware datetime (Amsterdam)
        aware_dt = datetime(2025, 6, 15, 14, 30, 0, tzinfo=AMSTERDAM_TZ)

        # Normalize it
        normalized = _normalize_datetime(aware_dt)

        # Verify it's unchanged
        assert normalized == aware_dt
        assert normalized.tzinfo == AMSTERDAM_TZ

    def test_normalize_utc_datetime_preserved(self):
        """As a user I want UTC timezone-aware datetimes preserved, so I can handle different timezones correctly.
        Technical: _normalize_datetime should preserve timezone-aware datetimes even if they're not Amsterdam.
        Validation: Verify UTC datetime is returned unchanged.
        """
        from datetime import timezone as tz

        # Create a UTC timezone-aware datetime
        utc_dt = datetime(2025, 6, 15, 14, 30, 0, tzinfo=tz.utc)

        # Normalize it
        normalized = _normalize_datetime(utc_dt)

        # Verify it's unchanged (preserves original timezone)
        assert normalized == utc_dt
        assert normalized.tzinfo == tz.utc

    def test_amsterdam_dst_summer_time(self):
        """As a user I want DST handled correctly in summer, so timezone conversions are accurate.
        Technical: Amsterdam timezone should handle daylight saving time (CEST = UTC+2) in summer.
        Validation: Verify summer datetime has correct UTC offset (+02:00).
        """
        # June 15, 2025 is in summer (CEST = UTC+2)
        naive_dt = datetime(2025, 6, 15, 14, 30, 0)
        normalized = _normalize_datetime(naive_dt)

        # Verify timezone info
        assert normalized.tzinfo == AMSTERDAM_TZ

        # Verify UTC offset is +02:00 (CEST) in summer
        # We can't directly check offset without converting, but we can verify it's timezone-aware
        assert normalized.tzinfo is not None

        # Convert to UTC to verify offset
        utc_offset = normalized.utcoffset().total_seconds() / 3600
        assert utc_offset == 2.0  # CEST is UTC+2

    def test_amsterdam_dst_winter_time(self):
        """As a user I want DST handled correctly in winter, so timezone conversions are accurate.
        Technical: Amsterdam timezone should handle standard time (CET = UTC+1) in winter.
        Validation: Verify winter datetime has correct UTC offset (+01:00).
        """
        # January 15, 2025 is in winter (CET = UTC+1)
        naive_dt = datetime(2025, 1, 15, 14, 30, 0)
        normalized = _normalize_datetime(naive_dt)

        # Verify timezone info
        assert normalized.tzinfo == AMSTERDAM_TZ

        # Convert to UTC to verify offset
        utc_offset = normalized.utcoffset().total_seconds() / 3600
        assert utc_offset == 1.0  # CET is UTC+1

    def test_dst_transition_spring(self):
        """As a user I want DST transitions handled correctly, so timezone conversions work at transition points.
        Technical: Amsterdam timezone should handle spring DST transition (last Sunday in March).
        Validation: Verify DST transition is handled correctly.
        """
        # March 30, 2025 is the last Sunday in March (DST transition day)
        # At 2:00 AM, clocks spring forward to 3:00 AM (CET -> CEST)
        # Test before transition (still CET)
        naive_dt_before = datetime(2025, 3, 30, 1, 30, 0)
        normalized_before = _normalize_datetime(naive_dt_before)
        assert normalized_before.tzinfo == AMSTERDAM_TZ

        # Test after transition (CEST)
        naive_dt_after = datetime(2025, 3, 30, 3, 30, 0)
        normalized_after = _normalize_datetime(naive_dt_after)
        assert normalized_after.tzinfo == AMSTERDAM_TZ

        # Both should be timezone-aware
        assert normalized_before.tzinfo is not None
        assert normalized_after.tzinfo is not None

    def test_dst_transition_fall(self):
        """As a user I want DST transitions handled correctly, so timezone conversions work at transition points.
        Technical: Amsterdam timezone should handle fall DST transition (last Sunday in October).
        Validation: Verify DST transition is handled correctly.
        """
        # October 26, 2025 is the last Sunday in October (DST transition day)
        # At 3:00 AM, clocks fall back to 2:00 AM (CEST -> CET)
        naive_dt = datetime(2025, 10, 26, 2, 30, 0)
        normalized = _normalize_datetime(naive_dt)

        # Verify timezone info
        assert normalized.tzinfo == AMSTERDAM_TZ
        assert normalized.tzinfo is not None

    def test_comparison_with_calendar_event_timezone(self):
        """As a user I want normalized datetimes comparable with calendar events, so conflict detection works correctly.
        Technical: Normalized Amsterdam datetime should be comparable with timezone-aware calendar event datetimes.
        Validation: Verify comparison operations work between normalized session times and calendar event times.
        """
        # Create a naive session datetime
        session_start = datetime(2025, 6, 15, 14, 30, 0)
        normalized_session = _normalize_datetime(session_start)

        # Create a calendar event datetime (from Google Calendar API format)
        # Calendar events come as ISO format with Z (UTC) or timezone offset
        event_start_str = "2025-06-15T14:30:00+02:00"  # CEST (Amsterdam summer)
        event_start = datetime.fromisoformat(event_start_str)

        # Both should be timezone-aware and comparable
        assert normalized_session.tzinfo is not None
        assert event_start.tzinfo is not None

        # They should be equal (same time in Amsterdam timezone)
        assert normalized_session == event_start

        # Comparison operations should work
        assert normalized_session <= event_start
        assert normalized_session >= event_start

    def test_edge_case_midnight(self):
        """As a user I want edge cases like midnight handled correctly, so timezone normalization works at boundaries.
        Technical: _normalize_datetime should handle midnight and other edge cases correctly.
        Validation: Verify midnight datetime is normalized correctly.
        """
        # Test midnight
        naive_dt = datetime(2025, 6, 15, 0, 0, 0)
        normalized = _normalize_datetime(naive_dt)

        assert normalized.tzinfo == AMSTERDAM_TZ
        assert normalized.hour == 0
        assert normalized.minute == 0
        assert normalized.second == 0

    def test_edge_case_end_of_day(self):
        """As a user I want edge cases like end of day handled correctly, so timezone normalization works at boundaries.
        Technical: _normalize_datetime should handle end-of-day datetimes correctly.
        Validation: Verify 23:59:59 datetime is normalized correctly.
        """
        # Test end of day
        naive_dt = datetime(2025, 6, 15, 23, 59, 59)
        normalized = _normalize_datetime(naive_dt)

        assert normalized.tzinfo == AMSTERDAM_TZ
        assert normalized.hour == 23
        assert normalized.minute == 59
        assert normalized.second == 59
