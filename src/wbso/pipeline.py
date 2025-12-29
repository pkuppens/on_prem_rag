#!/usr/bin/env python3
"""
WBSO Calendar Upload Pipeline

Unified pipeline that validates, converts, uploads, and verifies WBSO calendar entries.
Uses extensible step-based architecture for easy insertion of new steps.

Implements TOC-AUTO-001: No Calendar Entries in WBSO Calendar (CRITICAL)

Author: AI Assistant
Created: 2025-11-28
Updated: 2025-11-28
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .logging_config import get_logger
from .pipeline_steps import (
    step_assign_activities,
    step_assign_commits_to_sessions,
    step_calendar_replace,
    step_conflict_detect,
    step_consolidate_system_events,
    step_content_polish,
    step_convert_to_work_sessions,
    step_data_refresh,
    step_data_summary,
    step_deduplicate,
    step_detect_commits_without_system_events,
    step_event_convert,
    step_filter_logon_logoff,
    step_google_calendar_data_preparation,
    step_load_activities,
    step_load_polished_sessions,
    step_polish_logon_logoff,
    step_report,
    step_store_activity_blocks,
    step_system_events_summary,
    step_time_polish,
    step_validate,
    step_verify,
)

logger = get_logger("pipeline")

# Default paths
UPLOAD_OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "upload_output"

# Default target date range
DEFAULT_START_DATE = datetime(2025, 6, 1)
DEFAULT_END_DATE = datetime(2025, 12, 31, 23, 59, 59)


class WBSOCalendarPipeline:
    """Unified pipeline for WBSO calendar upload with extensible step architecture."""

    def __init__(
        self,
        force_validation: bool = False,
        dry_run: bool = False,
        force_refresh: bool = False,
        force_regenerate_activities: bool = False,
        force_regenerate_system_events: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """Initialize pipeline.

        Args:
            start_date: Start date for calendar operations (default: 2025-06-01)
            end_date: End date for calendar operations (default: 2025-12-31)
        """
        self.force_validation = force_validation
        self.dry_run = dry_run
        self.force_refresh = force_refresh
        self.force_regenerate_activities = force_regenerate_activities
        self.force_regenerate_system_events = force_regenerate_system_events

        # Date range for calendar operations
        self.start_date = start_date or DEFAULT_START_DATE
        self.end_date = end_date or DEFAULT_END_DATE

        # Pipeline context (shared state between steps)
        self.context = {
            "force_validation": force_validation,
            "dry_run": dry_run,
            "force_refresh": force_refresh,
            "force_regenerate_activities": force_regenerate_activities,
            "force_regenerate_system_events": force_regenerate_system_events,
            "target_start_date": self.start_date,
            "target_end_date": self.end_date,
        }

        # Step reports (array of individual step reports)
        self.step_reports: List[Dict[str, Any]] = []

        # Define pipeline steps (easily extensible - just add/remove/reorder)
        self.pipeline_steps: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = [
            step_data_refresh,  # Refresh data sources (extract new CSV files)
            step_consolidate_system_events,  # Consolidate all system_events_*.csv into all_system_events.csv (one-off)
            step_filter_logon_logoff,  # Filter logon/logoff events (7001/7002) and create sessions
            step_polish_logon_logoff,  # Polish logon/logoff timestamps (round to 5 minutes, add breaks)
            step_data_summary,  # Summarize data collection date ranges
            step_load_activities,  # Load/generate WBSO activities list
            step_convert_to_work_sessions,  # Convert polished sessions to work sessions with filtering
            step_load_polished_sessions,  # Load polished logon/logoff sessions into WBSODataset
            step_system_events_summary,  # Summarize system events coverage and hours
            step_validate,  # Validate data
            step_time_polish,  # Round times, add breaks, clip to max hours
            step_deduplicate,  # Remove duplicates
            step_store_activity_blocks,  # Store polished activity blocks for human review
            step_conflict_detect,  # Detect calendar conflicts
            step_assign_activities,  # Assign WBSO activities based on commits and repo purpose
            step_assign_commits_to_sessions,  # Assign commits to sessions by timestamp
            step_detect_commits_without_system_events,  # Detect commits on days without system events
            step_content_polish,  # Polish event content
            step_event_convert,  # Convert to calendar events
            step_google_calendar_data_preparation,  # Prepare calendar events (corrections, filters, ISO week)
            step_calendar_replace,  # Replace calendar events (delete old, upload new)
            step_verify,  # Verify upload
            step_report,  # Generate report
        ]

    def run(self) -> int:
        """Run the complete pipeline."""
        logger.info("=" * 60)
        logger.info("WBSO CALENDAR UPLOAD PIPELINE")
        logger.info("=" * 60)
        logger.info(f"Dry Run: {'Yes' if self.dry_run else 'No'}")
        logger.info(f"Force Refresh: {'Yes' if self.force_refresh else 'No'}")
        logger.info(f"Date Range: {self.start_date.date()} to {self.end_date.date()}")
        logger.info("")

        try:
            # Execute each step in sequence
            total_steps = len(self.pipeline_steps)
            for step_index, step_func in enumerate(self.pipeline_steps, 1):
                step_name = step_func.__name__
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Executing Step {step_index}/{total_steps}: {step_name}")
                logger.info(f"{'=' * 60}")
                sys.stdout.flush()  # Ensure output is visible immediately

                step_start_time = time.time()
                try:
                    # Execute step
                    step_report = step_func(self.context)

                    # Calculate step duration
                    step_duration = time.time() - step_start_time

                    # Store step report with timing
                    step_report["duration_seconds"] = step_duration
                    self.step_reports.append(step_report)

                    # Log step completion with timing
                    if step_report.get("success", False):
                        logger.info(f"✅ Step {step_name} completed in {step_duration:.2f} seconds")
                        logger.info(f"   Message: {step_report.get('message', 'No message')}")
                    else:
                        logger.error(f"❌ Step {step_name} failed after {step_duration:.2f} seconds")
                        logger.error(f"   Error: {step_report.get('message', 'Unknown error')}")
                    sys.stdout.flush()  # Ensure output is visible immediately

                    # Check if step failed
                    if not step_report.get("success", False):
                        logger.error(f"Step {step_name} failed: {step_report.get('message', 'Unknown error')}")
                        # Continue to next step (some steps can fail without stopping pipeline)
                        # Critical steps should return False and we can check here

                except Exception as e:
                    step_duration = time.time() - step_start_time
                    logger.error(f"Step {step_name} raised exception after {step_duration:.2f} seconds: {e}", exc_info=True)
                    sys.stdout.flush()  # Ensure output is visible immediately
                    # Create error report for this step
                    error_report = {
                        "step_name": step_name,
                        "success": False,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "duration_seconds": step_duration,
                        "message": f"Step failed with exception: {e}",
                    }
                    self.step_reports.append(error_report)
                    # Continue to next step

            # Generate final pipeline report
            self.generate_pipeline_report()

            # Determine success
            if self.dry_run:
                logger.info("✅ Pipeline completed (dry run)")
                return 0

            verification_report = next((r for r in self.step_reports if r.get("step_name") == "verify"), None)
            calendar_hours = verification_report.get("total_hours", 0.0) if verification_report else 0.0

            if calendar_hours >= 400.0:
                logger.info(f"✅ Pipeline completed successfully: {calendar_hours:.2f} hours in calendar")
                return 0
            else:
                logger.warning(f"⚠️ Pipeline completed but calendar hours ({calendar_hours:.2f}) below target (400+)")
                return 0  # Still return 0 as pipeline completed, just not enough hours

        except Exception as e:
            logger.error(f"Pipeline failed with exception: {e}", exc_info=True)
            return 1

    def generate_pipeline_report(self) -> None:
        """Generate comprehensive pipeline report with step-by-step results."""
        logger.info("=" * 60)
        logger.info("GENERATING PIPELINE REPORT")
        logger.info("=" * 60)

        # Get summary data from context
        dataset = self.context.get("dataset")
        verification_results = self.context.get("verification_results", {})
        polished_summary = self.context.get("polished_logon_logoff_summary", {})

        # Get work sessions hours from convert_to_work_sessions step
        work_sessions_hours = 0.0
        convert_step_report = next((r for r in self.step_reports if r.get("step_name") == "convert_to_work_sessions"), None)
        if convert_step_report:
            work_sessions_hours = convert_step_report.get("total_hours", 0.0)

        # Calculate totals
        from .calendar_event import WBSODataset, WBSOSession

        wbso_sessions: List[WBSOSession] = []
        if isinstance(dataset, WBSODataset):
            wbso_sessions = [s for s in dataset.sessions if s.is_wbso]  # type: ignore[attr-defined]

        calculated_hours = 0.0
        for s in wbso_sessions:
            if s.start_time and self.start_date.date() <= s.start_time.date() <= self.end_date.date():
                calculated_hours += s.work_hours

        calendar_hours = verification_results.get("total_hours", 0.0) if isinstance(verification_results, dict) else 0.0

        # Get commit filtering status from convert step
        commit_filtering_disabled = False
        dates_with_commits_count = 0
        dates_without_commits_count = 0
        convert_step_report = next((r for r in self.step_reports if r.get("step_name") == "convert_to_work_sessions"), None)
        if convert_step_report:
            commit_filtering_disabled = convert_step_report.get("commit_filtering_disabled", False)
            dates_with_commits_count = convert_step_report.get("dates_with_commits", 0)
            dates_without_commits_count = convert_step_report.get("dates_without_commits", 0)

        # Create comprehensive report
        report = {
            "pipeline_timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "date_range": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
            },
            "summary": {
                "work_sessions_hours": work_sessions_hours,  # Hours from polished work sessions (after filtering)
                "calculated_hours": calculated_hours,  # Hours from WBSO sessions in dataset
                "calendar_hours": calendar_hours,  # Hours in Google Calendar (if uploaded)
                "gap": calculated_hours - calendar_hours,
                "target_hours": 510.0,
                "target_gap": 510.0 - calendar_hours,
                "target_achievement_percent": (calendar_hours / 510.0 * 100) if 510.0 > 0 else 0,
                "hours_that_could_be_assigned_to_wbso": work_sessions_hours,  # Hours available for WBSO assignment
                "commit_filtering_note": "Commit-based filtering is disabled to avoid filtering out too much work. Dates with commits are tracked for reporting only."
                if commit_filtering_disabled
                else None,
                "dates_with_commits": dates_with_commits_count,
                "dates_without_commits": dates_without_commits_count,
            },
            "polished_logon_logoff": polished_summary,  # Add polished logon/logoff summary
            "steps": self.step_reports,  # Array of step reports
        }

        # Save report
        UPLOAD_OUTPUT_DIR.mkdir(exist_ok=True)
        report_path = UPLOAD_OUTPUT_DIR / "pipeline_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n{'=' * 60}")
        print("WBSO CALENDAR PIPELINE SUMMARY")
        print(f"{'=' * 60}")
        target_start_date, target_end_date = self.start_date, self.end_date
        print(f"Date Range: {target_start_date.date()} to {target_end_date.date()}")
        print(f"Work Sessions Hours (polished): {work_sessions_hours:.2f} hours")
        print(f"Calculated Hours (WBSO sessions): {calculated_hours:.2f} hours")
        print(f"Calendar Hours: {calendar_hours:.2f} hours")
        print(f"Gap: {calculated_hours - calendar_hours:.2f} hours")
        print(f"Target Hours: 510.0 hours")
        print(f"Target Gap: {510.0 - calendar_hours:.2f} hours")
        print(f"Target Achievement: {(calendar_hours / 510.0 * 100):.1f}%")
        print(f"Hours That Could Be Assigned to WBSO: {work_sessions_hours:.2f} hours")
        if commit_filtering_disabled:
            print(f"\nNote: Commit-based filtering is disabled to avoid filtering out too much work.")
            print(f"      Dates with commits: {dates_with_commits_count}, Dates without commits: {dates_without_commits_count}")

        # Print step summary
        print(f"\nPipeline Steps ({len(self.step_reports)}):")
        for step_report in self.step_reports:
            step_name = step_report.get("step_name", "unknown")
            success = step_report.get("success", False)
            message = step_report.get("message", "")
            status = "✅" if success else "❌"
            print(f"  {status} {step_name}: {message}")

        print(f"\nReport saved to: {report_path}")
        print(f"{'=' * 60}\n")

        logger.info(f"✅ Report generated: {report_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="WBSO Calendar Upload Pipeline")
    parser.add_argument("--force-validation", action="store_true", help="Force re-validation even if validated data exists")
    parser.add_argument("--force-refresh", action="store_true", help="Force data refresh")
    parser.add_argument("--force-regenerate-activities", action="store_true", help="Force regenerate WBSO activities list")
    parser.add_argument(
        "--force-regenerate-system-events", action="store_true", help="Force regenerate consolidated system events file"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - don't actually upload")
    parser.add_argument("--start-date", type=str, help="Start date for calendar operations (YYYY-MM-DD, default: 2025-06-01)")
    parser.add_argument("--end-date", type=str, help="End date for calendar operations (YYYY-MM-DD, default: 2025-12-31)")
    args = parser.parse_args()

    # Parse date arguments
    start_date = DEFAULT_START_DATE
    end_date = DEFAULT_END_DATE
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD")
            return 1
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            # Set to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            return 1

    pipeline = WBSOCalendarPipeline(
        force_validation=args.force_validation,
        dry_run=args.dry_run,
        force_refresh=args.force_refresh,
        force_regenerate_activities=args.force_regenerate_activities,
        force_regenerate_system_events=args.force_regenerate_system_events,
        start_date=start_date,
        end_date=end_date,
    )
    exit_code = pipeline.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
