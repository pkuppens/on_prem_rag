#!/usr/bin/env python3
"""
Upload Calendar Events from CSV to Google Calendar

This script loads calendar events directly from CSV and uploads them to Google Calendar,
replacing existing events in the date range. No pipeline recalculation needed.

Author: AI Assistant
Created: 2025-12-02
Updated: 2025-12-02
"""

import csv
import json
import signal
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.wbso.calendar_event import CalendarEvent
from src.wbso.logging_config import get_logger
from src.wbso.pipeline_steps import step_calendar_replace
from src.wbso.upload import GoogleCalendarUploader

logger = get_logger("csv_calendar_upload")

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "data"
CREDENTIALS_PATH = SCRIPT_DIR / "scripts" / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "scripts" / "token.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "wbso_calendar_config.json"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"

# Error logging directory (outside git version control)
ERROR_LOG_DIR = project_root / "tmp" / "calendar_upload_logs"
ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global state for cancellation tracking
_cancellation_info = {"cancelled": False, "reason": None, "timestamp": None}


def detect_date_range_from_csv(csv_path: Path) -> Tuple[datetime, datetime]:
    """
    Detect date range from CSV file by finding min and max dates.

    Args:
        csv_path: Path to calendar events CSV

    Returns:
        Tuple of (start_date, end_date)
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Calendar events CSV not found: {csv_path}")

    dates = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start_str = row.get("start_datetime", "")
            if start_str:
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    dates.append(start_dt.date())
                except (ValueError, AttributeError):
                    continue

    if not dates:
        raise ValueError("No valid dates found in CSV file")

    min_date = min(dates)
    max_date = max(dates)

    start_date = datetime.combine(min_date, datetime.min.time())
    end_date = datetime.combine(max_date, datetime.max.time()).replace(hour=23, minute=59, second=59)

    logger.info(f"Auto-detected date range from CSV: {min_date} to {max_date}")
    return start_date, end_date


def save_error_log(error_data: Dict[str, Any], log_dir: Path) -> Path:
    """
    Save error/cancellation information to log file.

    Args:
        error_data: Dictionary containing error information
        log_dir: Directory to save log files

    Returns:
        Path to saved log file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"calendar_upload_error_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(error_data, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"Error log saved to: {log_file}")
    return log_file


def signal_handler(signum, frame):
    """Handle cancellation signals (Ctrl+C, etc.)."""
    _cancellation_info["cancelled"] = True
    _cancellation_info["reason"] = f"Signal {signum} received"
    _cancellation_info["timestamp"] = datetime.now().isoformat()
    logger.warning(f"⚠️  Cancellation signal received: {signum}")


