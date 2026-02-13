#!/usr/bin/env python3
"""
Test suite for CSV commit data processing functionality.

This module tests the process_commit_csvs.py script functionality
for WBSO hours registration and work block analysis.
"""


# Import the processing functions
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "docs" / "project" / "hours" / "scripts"))

from process_commit_csvs import extract_repo_name, generate_metadata, is_wbso_author, is_wbso_commit, parse_datetime_to_iso


class TestCommitCSVProcessing(unittest.TestCase):
    """Test cases for CSV commit data processing functionality."""

    def test_parse_datetime_to_iso_with_timezone(self):
        """As a user I want datetime parsing to handle timezone information correctly, so I can process commits from different time zones.
        Technical: Parse datetime strings with timezone offset to ISO 8601 format.
        Validation: Test various timezone formats and edge cases.
        """
        # Test with timezone
        result = parse_datetime_to_iso("2025-05-30 20:33:36 +0200")
        self.assertEqual(result, "2025-05-30T20:33:36+02:00")

        # Test without timezone
        result = parse_datetime_to_iso("2025-05-30 20:33:36")
        self.assertEqual(result, "2025-05-30T20:33:36")

        # Test invalid format
        result = parse_datetime_to_iso("invalid-date")
        self.assertIsNone(result)

    def test_extract_repo_name(self):
        """As a user I want repository names extracted from CSV filenames, so I can identify which project each commit belongs to.
        Technical: Extract repository name from CSV filename by removing .csv extension.
        Validation: Test various filename formats and edge cases.
        """
        self.assertEqual(extract_repo_name("on_prem_rag.csv"), "on_prem_rag")
        self.assertEqual(extract_repo_name("healthcare-aigent.csv"), "healthcare-aigent")
        self.assertEqual(extract_repo_name("my_chat_gpt.csv"), "my_chat_gpt")
        self.assertEqual(extract_repo_name("WBSO-AICM-2025-01.csv"), "WBSO-AICM-2025-01")

    def test_is_wbso_author(self):
        """As a user I want WBSO authors identified correctly, so I can filter commits by the WBSO holder.
        Technical: Case-insensitive matching for 'kuppens' in author field to identify WBSO holder.
        Validation: Test various author name formats and case variations.
        """
        # Test positive cases
        self.assertTrue(is_wbso_author("Pieter Kuppens"))
        self.assertTrue(is_wbso_author("pkuppens"))
        self.assertTrue(is_wbso_author("Kuppens, Pieter"))
        self.assertTrue(is_wbso_author("P. Kuppens"))

        # Test negative cases
        self.assertFalse(is_wbso_author("John Doe"))
        self.assertFalse(is_wbso_author("Jane Smith"))
        self.assertFalse(is_wbso_author(""))
        self.assertFalse(is_wbso_author("john.doe@example.com"))  # Email without kuppens

    def test_is_wbso_commit(self):
        """As a user I want WBSO eligible commits identified correctly, so I can track work eligible for tax deduction.
        Technical: Check both author (WBSO holder) AND timestamp >= 2025-06-01 for WBSO eligibility.
        Validation: Test various author and date combinations.
        """
        # Test positive cases (WBSO author + eligible date)
        self.assertTrue(is_wbso_commit("Pieter Kuppens", "2025-06-01T10:00:00+02:00"))
        self.assertTrue(is_wbso_commit("pkuppens", "2025-07-15T14:30:00+02:00"))
        self.assertTrue(is_wbso_commit("Kuppens, Pieter", "2025-09-30T09:00:00+02:00"))

        # Test negative cases (non-WBSO author)
        self.assertFalse(is_wbso_commit("John Doe", "2025-06-01T10:00:00+02:00"))
        self.assertFalse(is_wbso_commit("Jane Smith", "2025-07-15T14:30:00+02:00"))

        # Test negative cases (WBSO author but before WBSO start date)
        self.assertFalse(is_wbso_commit("Pieter Kuppens", "2025-05-31T23:59:59+02:00"))
        self.assertFalse(is_wbso_commit("pkuppens", "2024-12-31T10:00:00+02:00"))

        # Test edge case (exactly at WBSO start date)
        self.assertTrue(is_wbso_commit("Pieter Kuppens", "2025-06-01T00:00:00+00:00"))

    def test_generate_metadata(self):
        """As a user I want metadata generated from commit data, so I can understand the scope and statistics of processed commits.
        Technical: Generate summary statistics including total commits, WBSO commits, repositories, and date range.
        Validation: Test with various commit datasets and edge cases.
        """
        # Test with sample commits (all WBSO authors, but only some WBSO eligible by date)
        commits = [
            {
                "timestamp": "2025-05-30T20:33:36+02:00",
                "repo_name": "on_prem_rag",
                "author": "Pieter Kuppens",
                "is_wbso": False,  # Before WBSO start date
            },
            {
                "timestamp": "2025-06-01T10:15:00+02:00",
                "repo_name": "healthcare-aigent",
                "author": "Pieter Kuppens",
                "is_wbso": True,  # On WBSO start date
            },
            {
                "timestamp": "2025-07-15T14:30:00+02:00",
                "repo_name": "on_prem_rag",
                "author": "pkuppens",
                "is_wbso": True,  # After WBSO start date
            },
        ]

        metadata = generate_metadata(commits)

        self.assertEqual(metadata["total_commits"], 3)  # All WBSO authors
        self.assertEqual(metadata["wbso_commits"], 2)  # Only 2 eligible by date
        self.assertEqual(set(metadata["repositories"]), {"on_prem_rag", "healthcare-aigent"})
        self.assertEqual(metadata["date_range"]["start"], "2025-05-30T20:33:36+02:00")
        self.assertEqual(metadata["date_range"]["end"], "2025-07-15T14:30:00+02:00")

    def test_generate_metadata_empty_commits(self):
        """As a user I want metadata generation to handle empty commit lists gracefully, so the system doesn't crash with no data.
        Technical: Handle empty commits list and return appropriate default values.
        Validation: Test with empty list and verify default metadata structure.
        """
        metadata = generate_metadata([])

        self.assertEqual(metadata["total_commits"], 0)
        self.assertEqual(metadata["wbso_commits"], 0)
        self.assertEqual(metadata["repositories"], [])
        self.assertIsNone(metadata["date_range"]["start"])
        self.assertIsNone(metadata["date_range"]["end"])

    def test_generate_metadata_commits_without_timestamps(self):
        """As a user I want metadata generation to handle commits without timestamps, so the system is robust against malformed data.
        Technical: Handle commits with missing or None timestamp values.
        Validation: Test with commits having None timestamps and verify date range handling.
        """
        commits = [
            {"timestamp": "2025-05-30T20:33:36+02:00", "repo_name": "on_prem_rag", "author": "Pieter Kuppens", "is_wbso": True},
            {"timestamp": None, "repo_name": "healthcare-aigent", "author": "Pieter Kuppens", "is_wbso": True},
        ]

        metadata = generate_metadata(commits)

        self.assertEqual(metadata["total_commits"], 2)
        self.assertEqual(metadata["wbso_commits"], 2)
        self.assertEqual(metadata["date_range"]["start"], "2025-05-30T20:33:36+02:00")
        self.assertEqual(metadata["date_range"]["end"], "2025-05-30T20:33:36+02:00")


if __name__ == "__main__":
    unittest.main()
