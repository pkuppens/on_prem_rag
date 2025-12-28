#!/usr/bin/env python3
"""
Tests for WBSO Data Validation Module

This module provides comprehensive tests for the WBSO data validation functionality,
including duplicate detection, overlap analysis, and data quality checks.

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

from src.wbso.validation import WBSODataValidator
from src.wbso.calendar_event import WBSOSession, WBSODataset


class TestWBSODataValidator:
    """Test WBSODataValidator class functionality."""

    def test_validator_initialization(self):
        """As a user I want to initialize a validator, so I can validate WBSO data.
        Technical: WBSODataValidator should initialize with empty dataset and validation results.
        """
        data_dir = Path("/tmp/test_data")
        validator = WBSODataValidator(data_dir)

        assert validator.data_dir == data_dir
        assert isinstance(validator.dataset, WBSODataset)
        assert validator.dataset.sessions == []
        assert validator.validation_results == []
        assert validator.duplicates == {}
        assert validator.overlaps == []
        assert validator.audit_trail == {}

    def test_validate_duplicates_no_duplicates(self):
        """As a user I want to detect duplicates, so I can clean data quality issues.
        Technical: validate_duplicates should return empty results when no duplicates exist.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test sessions without duplicates
            start_time = datetime(2025, 10, 18, 9, 0, 0)
            end_time = datetime(2025, 10, 18, 17, 0, 0)

            session1 = WBSOSession(
                session_id="session-001",
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
                session_id="session-002",
                start_time=datetime(2025, 10, 19, 9, 0, 0),
                end_time=datetime(2025, 10, 19, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-19",
                session_type="full_day",
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=3,
                source_type="real",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.extend([session1, session2])

            result = validator.validate_duplicates()

            assert result["session_id_duplicates"] == 0
            assert result["datetime_duplicates"] == 0
            assert len(result["details"]["session_ids"]) == 0
            assert len(result["details"]["datetime_ranges"]) == 0

    def test_validate_duplicates_with_duplicates(self):
        """As a user I want to detect duplicate session IDs, so I can identify data quality issues.
        Technical: validate_duplicates should return duplicate session_ids when they exist.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test sessions with duplicates
            start_time = datetime(2025, 10, 18, 9, 0, 0)
            end_time = datetime(2025, 10, 18, 17, 0, 0)

            session1 = WBSOSession(
                session_id="session-001",
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
                session_id="session-001",  # Duplicate session_id
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

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.extend([session1, session2])

            result = validator.validate_duplicates()

            assert result["session_id_duplicates"] == 1
            assert "session-001" in result["details"]["session_ids"]

    def test_validate_time_ranges_valid_sessions(self):
        """As a user I want to validate time ranges, so I can ensure logical session timing.
        Technical: validate_time_ranges should return empty list when all sessions have valid time ranges.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test sessions with valid time ranges
            start_time = datetime(2025, 10, 18, 9, 0, 0)
            end_time = datetime(2025, 10, 18, 17, 0, 0)

            session = WBSOSession(
                session_id="session-001",
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

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            issues = validator.validate_time_ranges()

            assert len(issues) == 0

    def test_validate_time_ranges_invalid_sessions(self):
        """As a user I want to detect invalid time ranges, so I can fix data quality issues.
        Technical: validate_time_ranges should return issues when sessions have invalid time ranges.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test session with invalid time range (start >= end)
            start_time = datetime(2025, 10, 18, 17, 0, 0)
            end_time = datetime(2025, 10, 18, 9, 0, 0)

            session = WBSOSession(
                session_id="session-001",
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

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            issues = validator.validate_time_ranges()

            assert len(issues) == 1
            assert issues[0]["session_id"] == "session-001"
            assert issues[0]["issue"] == "start_time >= end_time"
            assert issues[0]["severity"] == "error"

    def test_validate_overlaps_no_overlaps(self):
        """As a user I want to detect overlapping sessions, so I can identify scheduling conflicts.
        Technical: validate_overlaps should return empty list when no overlaps exist.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test sessions without overlaps
            session1 = WBSOSession(
                session_id="session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
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
                session_id="session-002",
                start_time=datetime(2025, 10, 19, 9, 0, 0),
                end_time=datetime(2025, 10, 19, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-19",
                session_type="full_day",
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=3,
                source_type="real",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.extend([session1, session2])

            overlaps = validator.validate_overlaps()

            assert len(overlaps) == 0

    def test_validate_overlaps_with_overlaps(self):
        """As a user I want to detect overlapping sessions, so I can identify scheduling conflicts.
        Technical: validate_overlaps should return overlap information when overlaps exist.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test sessions with overlaps
            session1 = WBSOSession(
                session_id="session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
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
                session_id="session-002",
                start_time=datetime(2025, 10, 18, 13, 0, 0),  # Overlaps with session1
                end_time=datetime(2025, 10, 18, 21, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-18",
                session_type="full_day",
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=3,
                source_type="real",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.extend([session1, session2])

            overlaps = validator.validate_overlaps()

            assert len(overlaps) == 1
            assert overlaps[0]["session1_id"] == "session-001"
            assert overlaps[0]["session2_id"] == "session-002"
            assert overlaps[0]["overlap_hours"] == 4.0  # 4 hours overlap

    def test_validate_wbso_completeness_valid_sessions(self):
        """As a user I want to validate WBSO completeness, so I can ensure proper categorization.
        Technical: validate_wbso_completeness should return empty list when all WBSO sessions are complete.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test session with complete WBSO data
            session = WBSOSession(
                session_id="session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-18",
                session_type="full_day",
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=5,
                source_type="real",
                wbso_justification="Test R&D activity",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            issues = validator.validate_wbso_completeness()

            assert len(issues) == 0

    def test_validate_wbso_completeness_invalid_sessions(self):
        """As a user I want to detect incomplete WBSO sessions, so I can fix categorization issues.
        Technical: validate_wbso_completeness should return issues when WBSO sessions are incomplete.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test session with incomplete WBSO data
            session = WBSOSession(
                session_id="session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-18",
                session_type="full_day",
                is_wbso=True,
                wbso_category="INVALID_CATEGORY",  # Invalid category
                is_synthetic=False,
                commit_count=5,
                source_type="real",
                wbso_justification="",  # Missing justification
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            issues = validator.validate_wbso_completeness()

            assert len(issues) == 2  # Invalid category + missing justification
            assert any("Invalid WBSO category" in issue["issue"] for issue in issues)
            assert any("Missing WBSO justification" in issue["issue"] for issue in issues)

    def test_validate_data_quality_valid_sessions(self):
        """As a user I want to validate data quality, so I can ensure consistent data.
        Technical: validate_data_quality should return empty list when all sessions have good data quality.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test session with good data quality
            session = WBSOSession(
                session_id="session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-18",
                session_type="morning",  # Matches start time (9 AM)
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=5,
                source_type="real",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            issues = validator.validate_data_quality()

            assert len(issues) == 0

    def test_validate_data_quality_invalid_sessions(self):
        """As a user I want to detect data quality issues, so I can fix inconsistent data.
        Technical: validate_data_quality should return issues when sessions have data quality problems.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test session with data quality issues
            session = WBSOSession(
                session_id="",  # Missing session_id
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
                work_hours=10.0,  # More than duration_hours
                duration_hours=8.0,
                date="2025-10-18",
                session_type="evening",  # Doesn't match start time (9 AM)
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=5,
                source_type="real",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            issues = validator.validate_data_quality()

            assert len(issues) >= 2  # Missing session_id + work_hours > duration_hours
            assert any("Missing session_id" in issue["issue"] for issue in issues)
            assert any("work_hours > duration_hours" in issue["issue"] for issue in issues)

    def test_generate_hours_audit_trail(self):
        """As a user I want to generate hours audit trail, so I can verify WBSO hours calculations.
        Technical: generate_hours_audit_trail should return comprehensive audit information.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test sessions
            wbso_session = WBSOSession(
                session_id="wbso-session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
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

            non_wbso_session = WBSOSession(
                session_id="non-wbso-session-001",
                start_time=datetime(2025, 10, 19, 9, 0, 0),
                end_time=datetime(2025, 10, 19, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-19",
                session_type="full_day",
                is_wbso=False,
                wbso_category="",
                is_synthetic=False,
                commit_count=3,
                source_type="real",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.extend([wbso_session, non_wbso_session])

            audit_trail = validator.generate_hours_audit_trail()

            assert audit_trail["total_sessions"] == 2
            assert audit_trail["wbso_sessions"] == 1
            assert audit_trail["total_hours"] == 16.0
            assert audit_trail["wbso_hours"] == 8.0
            assert audit_trail["wbso_percentage"] == 50.0
            assert "AI_FRAMEWORK" in audit_trail["category_breakdown"]
            assert len(audit_trail["evidence_trail"]) == 1  # Only WBSO sessions

    def test_run_comprehensive_validation(self):
        """As a user I want to run comprehensive validation, so I can check all data quality aspects.
        Technical: run_comprehensive_validation should return complete validation results.
        """
        # Create test data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            # Create test session
            session = WBSOSession(
                session_id="session-001",
                start_time=datetime(2025, 10, 18, 9, 0, 0),
                end_time=datetime(2025, 10, 18, 17, 0, 0),
                work_hours=8.0,
                duration_hours=8.0,
                date="2025-10-18",
                session_type="full_day",
                is_wbso=True,
                wbso_category="AI_FRAMEWORK",
                is_synthetic=False,
                commit_count=5,
                source_type="real",
                wbso_justification="Test R&D activity",
            )

            validator = WBSODataValidator(data_dir)
            validator.dataset.sessions.append(session)

            results = validator.run_comprehensive_validation()

            assert "validation_timestamp" in results
            assert "data_sources_loaded" in results
            assert "duplicates" in results
            assert "time_ranges" in results
            assert "overlaps" in results
            assert "wbso_completeness" in results
            assert "data_quality" in results
            assert "hours_audit" in results
            assert "summary" in results

            summary = results["summary"]
            assert "total_errors" in summary
            assert "total_warnings" in summary
            assert "validation_passed" in summary
            assert "ready_for_upload" in summary
