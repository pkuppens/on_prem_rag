#!/usr/bin/env python3
"""
Check WBSO Calendar Hours

Quick script to check how many hours are actually in the WBSO Google Calendar.
Also detects duplicates and conflicts within the calendar.
"""

import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from wbso.logging_config import get_logger
from wbso.upload import GoogleCalendarUploader

logger = get_logger("check_calendar_hours")


def calculate_hours_from_events(events):
    """Calculate total hours from calendar events."""
    total_hours = 0.0

    for event in events:
        start_str = event.get("start", {}).get("dateTime")
        end_str = event.get("end", {}).get("dateTime")

        if not start_str or not end_str:
            continue

        try:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            duration = end_dt - start_dt
            hours = duration.total_seconds() / 3600.0
            total_hours += hours
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing event times: {e}")
            continue

    return total_hours


def detect_duplicates(events):
    """Detect duplicate events by session_id and datetime range."""
    duplicates = {
        "by_session_id": defaultdict(list),
        "by_datetime": defaultdict(list),
    }

    for event in events:
        # Check by session_id
        private_props = event.get("extendedProperties", {}).get("private", {})
        session_id = private_props.get("session_id")
        if session_id:
            duplicates["by_session_id"][session_id].append(
                {
                    "event_id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": event.get("start", {}).get("dateTime"),
                    "end": event.get("end", {}).get("dateTime"),
                }
            )

        # Check by datetime range
        start_str = event.get("start", {}).get("dateTime")
        end_str = event.get("end", {}).get("dateTime")
        if start_str and end_str:
            dt_key = f"{start_str}-{end_str}"
            duplicates["by_datetime"][dt_key].append(
                {
                    "event_id": event.get("id"),
                    "summary": event.get("summary"),
                    "session_id": session_id,
                }
            )

    # Filter to only actual duplicates (more than one)
    duplicate_session_ids = {k: v for k, v in duplicates["by_session_id"].items() if len(v) > 1}
    duplicate_datetime_ranges = {k: v for k, v in duplicates["by_datetime"].items() if len(v) > 1}

    return {
        "by_session_id": duplicate_session_ids,
        "by_datetime": duplicate_datetime_ranges,
    }


def detect_conflicts(events):
    """Detect time conflicts between events."""
    conflicts = []

    # Sort events by start time
    sorted_events = sorted(events, key=lambda e: e.get("start", {}).get("dateTime", ""))

    for i, event1 in enumerate(sorted_events):
        start1_str = event1.get("start", {}).get("dateTime")
        end1_str = event1.get("end", {}).get("dateTime")

        if not start1_str or not end1_str:
            continue

        try:
            start1 = datetime.fromisoformat(start1_str.replace("Z", "+00:00"))
            end1 = datetime.fromisoformat(end1_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        # Check against remaining events
        for event2 in sorted_events[i + 1 :]:
            start2_str = event2.get("start", {}).get("dateTime")
            end2_str = event2.get("end", {}).get("dateTime")

            if not start2_str or not end2_str:
                continue

            try:
                start2 = datetime.fromisoformat(start2_str.replace("Z", "+00:00"))
                end2 = datetime.fromisoformat(end2_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            # Check for overlap
            if start1 < end2 and end1 > start2:
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0

                conflicts.append(
                    {
                        "event1_id": event1.get("id"),
                        "event1_summary": event1.get("summary"),
                        "event1_start": start1_str,
                        "event1_end": end1_str,
                        "event2_id": event2.get("id"),
                        "event2_summary": event2.get("summary"),
                        "event2_start": start2_str,
                        "event2_end": end2_str,
                        "overlap_hours": overlap_hours,
                        "conflict_type": "short" if overlap_hours < 2.0 else "long",
                    }
                )
        # Optimization: if start1 is after all other events' end times, we can break
        # But for simplicity, we check all pairs

    return conflicts


def main():
    """Check hours in WBSO calendar and detect duplicates/conflicts."""
    script_dir = Path(__file__).parent.parent
    credentials_path = script_dir / "scripts" / "credentials.json"
    token_path = script_dir / "scripts" / "token.json"
    config_path = script_dir / "config" / "wbso_calendar_config.json"

    # Date range: 2025-06-01 to today
    start_date = datetime(2025, 6, 1)
    end_date = datetime.now()

    uploader = GoogleCalendarUploader(credentials_path, token_path, config_path)

    # Authenticate
    if not uploader.authenticate():
        print("❌ Authentication failed")
        return 1

    # Get WBSO calendar ID
    calendar_id = uploader.get_wbso_calendar_id()
    if not calendar_id:
        print("❌ WBSO calendar not found")
        return 1

    # Get existing events
    existing_events_data = uploader.get_existing_events(start_date, end_date)
    events = existing_events_data.get("events", [])

    # Filter events in date range
    filtered_events = []
    for event in events:
        start_str = event.get("start", {}).get("dateTime")
        if start_str:
            try:
                event_start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                if start_date <= event_start <= end_date:
                    filtered_events.append(event)
            except (ValueError, AttributeError):
                continue

    # Calculate hours
    total_hours = calculate_hours_from_events(filtered_events)

    # Detect duplicates
    duplicates = detect_duplicates(filtered_events)
    duplicate_session_ids = duplicates["by_session_id"]
    duplicate_datetime_ranges = duplicates["by_datetime"]

    # Detect conflicts
    conflicts = detect_conflicts(filtered_events)
    short_conflicts = [c for c in conflicts if c["conflict_type"] == "short"]
    long_conflicts = [c for c in conflicts if c["conflict_type"] == "long"]

    # Print results
    print(f"\n{'=' * 60}")
    print("WBSO CALENDAR HOURS CHECK")
    print(f"{'=' * 60}")
    print(f"Calendar: WBSO Activities 2025")
    print(f"Date Range: {start_date.date()} to {end_date.date()}")
    print(f"Total Events: {len(filtered_events)}")
    print(f"Total Hours: {total_hours:.2f} hours")
    print(f"\nDuplicate Detection:")
    print(f"  Duplicate Session IDs: {len(duplicate_session_ids)}")
    print(f"  Duplicate DateTime Ranges: {len(duplicate_datetime_ranges)}")
    print(f"\nConflict Detection:")
    print(f"  Total Conflicts: {len(conflicts)}")
    print(f"  Short Conflicts (<2h): {len(short_conflicts)}")
    print(f"  Long Conflicts (≥2h): {len(long_conflicts)}")

    # Show duplicate details
    if duplicate_session_ids:
        print(f"\nDuplicate Session IDs (showing first 5):")
        for session_id, event_list in list(duplicate_session_ids.items())[:5]:
            print(f"  {session_id}: {len(event_list)} events")
            for event_info in event_list[:2]:
                print(f"    - {event_info['summary']} ({event_info['event_id']})")

    if duplicate_datetime_ranges:
        print(f"\nDuplicate DateTime Ranges (showing first 5):")
        for dt_key, event_list in list(duplicate_datetime_ranges.items())[:5]:
            print(f"  {dt_key}: {len(event_list)} events")
            for event_info in event_list[:2]:
                print(f"    - {event_info['summary']} ({event_info['event_id']})")

    # Show conflict details
    if conflicts:
        print(f"\nConflicts (showing first 5):")
        for conflict in conflicts[:5]:
            print(f"  {conflict['conflict_type'].upper()}: {conflict['overlap_hours']:.2f}h overlap")
            print(f"    Event 1: {conflict['event1_summary']}")
            print(f"    Event 2: {conflict['event2_summary']}")

    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    exit(main())
