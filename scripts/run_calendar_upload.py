#!/usr/bin/env python3
"""
Standalone script to run calendar upload/replacement step separately.

This script loads prepared calendar events and uploads them to Google Calendar,
replacing existing events in the date range.

Usage:
    uv run python scripts/run_calendar_upload.py --start-date 2025-06-01 --end-date 2025-12-02
    uv run python scripts/run_calendar_upload.py --start-date 2025-06-01 --end-date 2025-12-02 --dry-run

Author: AI Assistant
Created: 2025-12-02
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.wbso.pipeline_steps import step_calendar_replace, _get_target_dates
from src.wbso.calendar_event import CalendarEvent
from src.wbso.upload import GoogleCalendarUploader
from src.wbso.logging_config import get_logger

logger = get_logger("calendar_upload_script")

# Default paths
SCRIPT_DIR = Path(__file__).parent.parent / "docs" / "project" / "hours"
DATA_DIR = SCRIPT_DIR / "data"
CREDENTIALS_PATH = SCRIPT_DIR / "scripts" / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "scripts" / "token.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "wbso_calendar_config.json"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"


def load_calendar_events_from_csv(csv_path: Path) -> list[CalendarEvent]:
    """Load calendar events from CSV file."""
    import csv
    import json

    if not csv_path.exists():
        raise FileNotFoundError(f"Calendar events CSV not found: {csv_path}")

    events = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Reconstruct CalendarEvent from CSV row
                # Note: CSV doesn't contain all CalendarEvent fields, so we need to reconstruct
                # the minimal required fields
                start_dt = row.get("start_datetime", "")
                end_dt = row.get("end_datetime", "")
                summary = row.get("summary", "")
                session_id = row.get("session_id", "")

                if not start_dt or not end_dt:
                    logger.warning(f"Skipping row with missing datetime: {row}")
                    continue

                # Create minimal CalendarEvent
                # We'll need to load from the actual prepared events or reconstruct
                # For now, let's try to load from the context if available
                # This is a limitation - we need the full CalendarEvent objects
                logger.warning(
                    "CSV loading is limited - calendar events should be loaded from pipeline context. "
                    "Run the pipeline up to step_google_calendar_data_preparation first."
                )
                # We'll need to use the dataset instead
                break

            except Exception as e:
                logger.error(f"Error loading row from CSV: {e}")
                continue

    return events


def load_calendar_events_from_prepared_data() -> list[CalendarEvent]:
    """Load calendar events from prepared data (run pipeline steps up to preparation)."""
    logger.info("Loading calendar events by running pipeline steps up to data preparation...")

    # We need to run the pipeline steps up to step_google_calendar_data_preparation
    # to get the prepared calendar events
    from src.wbso.pipeline_steps import (
        step_data_refresh,
        step_consolidate_system_events,
        step_filter_logon_logoff,
        step_polish_logon_logoff,
        step_load_activities,
        step_convert_to_work_sessions,
        step_load_polished_sessions,
        step_validate,
        step_time_polish,
        step_deduplicate,
        step_assign_activities,
        step_assign_commits_to_sessions,
        step_content_polish,
        step_event_convert,
        step_google_calendar_data_preparation,
    )

    # Set up minimal context
    context: Dict[str, Any] = {
        "force_refresh": False,
        "force_regenerate_activities": False,
        "force_regenerate_system_events": False,
        "dry_run": False,
    }

    # Run steps up to data preparation
    steps = [
        ("data_refresh", step_data_refresh),
        ("consolidate_system_events", step_consolidate_system_events),
        ("filter_logon_logoff", step_filter_logon_logoff),
        ("polish_logon_logoff", step_polish_logon_logoff),
        ("load_activities", step_load_activities),
        ("convert_to_work_sessions", step_convert_to_work_sessions),
        ("load_polished_sessions", step_load_polished_sessions),
        ("validate", step_validate),
        ("time_polish", step_time_polish),
        ("deduplicate", step_deduplicate),
        ("assign_activities", step_assign_activities),
        ("assign_commits_to_sessions", step_assign_commits_to_sessions),
        ("content_polish", step_content_polish),
        ("event_convert", step_event_convert),
        ("google_calendar_data_preparation", step_google_calendar_data_preparation),
    ]

    logger.info("Running pipeline steps to prepare calendar events...")
    for step_name, step_func in steps:
        logger.info(f"Running step: {step_name}")
        try:
            result = step_func(context)
            if not result.get("success", False):
                logger.warning(f"Step {step_name} reported failure: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Step {step_name} failed with exception: {e}", exc_info=True)
            raise

    # Get prepared calendar events from context
    calendar_events = context.get("calendar_events", [])
    if not calendar_events:
        raise ValueError("No calendar events prepared. Check pipeline steps for errors.")

    logger.info(f"Loaded {len(calendar_events)} prepared calendar events")
    return calendar_events


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run calendar upload/replacement step separately")
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - don't actually upload")
    args = parser.parse_args()

    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError as e:
        logger.error(f"Invalid date format: {e}. Use YYYY-MM-DD")
        return 1

    logger.info("=" * 60)
    logger.info("CALENDAR UPLOAD STANDALONE SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("")

    # Load calendar events
    try:
        calendar_events = load_calendar_events_from_prepared_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("\nTo prepare the data, run:")
        logger.error("  uv run python -m src.wbso.pipeline --start-date 2025-06-01 --end-date 2025-12-02")
        logger.error("  (The pipeline will stop before calendar upload if there are issues)")
        return 1
    except Exception as e:
        logger.error(f"Failed to load calendar events: {e}", exc_info=True)
        return 1

    if not calendar_events:
        logger.error("No calendar events to upload")
        return 1

    logger.info(f"Loaded {len(calendar_events)} calendar events ready for upload")

    # Filter events by date range
    filtered_events = []
    for event in calendar_events:
        try:
            start_dt_str = event.start.get("dateTime", "")
            if start_dt_str:
                event_start = datetime.fromisoformat(start_dt_str.replace("Z", "+00:00"))
                if start_date.date() <= event_start.date() <= end_date.date():
                    filtered_events.append(event)
        except Exception as e:
            logger.warning(f"Error filtering event {event.summary}: {e}")

    logger.info(f"Filtered to {len(filtered_events)} events in date range")

    if not filtered_events:
        logger.warning("No events in the specified date range")
        return 1

    # Set up context for step_calendar_replace
    context: Dict[str, Any] = {
        "dry_run": args.dry_run,
        "calendar_events": filtered_events,
        "target_start_date": start_date,
        "target_end_date": end_date,
        "force_refresh": False,
        "force_regenerate_activities": False,
        "force_regenerate_system_events": False,
    }

    # Initialize uploader
    uploader = GoogleCalendarUploader(CREDENTIALS_PATH, TOKEN_PATH, CONFIG_PATH)
    if not uploader.authenticate():
        logger.error("Authentication failed")
        return 1

    if not uploader.get_wbso_calendar_id():
        logger.error("WBSO calendar not found or no write access")
        return 1

    context["uploader"] = uploader

    # Run calendar replacement step
    logger.info("")
    logger.info("Running calendar replacement step...")
    logger.info("")

    try:
        result = step_calendar_replace(context)

        # Print results
        logger.info("")
        logger.info("=" * 60)
        logger.info("CALENDAR UPLOAD RESULTS")
        logger.info("=" * 60)

        if result.get("success"):
            logger.info("✅ Calendar upload completed successfully")
            logger.info(f"   Deleted: {result.get('deleted_count', 0)} events")
            logger.info(f"   Uploaded: {result.get('uploaded_count', 0)} events")
            logger.info(f"   Failed: {result.get('failed_count', 0)} events")
        else:
            logger.error("❌ Calendar upload failed")
            logger.error(f"   Message: {result.get('message', 'Unknown error')}")

        # Check for errors in upload results
        upload_results = context.get("upload_results", {})
        errors = upload_results.get("errors", [])
        if errors:
            logger.warning(f"\n⚠️  {len(errors)} upload errors detected:")
            for error in errors[:10]:  # Show first 10
                logger.warning(
                    f"   - {error.get('event_summary', 'Unknown')}: "
                    f"{error.get('error_message', 'Unknown error')} "
                    f"(Code: {error.get('error_code', 'N/A')})"
                )
            if len(errors) > 10:
                logger.warning(f"   ... and {len(errors) - 10} more errors")

        # Check for rate limiting
        upload_results_list = upload_results.get("upload_results", [])
        rate_limit_errors = [r for r in upload_results_list if r.get("error_code") == 429]
        if rate_limit_errors:
            logger.warning(f"\n⚠️  Rate limiting detected: {len(rate_limit_errors)} events hit rate limits")
            logger.warning("   Consider increasing RATE_LIMIT_DELAY in src/wbso/upload.py")

        return 0 if result.get("success") else 1

    except Exception as e:
        logger.error(f"Calendar upload failed with exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
