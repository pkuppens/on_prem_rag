#!/usr/bin/env python3
"""
Tests for WBSO Calendar Event Data Models

This module provides comprehensive tests for the WBSO calendar event data models,
including validation, conversion, and data management functionality.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Created: 2025-10-19
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

from src.wbso.calendar_event import (
    WBSOSession,
    CalendarEvent,
    ValidationResult,
    WBSODataset,
)


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_validation_result_creation(self):
        """As a user I want to create validation results, so I can track data quality issues.
        Technical: ValidationResult should initialize with default values and allow customization.
        """
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.session_id == ""
        assert isinstance(result.validation_timestamp, datetime)

    def test_validation_result_with_custom_values(self):
        """As a user I want to create validation results with custom values, so I can track specific session issues.
        Technical: ValidationResult should accept custom values for all fields.
        """
        timestamp = datetime.now()
        result = ValidationResult(
            is_valid=False,
            errors=["Test error"],
            warnings=["Test warning"],
            session_id="test-session-001",
            validation_timestamp=timestamp,
        )
        assert result.is_valid is False
        assert result.errors == ["Test error"]
        assert result.warnings == ["Test warning"]
        assert result.session_id == "test-session-001"
        assert result.validation_timestamp == timestamp

    def test_add_error(self):
        """As a user I want to add errors to validation results, so I can track data quality issues.
        Technical: add_error method should append errors and set is_valid to False.
        """
        result = ValidationResult()
        result.add_error("Test error")
        assert result.errors == ["Test error"]
        assert result.is_valid is False

    def test_add_warning(self):
        """As a user I want to add warnings to validation results, so I can track non-critical issues.
        Technical: add_warning method should append warnings without affecting is_valid.
        """
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.warnings == ["Test warning"]
        assert result.is_valid is True

    def test_to_dict(self):
        """As a user I want to convert validation results to dictionaries, so I can serialize them.
        Technical: to_dict method should return a dictionary with all fields properly formatted.
        """
        result = ValidationResult(session_id="test-session-001")
        result.add_error("Test error")
        result.add_warning("Test warning")

        data = result.to_dict()
        assert data["is_valid"] is False
        assert data["errors"] == ["Test error"]
        assert data["warnings"] == ["Test warning"]
        assert data["session_id"] == "test-session-001"
        assert "validation_timestamp" in data


class TestWBSOSession:
    """Test WBSOSession dataclass functionality."""

    def test_wbso_session_creation(self):
        """As a user I want to create WBSO sessions, so I can track work activities.
        Technical: WBSOSession should initialize with all required fields.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        assert session.session_id == "test-session-001"
        assert session.start_time == start_time
        assert session.end_time == end_time
        assert session.work_hours == 8.0
        assert session.is_wbso is True
        assert session.wbso_category == "AI_FRAMEWORK"

    def test_wbso_session_validation_success(self):
        """As a user I want to validate WBSO sessions, so I can ensure data quality.
        Technical: validate method should return ValidationResult with is_valid=True for valid sessions.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
            repository_name="on_prem_rag",
            wbso_justification="Test R&D activity",
        )

        result = session.validate()
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_wbso_session_validation_errors(self):
        """As a user I want validation to catch errors, so I can fix data quality issues.
        Technical: validate method should return ValidationResult with errors for invalid sessions.
        """
        # Test missing required fields
        session = WBSOSession(
            session_id="",  # Empty session_id
            start_time=None,  # Missing start_time
            end_time=None,  # Missing end_time
            work_hours=None,  # Missing work_hours
            duration_hours=8.0,
            date="",  # Empty date
            session_type="",  # Empty session_type
            is_wbso=None,  # Missing is_wbso
            wbso_category="",  # Empty wbso_category
            is_synthetic=None,  # Missing is_synthetic
            commit_count=None,  # Missing commit_count
            source_type="",  # Empty source_type
        )

        result = session.validate()
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_wbso_session_time_validation(self):
        """As a user I want time validation, so I can ensure logical time ranges.
        Technical: validate method should check start_time < end_time and reasonable durations.
        """
        # Test start_time >= end_time
        start_time = datetime(2025, 10, 18, 17, 0, 0)
        end_time = datetime(2025, 10, 18, 9, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        result = session.validate()
        assert result.is_valid is False
        assert any("start_time must be before end_time" in error for error in result.errors)

    def test_wbso_session_hours_validation(self):
        """As a user I want hours validation, so I can ensure reasonable work hours.
        Technical: validate method should check work_hours <= duration_hours and reasonable values.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        # Test work_hours > duration_hours
        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=10.0,  # More than duration
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        result = session.validate()
        assert result.is_valid is False
        assert any("work_hours cannot exceed duration_hours" in error for error in result.errors)

    def test_wbso_session_category_validation(self):
        """As a user I want category validation, so I can ensure valid WBSO categories.
        Technical: validate method should check WBSO categories against valid list.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        # Test invalid WBSO category
        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="INVALID_CATEGORY",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        result = session.validate()
        assert result.is_valid is False
        assert any("Invalid WBSO category" in error for error in result.errors)

    def test_wbso_session_to_dict(self):
        """As a user I want to convert sessions to dictionaries, so I can serialize them.
        Technical: to_dict method should return a dictionary with all fields properly formatted.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        data = session.to_dict()
        assert data["session_id"] == "test-session-001"
        assert data["work_hours"] == 8.0
        assert data["is_wbso"] is True
        assert data["wbso_category"] == "AI_FRAMEWORK"
        assert "start_time" in data
        assert "end_time" in data

    def test_wbso_session_from_dict(self):
        """As a user I want to create sessions from dictionaries, so I can deserialize data.
        Technical: from_dict class method should create WBSOSession from dictionary data.
        """
        data = {
            "session_id": "test-session-001",
            "start_time": "2025-10-18T09:00:00",
            "end_time": "2025-10-18T17:00:00",
            "work_hours": 8.0,
            "duration_hours": 8.0,
            "date": "2025-10-18",
            "session_type": "full_day",
            "is_wbso": True,
            "wbso_category": "AI_FRAMEWORK",
            "is_synthetic": False,
            "commit_count": 5,
            "source_type": "real",
        }

        session = WBSOSession.from_dict(data)
        assert session.session_id == "test-session-001"
        assert session.work_hours == 8.0
        assert session.is_wbso is True
        assert session.wbso_category == "AI_FRAMEWORK"
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.end_time, datetime)

    def test_wbso_session_get_duration(self):
        """As a user I want to get session duration, so I can calculate time spans.
        Technical: get_duration method should return timedelta between start and end times.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        duration = session.get_duration()
        assert duration == timedelta(hours=8)


class TestCalendarEvent:
    """Test CalendarEvent dataclass functionality."""

    def test_calendar_event_creation(self):
        """As a user I want to create calendar events, so I can schedule WBSO activities.
        Technical: CalendarEvent should initialize with all required fields.
        """
        event = CalendarEvent(
            summary="Test WBSO Event",
            description="Test description",
            start={"dateTime": "2025-10-18T09:00:00", "timeZone": "Europe/Amsterdam"},
            end={"dateTime": "2025-10-18T17:00:00", "timeZone": "Europe/Amsterdam"},
        )

        assert event.summary == "Test WBSO Event"
        assert event.description == "Test description"
        assert event.start["dateTime"] == "2025-10-18T09:00:00"
        assert event.end["dateTime"] == "2025-10-18T17:00:00"

    def test_calendar_event_validation_success(self):
        """As a user I want to validate calendar events, so I can ensure proper formatting.
        Technical: validate method should return ValidationResult with is_valid=True for valid events.
        """
        event = CalendarEvent(
            summary="Test WBSO Event",
            description="Test description",
            start={"dateTime": "2025-10-18T09:00:00", "timeZone": "Europe/Amsterdam"},
            end={"dateTime": "2025-10-18T17:00:00", "timeZone": "Europe/Amsterdam"},
        )

        result = event.validate()
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_calendar_event_validation_errors(self):
        """As a user I want validation to catch errors, so I can fix event formatting issues.
        Technical: validate method should return ValidationResult with errors for invalid events.
        """
        # Test missing required fields
        event = CalendarEvent(
            summary="",  # Empty summary
            description="",  # Empty description
            start={},  # Missing dateTime and timeZone
            end={},  # Missing dateTime and timeZone
        )

        result = event.validate()
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_calendar_event_to_google_format(self):
        """As a user I want to convert events to Google Calendar format, so I can upload them.
        Technical: to_google_format method should return dictionary in Google Calendar API format.
        """
        event = CalendarEvent(
            summary="Test WBSO Event",
            description="Test description",
            start={"dateTime": "2025-10-18T09:00:00", "timeZone": "Europe/Amsterdam"},
            end={"dateTime": "2025-10-18T17:00:00", "timeZone": "Europe/Amsterdam"},
            color_id="1",
            location="Home Office",
        )

        google_format = event.to_google_format()
        assert google_format["summary"] == "Test WBSO Event"
        assert google_format["description"] == "Test description"
        assert google_format["colorId"] == "1"
        assert google_format["location"] == "Home Office"

    def test_calendar_event_from_wbso_session(self):
        """As a user I want to create calendar events from WBSO sessions, so I can schedule activities.
        Technical: from_wbso_session class method should create CalendarEvent from WBSOSession.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
            repository_name="on_prem_rag",
            wbso_justification="Test R&D activity",
        )

        event = CalendarEvent.from_wbso_session(session)
        assert "AI Framework Ontwikkeling" in event.summary
        assert "AI_FRAMEWORK" in event.description
        assert event.start["dateTime"] == "2025-10-18T09:00:00"
        assert event.end["dateTime"] == "2025-10-18T17:00:00"
        assert event.extended_properties["private"]["session_id"] == "test-session-001"