def load_calendar_events_from_csv(csv_path: Path) -> List[CalendarEvent]:
    """Load calendar events from CSV file and convert to CalendarEvent objects."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Calendar events CSV not found: {csv_path}")

    events = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                session_id = row.get("session_id", "")
                summary = row.get("summary", "")
                description = row.get("description", "")
                start_str = row.get("start_datetime", "")
                end_str = row.get("end_datetime", "")
                location = row.get("location", "Thuiswerk")
                hours = float(row.get("hours", 0.0))

                if not start_str or not end_str:
                    logger.warning(f"Skipping row with missing datetime: {session_id}")
                    continue

                # Parse datetimes
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

                # Format for Google Calendar
                start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
                end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

                # Create CalendarEvent
                event = CalendarEvent(
                    summary=summary,
                    description=description,
                    start={"dateTime": start_iso, "timeZone": "Europe/Amsterdam"},
                    end={"dateTime": end_iso, "timeZone": "Europe/Amsterdam"},
                    color_id="1",
                    extended_properties={
                        "private": {
                            "wbso_project": "WBSO-AICM-2025-01",
                            "wbso_category": "GENERAL_RD",  # Default category
                            "session_id": session_id,
                            "work_hours": str(hours),
                            "is_synthetic": "false",
                            "commit_count": "0",
                            "source_type": "real",
                            "confidence_score": "1.0",
                            "activity_id": "",
                        }
                    },
                    location=location,
                    transparency="opaque",
                )

                events.append(event)

            except Exception as e:
                logger.warning(f"Error loading row {row.get('session_id', 'unknown')}: {e}")
                continue

    logger.info(f"Loaded {len(events)} calendar events from CSV")
    return events


def main():
    """Main entry point."""
    import argparse

    # Set up signal handlers for cancellation tracking
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description="Upload calendar events from CSV to Google Calendar")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD), auto-detected if not provided")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), auto-detected if not provided")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - don't actually upload")
    args = parser.parse_args()

    # Initialize error tracking
    error_data = {
        "script": "upload_calendar_from_csv.py",
        "started_at": datetime.now().isoformat(),
        "dry_run": args.dry_run,
        "errors": [],
        "warnings": [],
        "cancellation": None,
        "result": None,
    }

    try:
        # Auto-detect date range if not provided
        if args.start_date and args.end_date:
            try:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)
                logger.info(f"Using provided date range: {start_date.date()} to {end_date.date()}")
            except ValueError as e:
                logger.error(f"Invalid date format: {e}. Use YYYY-MM-DD")
                error_data["errors"].append(f"Invalid date format: {e}")
                error_data["result"] = "failed"
                save_error_log(error_data, ERROR_LOG_DIR)
                return 1
        else:
            try:
                start_date, end_date = detect_date_range_from_csv(CALENDAR_EVENTS_CSV)
                error_data["auto_detected_dates"] = {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                }
            except Exception as e:
                logger.error(f"Failed to auto-detect date range: {e}")
                error_data["errors"].append(f"Auto-detect failed: {e}")
                error_data["result"] = "failed"
                save_error_log(error_data, ERROR_LOG_DIR)
                return 1

        logger.info("=" * 60)
        logger.info("CALENDAR UPLOAD FROM CSV")
        logger.info("=" * 60)
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Dry run: {args.dry_run}")
        logger.info("")

        # Load calendar events from CSV
        try:
            calendar_events = load_calendar_events_from_csv(CALENDAR_EVENTS_CSV)
            error_data["events_loaded"] = len(calendar_events)
        except Exception as e:
            logger.error(f"Failed to load calendar events: {e}", exc_info=True)
            error_data["errors"].append({"type": "load_error", "message": str(e), "traceback": traceback.format_exc()})
            error_data["result"] = "failed"
            save_error_log(error_data, ERROR_LOG_DIR)
            return 1

        if not calendar_events:
            logger.error("No calendar events to upload")
            error_data["errors"].append("No calendar events found in CSV")
            error_data["result"] = "failed"
            save_error_log(error_data, ERROR_LOG_DIR)
            return 1

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
                error_data["warnings"].append({"type": "filter_error", "event": event.summary, "message": str(e)})

        logger.info(f"Filtered to {len(filtered_events)} events in date range")
        error_data["events_filtered"] = len(filtered_events)

        if not filtered_events:
            logger.warning("No events in the specified date range")
            error_data["warnings"].append("No events in date range")
            error_data["result"] = "no_events"
            save_error_log(error_data, ERROR_LOG_DIR)
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
            error_data["upload_result"] = result

            # Check for cancellation
            if _cancellation_info["cancelled"]:
                error_data["cancellation"] = _cancellation_info
                logger.warning("⚠️  Upload was cancelled/interrupted")
                save_error_log(error_data, ERROR_LOG_DIR)
                return 130  # Standard exit code for SIGINT

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
                error_data["result"] = "success"
            else:
                logger.error("❌ Calendar upload failed")
                logger.error(f"   Message: {result.get('message', 'Unknown error')}")
                error_data["result"] = "failed"
                error_data["errors"].append({"type": "upload_failed", "message": result.get("message", "Unknown error")})

            # Check for errors in upload results
            upload_results = context.get("upload_results", {})
            errors = upload_results.get("errors", [])
            if errors:
                logger.warning(f"\n⚠️  {len(errors)} upload errors detected:")
                error_data["upload_errors"] = errors
                for error in errors[:10]:  # Show first 10
                    logger.warning(
                        f"   - {error.get('event_summary', 'Unknown')}: "
                        f"{error.get('error_message', 'Unknown error')} "
                        f"(Code: {error.get('error_code', 'N/A')})"
                    )
                if len(errors) > 10:
                    logger.warning(f"   ... and {len(errors) - 10} more errors")

            # Save error log if there were any issues
            if error_data["errors"] or error_data["warnings"] or not result.get("success"):
                save_error_log(error_data, ERROR_LOG_DIR)

            return 0 if result.get("success") else 1

        except KeyboardInterrupt:
            error_data["cancellation"] = {
                "cancelled": True,
                "reason": "KeyboardInterrupt (Ctrl+C)",
                "timestamp": datetime.now().isoformat(),
            }
            logger.warning("⚠️  Upload interrupted by user (KeyboardInterrupt)")
            save_error_log(error_data, ERROR_LOG_DIR)
            return 130

        except Exception as e:
            error_data["errors"].append({"type": "exception", "message": str(e), "traceback": traceback.format_exc()})
            error_data["result"] = "exception"
            logger.error(f"Calendar upload failed with exception: {e}", exc_info=True)
            save_error_log(error_data, ERROR_LOG_DIR)
            return 1

    except Exception as e:
        error_data["errors"].append({"type": "fatal_exception", "message": str(e), "traceback": traceback.format_exc()})
        error_data["result"] = "fatal_exception"
        logger.error(f"Fatal error: {e}", exc_info=True)
        save_error_log(error_data, ERROR_LOG_DIR)
        return 1


if __name__ == "__main__":
    sys.exit(main())
