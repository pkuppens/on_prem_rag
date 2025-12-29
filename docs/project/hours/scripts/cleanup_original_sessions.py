#!/usr/bin/env python3
"""
Cleanup Original Sessions from Google Calendar

This script identifies and deletes original sessions that have been split,
removing duplicates that cause overlaps.

Author: AI Assistant
Created: 2025-12-02
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.wbso.logging_config import get_logger
from src.wbso.upload import GoogleCalendarUploader

logger = get_logger("cleanup_sessions")

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
CREDENTIALS_PATH = SCRIPT_DIR / "scripts" / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "scripts" / "token.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "wbso_calendar_config.json"


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string from Google Calendar format."""
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Could not parse datetime: {dt_str}")


def get_base_session_id(session_id: str) -> str:
    """Get base session ID without split suffix (e.g., ses_0372.1 -> ses_0372)."""
    if "." in session_id:
        return session_id.split(".")[0]
    return session_id


def identify_original_sessions_to_delete(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify original sessions that should be deleted because they have split versions.

    Returns list of events to delete (original sessions that have .1, .2, etc. versions).
    """
    # Build sets of base session IDs that have splits
    base_ids_with_splits: Set[str] = set()
    all_session_ids: Dict[str, Dict[str, Any]] = {}  # session_id -> event

    for event in events:
        private_props = event.get("extendedProperties", {}).get("private", {})
        session_id = private_props.get("session_id", "")
        if session_id:
            all_session_ids[session_id] = event
            base_id = get_base_session_id(session_id)
            if "." in session_id:  # This is a split session
                base_ids_with_splits.add(base_id)

    # Find original sessions that have splits
    to_delete = []
    for session_id, event in all_session_ids.items():
        base_id = get_base_session_id(session_id)
        # If this is an original (no . in session_id) AND there are splits for this base_id
        if "." not in session_id and base_id in base_ids_with_splits:
            to_delete.append(event)

    return to_delete


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup original sessions that have been split")
    parser.add_argument("--start-date", type=str, default="2025-06-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - don't actually delete")
    args = parser.parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = datetime.now()

    logger.info("=" * 60)
    logger.info("CLEANUP ORIGINAL SESSIONS")
    logger.info("=" * 60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("")

    # Initialize uploader
    uploader = GoogleCalendarUploader(CREDENTIALS_PATH, TOKEN_PATH, CONFIG_PATH)
    if not uploader.authenticate():
        logger.error("Authentication failed")
        return 1

    if not uploader.get_wbso_calendar_id():
        logger.error("WBSO calendar not found or no write access")
        return 1

    # Get existing events with pagination
    logger.info("Extracting events from calendar...")
    existing_events = []
    page_token = None

    while True:
        try:
            events_result = (
                uploader.service.events()
                .list(
                    calendarId=uploader.wbso_calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token,
                )
                .execute()
            )

            items = events_result.get("items", [])
            existing_events.extend(items)

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

        except Exception as e:
            logger.error(f"Error extracting events: {e}")
            break

    logger.info(f"Found {len(existing_events)} events in calendar")

    # Identify original sessions to delete
    logger.info("Identifying original sessions with splits...")
    to_delete = identify_original_sessions_to_delete(existing_events)
    logger.info(f"Found {len(to_delete)} original sessions to delete")

    if not to_delete:
        logger.info("✅ No original sessions to delete - all sessions are properly split")
        return 0

    # Show what will be deleted
    logger.info("")
    logger.info("Original sessions to delete:")
    for event in to_delete:
        private_props = event.get("extendedProperties", {}).get("private", {})
        session_id = private_props.get("session_id", "")
        summary = event.get("summary", "")
        start_str = event.get("start", {}).get("dateTime", "")
        end_str = event.get("end", {}).get("dateTime", "")
        logger.info(f"  - {session_id}: {summary} ({start_str} to {end_str})")

    # Delete events
    if args.dry_run:
        logger.info("")
        logger.info("DRY RUN - Would delete these events")
        return 0

    logger.info("")
    logger.info("Deleting original sessions...")
    deleted_count = 0
    failed_count = 0

    for event in to_delete:
        event_id = event.get("id", "")
        session_id = event.get("extendedProperties", {}).get("private", {}).get("session_id", "")
        try:
            uploader.service.events().delete(calendarId=uploader.wbso_calendar_id, eventId=event_id).execute()
            deleted_count += 1
            logger.info(f"✅ Deleted {session_id} (event ID: {event_id})")
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Failed to delete {session_id}: {e}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("CLEANUP RESULTS")
    logger.info("=" * 60)
    logger.info(f"Deleted: {deleted_count} events")
    logger.info(f"Failed: {failed_count} events")
    logger.info("")

    if failed_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