class TestWBSODataset:
    """Test WBSODataset class functionality."""

    def test_wbso_dataset_creation(self):
        """As a user I want to create WBSO datasets, so I can manage collections of sessions.
        Technical: WBSODataset should initialize with empty sessions list.
        """
        dataset = WBSODataset()
        assert dataset.sessions == []
        assert dataset.total_hours == 0.0
        assert dataset.wbso_hours == 0.0
        assert dataset.session_count == 0

    def test_wbso_dataset_load_from_json(self):
        """As a user I want to load sessions from JSON files, so I can import data.
        Technical: load_from_json method should parse JSON and create WBSOSession objects.
        """
        # Create temporary JSON file
        test_data = {
            "sessions": [
                {
                    "session_id": "test-session-001",
                    "start_time": "2025-10-18T09:00:00",
                    "end_time": "2025-10-18T17:00:00",
                    "work_hours": 8.0,
                    "duration_hours": 8.0,
                    "date": "2025-10-18",
                    "session_type": "full_day",
                    "is_wbso": True,
                    "wbso_category": "AI_FRAMEWORK",
                    "is_synthetic": False,
                    "commit_count": 5,
                    "source_type": "real",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            dataset = WBSODataset()
            dataset.load_from_json(temp_path)

            assert len(dataset.sessions) == 1
            assert dataset.sessions[0].session_id == "test-session-001"
            assert dataset.sessions[0].work_hours == 8.0
        finally:
            Path(temp_path).unlink()

    def test_wbso_dataset_validate_all(self):
        """As a user I want to validate all sessions, so I can check data quality.
        Technical: validate_all method should return list of ValidationResult objects.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
            repository_name="on_prem_rag",
            wbso_justification="Test R&D activity",
        )

        dataset = WBSODataset()
        dataset.sessions.append(session)

        results = dataset.validate_all()
        assert len(results) == 1
        assert results[0].is_valid is True

    def test_wbso_dataset_find_duplicates(self):
        """As a user I want to find duplicate sessions, so I can clean data.
        Technical: find_duplicates method should return dictionary with duplicate session_ids and datetime ranges.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        # Create duplicate sessions
        session1 = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        session2 = WBSOSession(
            session_id="test-session-001",  # Duplicate session_id
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        dataset = WBSODataset()
        dataset.sessions.extend([session1, session2])

        duplicates = dataset.find_duplicates()
        assert len(duplicates["session_ids"]) == 1
        assert "test-session-001" in duplicates["session_ids"]

    def test_wbso_dataset_find_overlaps(self):
        """As a user I want to find overlapping sessions, so I can detect scheduling conflicts.
        Technical: find_overlaps method should return list of overlapping session pairs.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        # Create overlapping sessions
        session1 = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        session2 = WBSOSession(
            session_id="test-session-002",
            start_time=datetime(2025, 10, 18, 13, 0, 0),  # Overlaps with session1
            end_time=datetime(2025, 10, 18, 21, 0, 0),
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        dataset = WBSODataset()
        dataset.sessions.extend([session1, session2])

        overlaps = dataset.find_overlaps()
        assert len(overlaps) == 1
        assert overlaps[0]["session1_id"] == "test-session-001"
        assert overlaps[0]["session2_id"] == "test-session-002"
        assert overlaps[0]["overlap_hours"] == 4.0  # 4 hours overlap

    def test_wbso_dataset_get_summary_stats(self):
        """As a user I want to get summary statistics, so I can understand the dataset.
        Technical: get_summary_stats method should return comprehensive statistics dictionary.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        dataset = WBSODataset()
        dataset.sessions.append(session)

        stats = dataset.get_summary_stats()
        assert stats["total_sessions"] == 1
        assert stats["wbso_sessions"] == 1
        assert stats["total_hours"] == 8.0
        assert stats["wbso_hours"] == 8.0
        assert "AI_FRAMEWORK" in stats["category_breakdown"]

    def test_wbso_dataset_export_to_json(self):
        """As a user I want to export datasets to JSON, so I can save processed data.
        Technical: export_to_json method should create JSON file with session data.
        """
        start_time = datetime(2025, 10, 18, 9, 0, 0)
        end_time = datetime(2025, 10, 18, 17, 0, 0)

        session = WBSOSession(
            session_id="test-session-001",
            start_time=start_time,
            end_time=end_time,
            work_hours=8.0,
            duration_hours=8.0,
            date="2025-10-18",
            session_type="full_day",
            is_wbso=True,
            wbso_category="AI_FRAMEWORK",
            is_synthetic=False,
            commit_count=5,
            source_type="real",
        )

        dataset = WBSODataset()
        dataset.sessions.append(session)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            dataset.export_to_json(temp_path)

            # Verify file was created and contains data
            assert Path(temp_path).exists()
            with open(temp_path, "r") as f:
                data = json.load(f)
                assert data["total_sessions"] == 1
                assert len(data["sessions"]) == 1
                assert data["sessions"][0]["session_id"] == "test-session-001"
        finally:
            Path(temp_path).unlink()
