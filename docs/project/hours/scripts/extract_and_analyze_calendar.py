#!/usr/bin/env python3
"""
Extract and Analyze Google Calendar Events

This script extracts all WBSO calendar items from Google Calendar and:
1. Detects and reports overlapping items
2. Groups items by week and title
3. Summarizes hours worked in a markdown report

Author: AI Assistant
Created: 2025-12-02
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.wbso.logging_config import get_logger
from src.wbso.upload import GoogleCalendarUploader

logger = get_logger("calendar_extract")

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
CREDENTIALS_PATH = SCRIPT_DIR / "scripts" / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "scripts" / "token.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "wbso_calendar_config.json"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string from Google Calendar format."""
    try:
        # Google Calendar format: "2025-06-01T08:20:00+02:00" or "2025-06-01T08:20:00Z"
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        # Try alternative formats
        for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Could not parse datetime: {dt_str}")


def calculate_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> float:
    """Calculate overlap duration in hours between two time ranges."""
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start < overlap_end:
        overlap_duration = overlap_end - overlap_start
        return overlap_duration.total_seconds() / 3600.0

    return 0.0


def get_iso_week(dt: datetime) -> Tuple[str, int, int]:
    """Get ISO week number, year, and week number."""
    iso_year, iso_week, iso_weekday = dt.isocalendar()
    iso_week_str = f"{iso_year}-W{iso_week:02d}"
    return iso_week_str, iso_year, iso_week


