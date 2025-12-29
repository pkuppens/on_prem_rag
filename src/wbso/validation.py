#!/usr/bin/env python3
"""
WBSO Calendar Data Validation and Cleaning Module

This module provides comprehensive validation for WBSO calendar data including
duplicates, overlaps, data quality, and generates comprehensive audit trails.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Created: 2025-10-18
"""

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .calendar_event import ValidationResult, WBSODataset, WBSOSession
from .logging_config import get_logger

logger = get_logger("validation")


class WBSODataValidator:
    """Comprehensive validator for WBSO calendar data."""

    def __init__(self, data_dir: Path):
        """Initialize validator with data directory."""
        self.data_dir = Path(data_dir)
        self.dataset = WBSODataset()
        self.validation_results = []
        self.duplicates = {}
        self.overlaps = []
        self.audit_trail = {}

    def load_all_data_sources(self) -> None:
        """Load and cross-reference all data sources."""
        logger.info("Loading all data sources...")

        # Load work_log_complete.json (249 sessions)
        work_log_path = self.data_dir / "work_log_complete.json"
        if work_log_path.exists():
            logger.info(f"Loading work log from {work_log_path}")
            self.dataset.load_from_json(work_log_path)
        else:
            logger.warning(f"Work log not found: {work_log_path}")

        # Load wbso_calendar_events.json (94 WBSO events)
        wbso_events_path = self.data_dir / "wbso_calendar_events.json"
        if wbso_events_path.exists():
            logger.info(f"Loading WBSO events from {wbso_events_path}")
            # This might contain calendar events, not sessions
            with open(wbso_events_path, "r", encoding="utf-8") as f:
                wbso_data = json.load(f)
            logger.info(f"WBSO events data structure: {type(wbso_data)}")

        # Load synthetic_sessions.json (57 synthetic sessions)
        synthetic_path = self.data_dir / "synthetic_sessions.json"
        if synthetic_path.exists():
            logger.info(f"Loading synthetic sessions from {synthetic_path}")
            # Add synthetic sessions to dataset
            synthetic_dataset = WBSODataset()
            synthetic_dataset.load_from_json(synthetic_path)
            self.dataset.sessions.extend(synthetic_dataset.sessions)

        logger.info(f"Total sessions loaded: {len(self.dataset.sessions)}")

    def validate_duplicates(self) -> Dict[str, Any]:
        """Detect and report duplicate session_ids and datetime ranges."""
        logger.info("Checking for duplicates...")

        self.duplicates = self.dataset.find_duplicates()

        duplicate_report = {
            "session_id_duplicates": len(self.duplicates["session_ids"]),
            "datetime_duplicates": len(self.duplicates["datetime_ranges"]),
            "details": self.duplicates,
        }

        if self.duplicates["session_ids"]:
            logger.warning(f"Found {len(self.duplicates['session_ids'])} duplicate session IDs")
        if self.duplicates["datetime_ranges"]:
            logger.warning(f"Found {len(self.duplicates['datetime_ranges'])} duplicate datetime ranges")

        return duplicate_report

    def validate_time_ranges(self) -> List[Dict[str, Any]]:
        """Validate time ranges and detect issues."""
        logger.info("Validating time ranges...")

        time_issues = []

        for session in self.dataset.sessions:
            if not session.start_time or not session.end_time:
                time_issues.append(
                    {"session_id": session.session_id, "issue": "Missing start_time or end_time", "severity": "error"}
                )
                continue

            # Check start_time < end_time
            if session.start_time >= session.end_time:
                time_issues.append(
                    {
                        "session_id": session.session_id,
                        "issue": "start_time >= end_time",
                        "start_time": session.start_time.isoformat(),
                        "end_time": session.end_time.isoformat(),
                        "severity": "error",
                    }
                )

            # Check for impossible durations (>24 hours)
            duration = session.end_time - session.start_time
            if duration.total_seconds() > 24 * 3600:
                time_issues.append(
                    {
                        "session_id": session.session_id,
                        "issue": "Duration exceeds 24 hours",
                        "duration_hours": duration.total_seconds() / 3600,
                        "severity": "error",
                    }
                )

            # Check for sessions crossing midnight improperly
            if session.start_time.date() != session.end_time.date():
                if session.session_type not in ["full_day", "evening"]:
                    time_issues.append(
                        {
                            "session_id": session.session_id,
                            "issue": "Session crosses midnight but type doesn't allow it",
                            "session_type": session.session_type,
                            "severity": "warning",
                        }
                    )

        logger.info(f"Found {len(time_issues)} time range issues")
        return time_issues

    def validate_overlaps(self) -> List[Dict[str, Any]]:
        """Find overlapping WBSO sessions."""
        logger.info("Checking for session overlaps...")

        self.overlaps = self.dataset.find_overlaps()

        critical_overlaps = [o for o in self.overlaps if o["severity"] == "critical"]
        warning_overlaps = [o for o in self.overlaps if o["severity"] == "warning"]

        logger.info(f"Found {len(critical_overlaps)} critical overlaps and {len(warning_overlaps)} warning overlaps")

        return self.overlaps

    def validate_wbso_completeness(self) -> List[Dict[str, Any]]:
        """Validate WBSO completeness and categorization."""
        logger.info("Validating WBSO completeness...")

        wbso_issues = []
        valid_categories = ["AI_FRAMEWORK", "ACCESS_CONTROL", "PRIVACY_CLOUD", "AUDIT_LOGGING", "DATA_INTEGRITY", "GENERAL_RD"]

        for session in self.dataset.sessions:
            if session.is_wbso:
                # Check for missing WBSO category
                if not session.wbso_category:
                    wbso_issues.append({"session_id": session.session_id, "issue": "Missing WBSO category", "severity": "error"})
                elif session.wbso_category not in valid_categories:
                    wbso_issues.append(
                        {
                            "session_id": session.session_id,
                            "issue": f"Invalid WBSO category: {session.wbso_category}",
                            "severity": "error",
                        }
                    )

                # Check for missing justification
                if not session.wbso_justification:
                    wbso_issues.append(
                        {"session_id": session.session_id, "issue": "Missing WBSO justification", "severity": "error"}
                    )

        logger.info(f"Found {len(wbso_issues)} WBSO completeness issues")
        return wbso_issues

    def validate_data_quality(self) -> List[Dict[str, Any]]:
        """Check for data quality issues."""
        logger.info("Validating data quality...")

        quality_issues = []

        for session in self.dataset.sessions:
            # Check for missing required fields
            if not session.session_id:
                quality_issues.append({"session_id": session.session_id, "issue": "Missing session_id", "severity": "error"})

            # Check work_hours <= duration_hours
            if session.work_hours > session.duration_hours:
                quality_issues.append(
                    {
                        "session_id": session.session_id,
                        "issue": "work_hours > duration_hours",
                        "work_hours": session.work_hours,
                        "duration_hours": session.duration_hours,
                        "severity": "error",
                    }
                )

            # Check session_type matches time of day
            if session.start_time:
                hour = session.start_time.hour
                if session.session_type == "morning" and not (6 <= hour < 12):
                    quality_issues.append(
                        {
                            "session_id": session.session_id,
                            "issue": "session_type 'morning' but start hour is not 6-12",
                            "start_hour": hour,
                            "session_type": session.session_type,
                            "severity": "warning",
                        }
                    )
                elif session.session_type == "afternoon" and not (12 <= hour < 18):
                    quality_issues.append(
                        {
                            "session_id": session.session_id,
                            "issue": "session_type 'afternoon' but start hour is not 12-18",
                            "start_hour": hour,
                            "session_type": session.session_type,
                            "severity": "warning",
                        }
                    )
                elif session.session_type == "evening" and not (18 <= hour < 24):
                    quality_issues.append(
                        {
                            "session_id": session.session_id,
                            "issue": "session_type 'evening' but start hour is not 18-24",
                            "start_hour": hour,
                            "session_type": session.session_type,
                            "severity": "warning",
                        }
                    )

        logger.info(f"Found {len(quality_issues)} data quality issues")
        return quality_issues

    def generate_hours_audit_trail(self) -> Dict[str, Any]:
        """Generate comprehensive hours audit trail."""
        logger.info("Generating hours audit trail...")

        # Calculate totals
        total_sessions = len(self.dataset.sessions)
        wbso_sessions = [s for s in self.dataset.sessions if s.is_wbso]
        real_sessions = [s for s in self.dataset.sessions if s.source_type == "real"]
        synthetic_sessions = [s for s in self.dataset.sessions if s.source_type == "synthetic"]

        total_hours = sum(s.work_hours for s in self.dataset.sessions)
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

        # Generate evidence trail
        evidence_trail = []
        for session in wbso_sessions:
            evidence_trail.append(
                {
                    "session_id": session.session_id,
                    "date": session.date,
                    "start_time": session.start_time.isoformat() if session.start_time else None,
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "work_hours": session.work_hours,
                    "wbso_category": session.wbso_category,
                    "source_type": session.source_type,
                    "is_synthetic": session.is_synthetic,
                    "commit_count": session.commit_count,
                    "confidence_score": session.confidence_score,
                    "evidence_source": "system_events" if session.source_type == "real" else "synthetic_from_commits",
                }
            )

        audit_trail = {
            "calculation_timestamp": datetime.now().isoformat(),
            "total_sessions": total_sessions,
            "wbso_sessions": len(wbso_sessions),
            "real_sessions": len(real_sessions),
            "synthetic_sessions": len(synthetic_sessions),
            "total_hours": total_hours,
            "wbso_hours": wbso_hours,
            "real_hours": real_hours,
            "synthetic_hours": synthetic_hours,
            "wbso_percentage": (wbso_hours / total_hours * 100) if total_hours > 0 else 0,
            "category_breakdown": category_breakdown,
            "evidence_trail": evidence_trail,
            "claim_validation": {
                "claimed_hours": 438.27,
                "calculated_hours": wbso_hours,
                "difference": abs(438.27 - wbso_hours),
                "within_tolerance": abs(438.27 - wbso_hours) < 0.1,
            },
        }

        self.audit_trail = audit_trail
        logger.info(f"Hours audit: {wbso_hours:.2f} WBSO hours from {len(wbso_sessions)} sessions")

        return audit_trail

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks and generate comprehensive report."""
        logger.info("Starting comprehensive validation...")

        # Load all data
        self.load_all_data_sources()

        # Run all validation checks
        validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "data_sources_loaded": len(self.dataset.sessions),
            "duplicates": self.validate_duplicates(),
            "time_ranges": self.validate_time_ranges(),
            "overlaps": self.validate_overlaps(),
            "wbso_completeness": self.validate_wbso_completeness(),
            "data_quality": self.validate_data_quality(),
            "hours_audit": self.generate_hours_audit_trail(),
        }

        # Calculate summary statistics
        total_errors = (
            validation_results["duplicates"]["session_id_duplicates"]
            + validation_results["duplicates"]["datetime_duplicates"]
            + len([i for i in validation_results["time_ranges"] if i["severity"] == "error"])
            + len([i for i in validation_results["overlaps"] if i["severity"] == "critical"])
            + len([i for i in validation_results["wbso_completeness"] if i["severity"] == "error"])
            + len([i for i in validation_results["data_quality"] if i["severity"] == "error"])
        )

        total_warnings = (
            len([i for i in validation_results["time_ranges"] if i["severity"] == "warning"])
            + len([i for i in validation_results["overlaps"] if i["severity"] == "warning"])
            + len([i for i in validation_results["wbso_completeness"] if i["severity"] == "warning"])
            + len([i for i in validation_results["data_quality"] if i["severity"] == "warning"])
        )

        validation_results["summary"] = {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "validation_passed": total_errors == 0,
            "ready_for_upload": total_errors == 0 and total_warnings < 10,
        }

        logger.info(f"Validation complete: {total_errors} errors, {total_warnings} warnings")
        return validation_results

    def export_validation_reports(self, output_dir: Path) -> None:
        """Export all validation reports to files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Export validation report
        validation_report_path = output_dir / "validation_report.json"
        with open(validation_report_path, "w", encoding="utf-8") as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        logger.info(f"Validation report exported to {validation_report_path}")

        # Export hours audit trail
        audit_trail_path = output_dir / "hours_audit_trail.json"
        with open(audit_trail_path, "w", encoding="utf-8") as f:
            json.dump(self.audit_trail, f, indent=2, ensure_ascii=False)
        logger.info(f"Hours audit trail exported to {audit_trail_path}")

        # Export duplicate sessions
        duplicates_path = output_dir / "duplicate_sessions.json"
        with open(duplicates_path, "w", encoding="utf-8") as f:
            json.dump(self.duplicates, f, indent=2, ensure_ascii=False)
        logger.info(f"Duplicate sessions exported to {duplicates_path}")

        # Export overlap matrix as CSV
        if self.overlaps:
            overlap_path = output_dir / "overlap_matrix.csv"
            with open(overlap_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.overlaps[0].keys())
                writer.writeheader()
                writer.writerows(self.overlaps)
            logger.info(f"Overlap matrix exported to {overlap_path}")

        # Export cleaned dataset
        cleaned_dataset_path = output_dir / "cleaned_dataset.json"
        self.dataset.export_to_json(cleaned_dataset_path)
        logger.info(f"Cleaned dataset exported to {cleaned_dataset_path}")

        # Generate human-readable summary
        summary_path = output_dir / "validation_summary.md"
        self.generate_summary_report(summary_path)
        logger.info(f"Validation summary exported to {summary_path}")

    def generate_summary_report(self, output_path: Path) -> None:
        """Generate human-readable validation summary."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# WBSO Data Validation Summary\n\n")
            f.write(f"**Validation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Summary statistics
            summary = self.validation_results["summary"]
            f.write("## Summary\n\n")
            f.write(f"- **Total Sessions**: {self.validation_results['data_sources_loaded']}\n")
            f.write(f"- **Total Errors**: {summary['total_errors']}\n")
            f.write(f"- **Total Warnings**: {summary['total_warnings']}\n")
            f.write(f"- **Validation Passed**: {'✅ Yes' if summary['validation_passed'] else '❌ No'}\n")
            f.write(f"- **Ready for Upload**: {'✅ Yes' if summary['ready_for_upload'] else '❌ No'}\n\n")

            # Hours audit
            hours_audit = self.validation_results["hours_audit"]
            f.write("## Hours Audit\n\n")
            f.write(f"- **Total WBSO Hours**: {hours_audit['wbso_hours']:.2f}\n")
            f.write(f"- **Claimed Hours**: {hours_audit['claim_validation']['claimed_hours']:.2f}\n")
            f.write(f"- **Difference**: {hours_audit['claim_validation']['difference']:.2f}\n")
            f.write(f"- **Within Tolerance**: {'✅ Yes' if hours_audit['claim_validation']['within_tolerance'] else '❌ No'}\n\n")

            # Category breakdown
            f.write("## Category Breakdown\n\n")
            for category, data in hours_audit["category_breakdown"].items():
                f.write(f"- **{category}**: {data['count']} sessions, {data['hours']:.2f} hours\n")

            # Issues summary
            if summary["total_errors"] > 0:
                f.write("\n## Critical Issues\n\n")
                f.write("The following critical issues must be resolved before upload:\n\n")

                # Add specific error details here
                f.write("- See validation_report.json for detailed error information\n")

            if summary["total_warnings"] > 0:
                f.write("\n## Warnings\n\n")
                f.write("The following warnings should be reviewed:\n\n")
                f.write("- See validation_report.json for detailed warning information\n")


def main():
    """Main validation function."""
    # Set up paths
    script_dir = Path(__file__).parent.parent.parent / "docs" / "project" / "hours"
    data_dir = script_dir / "data"
    output_dir = script_dir / "validation_output"

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Initialize validator
    validator = WBSODataValidator(data_dir)

    # Run comprehensive validation
    validation_results = validator.run_comprehensive_validation()
    validator.validation_results = validation_results

    # Export reports
    validator.export_validation_reports(output_dir)

    # Print summary
    summary = validation_results["summary"]
    print(f"\n{'=' * 60}")
    print("WBSO DATA VALIDATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total Sessions: {validation_results['data_sources_loaded']}")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Total Warnings: {summary['total_warnings']}")
    print(f"Validation Passed: {'✅ Yes' if summary['validation_passed'] else '❌ No'}")
    print(f"Ready for Upload: {'✅ Yes' if summary['ready_for_upload'] else '❌ No'}")

    hours_audit = validation_results["hours_audit"]
    print(f"\nWBSO Hours: {hours_audit['wbso_hours']:.2f}")
    print(f"Claimed Hours: {hours_audit['claim_validation']['claimed_hours']:.2f}")
    print(f"Difference: {hours_audit['claim_validation']['difference']:.2f}")
    print(f"Within Tolerance: {'✅ Yes' if hours_audit['claim_validation']['within_tolerance'] else '❌ No'}")

    print(f"\nReports exported to: {output_dir}")
    print(f"{'=' * 60}")

    # Exit with appropriate code
    if summary["validation_passed"]:
        print("✅ Validation successful - data ready for upload")
        return 0
    else:
        print("❌ Validation failed - fix errors before upload")
        return 1


if __name__ == "__main__":
    exit(main())