def extract_calendar_events(uploader: GoogleCalendarUploader, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Extract all events from WBSO calendar in date range."""
    logger.info(f"Extracting events from {start_date.date()} to {end_date.date()}...")

    events = []
    page_token = None

    while True:
        try:
            # Query events
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
            events.extend(items)

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

        except Exception as e:
            logger.error(f"Error extracting events: {e}")
            break

    logger.info(f"Extracted {len(events)} events from calendar")
    return events


def detect_overlaps(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect overlapping calendar events."""
    overlaps = []

    for i, event1 in enumerate(events):
        start1_str = event1.get("start", {}).get("dateTime", "")
        end1_str = event1.get("end", {}).get("dateTime", "")

        if not start1_str or not end1_str:
            continue

        try:
            start1 = parse_datetime(start1_str)
            end1 = parse_datetime(end1_str)

            for j, event2 in enumerate(events[i + 1 :], start=i + 1):
                start2_str = event2.get("start", {}).get("dateTime", "")
                end2_str = event2.get("end", {}).get("dateTime", "")

                if not start2_str or not end2_str:
                    continue

                try:
                    start2 = parse_datetime(start2_str)
                    end2 = parse_datetime(end2_str)

                    overlap_hours = calculate_overlap(start1, end1, start2, end2)

                    if overlap_hours > 0:
                        overlaps.append(
                            {
                                "event1": {
                                    "id": event1.get("id", ""),
                                    "summary": event1.get("summary", ""),
                                    "start": start1_str,
                                    "end": end1_str,
                                    "session_id": event1.get("extendedProperties", {}).get("private", {}).get("session_id", ""),
                                },
                                "event2": {
                                    "id": event2.get("id", ""),
                                    "summary": event2.get("summary", ""),
                                    "start": start2_str,
                                    "end": end2_str,
                                    "session_id": event2.get("extendedProperties", {}).get("private", {}).get("session_id", ""),
                                },
                                "overlap_hours": overlap_hours,
                            }
                        )
                except Exception as e:
                    logger.warning(f"Error processing event2 for overlap: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error processing event1 for overlap: {e}")
            continue

    return overlaps


def group_by_week_and_title(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Group events by ISO week and title, summing hours."""
    grouped: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for event in events:
        start_str = event.get("start", {}).get("dateTime", "")
        if not start_str:
            continue

        try:
            start_dt = parse_datetime(start_str)
            iso_week_str, _, _ = get_iso_week(start_dt)

            # Get hours from extended properties or calculate from duration
            work_hours = 0.0
            private_props = event.get("extendedProperties", {}).get("private", {})
            if "work_hours" in private_props:
                try:
                    work_hours = float(private_props["work_hours"])
                except (ValueError, TypeError):
                    pass

            # If no work_hours in properties, calculate from duration
            if work_hours == 0.0:
                end_str = event.get("end", {}).get("dateTime", "")
                if end_str:
                    try:
                        end_dt = parse_datetime(end_str)
                        duration = end_dt - start_dt
                        work_hours = duration.total_seconds() / 3600.0
                    except Exception:
                        pass

            title = event.get("summary", "Unknown")
            grouped[iso_week_str][title] += work_hours

        except Exception as e:
            logger.warning(f"Error grouping event: {e}")
            continue

    return dict(grouped)


def generate_markdown_report(
    events: List[Dict[str, Any]], overlaps: List[Dict[str, Any]], grouped_data: Dict[str, Dict[str, float]]
) -> str:
    """Generate markdown report from calendar data."""
    lines = []

    # Header
    lines.append("# WBSO Calendar Analysis Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("This report is based on actual Google Calendar events.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary Statistics
    total_events = len(events)
    total_hours = sum(sum(week_data.values()) for week_data in grouped_data.values())
    total_weeks = len(grouped_data)
    total_activities = len(set(title for week_data in grouped_data.values() for title in week_data.keys()))

    lines.append("## Summary Statistics")
    lines.append("")
    lines.append(f"- **Total Events**: {total_events}")
    lines.append(f"- **Total Hours**: {total_hours:.2f}")
    lines.append(f"- **Total Weeks**: {total_weeks}")
    lines.append(f"- **Total Activities**: {total_activities}")
    lines.append(f"- **Overlapping Events**: {len(overlaps)}")
    lines.append("")

    # Overlapping Events Section
    if overlaps:
        lines.append("## ⚠️ Overlapping Events")
        lines.append("")
        lines.append("The following events have time overlaps:")
        lines.append("")
        lines.append("| Event 1 | Event 2 | Overlap (hours) |")
        lines.append("|---------|---------|-----------------|")

        for overlap in overlaps:
            e1 = overlap["event1"]
            e2 = overlap["event2"]
            e1_summary = e1["summary"][:40] + "..." if len(e1["summary"]) > 40 else e1["summary"]
            e2_summary = e2["summary"][:40] + "..." if len(e2["summary"]) > 40 else e2["summary"]
            lines.append(f"| {e1_summary} | {e2_summary} | {overlap['overlap_hours']:.2f} |")

        lines.append("")
        lines.append("### Detailed Overlap Information")
        lines.append("")

        for i, overlap in enumerate(overlaps, 1):
            e1 = overlap["event1"]
            e2 = overlap["event2"]
            lines.append(f"#### Overlap {i}")
            lines.append("")
            lines.append("**Event 1:**")
            lines.append(f"- Summary: {e1['summary']}")
            lines.append(f"- Session ID: {e1['session_id']}")
            lines.append(f"- Start: {e1['start']}")
            lines.append(f"- End: {e1['end']}")
            lines.append(f"- Calendar ID: {e1['id']}")
            lines.append("")
            lines.append("**Event 2:**")
            lines.append(f"- Summary: {e2['summary']}")
            lines.append(f"- Session ID: {e2['session_id']}")
            lines.append(f"- Start: {e2['start']}")
            lines.append(f"- End: {e2['end']}")
            lines.append(f"- Calendar ID: {e2['id']}")
            lines.append("")
            lines.append(f"**Overlap:** {overlap['overlap_hours']:.2f} hours")
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("## ✅ No Overlapping Events")
        lines.append("")
        lines.append("All calendar events are non-overlapping.")
        lines.append("")

    # Weekly Breakdown
    lines.append("## Weekly Breakdown")
    lines.append("")

    sorted_weeks = sorted(grouped_data.keys(), key=lambda w: (int(w.split("-")[0]), int(w.split("-W")[1])))

    for week in sorted_weeks:
        week_data = grouped_data[week]
        week_total = sum(week_data.values())

        lines.append(f"### {week}")
        lines.append("")
        lines.append(f"**Total Hours**: {week_total:.1f}")
        lines.append("")
        lines.append("| Activity | Hours |")
        lines.append("|----------|-------|")

        # Sort activities by hours (descending)
        sorted_activities = sorted(week_data.items(), key=lambda x: x[1], reverse=True)

        for title, hours in sorted_activities:
            # Escape pipe characters in title for markdown table
            title_escaped = title.replace("|", "\\|")
            lines.append(f"| {title_escaped} | {hours:.2f} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Activity Totals
    lines.append("## Activity Totals (All Weeks)")
    lines.append("")
    lines.append("| Activity | Total Hours | Weeks Active |")
    lines.append("|----------|-------------|--------------|")

    activity_totals: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0.0, 0))

    for week_data in grouped_data.values():
        for title, hours in week_data.items():
            current_total, current_weeks = activity_totals[title]
            activity_totals[title] = (current_total + hours, current_weeks + 1)

    # Sort by total hours (descending)
    sorted_activities = sorted(activity_totals.items(), key=lambda x: x[1][0], reverse=True)

    for title, (total_hours, weeks_active) in sorted_activities:
        title_escaped = title.replace("|", "\\|")
        lines.append(f"| {title_escaped} | {total_hours:.2f} | {weeks_active} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Week Totals
    lines.append("## Week Totals")
    lines.append("")
    lines.append("| Week | Total Hours | Activities |")
    lines.append("|------|-------------|-----------|")

    for week in sorted_weeks:
        week_data = grouped_data[week]
        week_total = sum(week_data.values())
        activity_count = len(week_data)
        lines.append(f"| {week} | {week_total:.1f} | {activity_count} |")

    lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract and analyze Google Calendar events")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD), defaults to 2025-06-01")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--output-file", type=Path, default=None, help="Output markdown file path")
    args = parser.parse_args()

    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime(2025, 6, 1)

    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = datetime.now()

    logger.info("=" * 60)
    logger.info("CALENDAR EXTRACTION AND ANALYSIS")
    logger.info("=" * 60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info("")

    # Initialize uploader for authentication
    uploader = GoogleCalendarUploader(CREDENTIALS_PATH, TOKEN_PATH, CONFIG_PATH)
    if not uploader.authenticate():
        logger.error("Authentication failed")
        return 1

    if not uploader.get_wbso_calendar_id():
        logger.error("WBSO calendar not found or no read access")
        return 1

    # Extract events
    events = extract_calendar_events(uploader, start_date, end_date)

    if not events:
        logger.warning("No events found in calendar")
        return 1

    # Detect overlaps
    logger.info("Detecting overlapping events...")
    overlaps = detect_overlaps(events)
    logger.info(f"Found {len(overlaps)} overlapping event pairs")

    # Group by week and title
    logger.info("Grouping events by week and title...")
    grouped_data = group_by_week_and_title(events)

    # Generate report
    logger.info("Generating markdown report...")
    markdown = generate_markdown_report(events, overlaps, grouped_data)

    # Save report
    if args.output_file:
        output_file = args.output_file
    else:
        output_file = OUTPUT_DIR / "CALENDAR_ANALYSIS_REPORT.md"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info(f"✅ Report saved to: {output_file}")

    # Save raw data as JSON for inspection
    json_file = OUTPUT_DIR / "calendar_events_extracted.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "extracted_at": datetime.now().isoformat(),
                "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "total_events": len(events),
                "overlaps": overlaps,
                "events": events,
            },
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    logger.info(f"✅ Raw data saved to: {json_file}")

    # Print summary
    total_hours = sum(sum(week_data.values()) for week_data in grouped_data.values())
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total events: {len(events)}")
    logger.info(f"Total hours: {total_hours:.2f}")
    logger.info(f"Overlapping pairs: {len(overlaps)}")
    logger.info(f"Weeks: {len(grouped_data)}")
    logger.info("")

    if overlaps:
        logger.warning(f"⚠️  {len(overlaps)} overlapping event pairs detected - see report for details")
        return 1
    else:
        logger.info("✅ No overlapping events detected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
