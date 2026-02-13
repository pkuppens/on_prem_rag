#!/usr/bin/env python3
"""
Generate Weekly WBSO Report

Generates markdown report with weekly breakdown of activities/subactivities and totals.

Author: AI Assistant
Created: 2025-11-30
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .logging_config import get_logger

logger = get_logger("generate_weekly_report")

# Default paths
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "data"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "output"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"
SESSION_SUBACTIVITY_CSV = OUTPUT_DIR / "session_subactivity_mapping.csv"
WEEKLY_REPORT_MD = OUTPUT_DIR / "weekly_wbso_report.md"


def generate_weekly_report(
    calendar_events_csv: Optional[Path] = None,
    session_subactivity_csv: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate weekly markdown report with activities/subactivities breakdown.

    Args:
        calendar_events_csv: Path to calendar events CSV
        session_subactivity_csv: Path to session-subactivity mapping CSV
        output_path: Output markdown path (uses default if None)

    Returns:
        Path to generated markdown file
    """
    calendar_events_csv = calendar_events_csv or CALENDAR_EVENTS_CSV
    session_subactivity_csv = session_subactivity_csv or SESSION_SUBACTIVITY_CSV
    output_path = output_path or WEEKLY_REPORT_MD
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load calendar events
    calendar_events = []
    if calendar_events_csv.exists():
        try:
            with open(calendar_events_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                calendar_events = list(reader)
            logger.info(f"Loaded {len(calendar_events)} calendar events")
        except Exception as e:
            logger.error(f"Error loading calendar events: {e}")
    else:
        logger.warning(f"Calendar events CSV not found: {calendar_events_csv}")

    # Load session-subactivity mapping
    session_subactivity_map: Dict[str, Dict[str, Any]] = {}
    if session_subactivity_csv.exists():
        try:
            with open(session_subactivity_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session_id = row.get("session_id", "")
                    if session_id:
                        session_subactivity_map[session_id] = row
            logger.info(f"Loaded {len(session_subactivity_map)} session-subactivity mappings")
        except Exception as e:
            logger.error(f"Error loading session-subactivity mapping: {e}")
    else:
        logger.warning(f"Session-subactivity CSV not found: {session_subactivity_csv}")

    # Group by week
    weekly_data: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "activities": defaultdict(lambda: {"sub_activities": defaultdict(float), "total_hours": 0.0}),
            "total_hours": 0.0,
            "event_count": 0,
        }
    )

    for event in calendar_events:
        session_id = event.get("session_id", "")
        iso_week_number = event.get("iso_week_number", "")
        hours = float(event.get("hours", 0.0))

        if not iso_week_number:
            continue

        weekly_data[iso_week_number]["total_hours"] += hours
        weekly_data[iso_week_number]["event_count"] += 1

        # Get activity/subactivity info
        if session_id in session_subactivity_map:
            mapping = session_subactivity_map[session_id]
            activity_name = mapping.get("activity_name_nl", "")
            sub_activity_name = mapping.get("sub_activity_name_nl", "")

            if activity_name:
                weekly_data[iso_week_number]["activities"][activity_name]["total_hours"] += hours
                if sub_activity_name:
                    weekly_data[iso_week_number]["activities"][activity_name]["sub_activities"][sub_activity_name] += hours

    # Generate markdown
    lines = []
    lines.append("# WBSO Weekly Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sort weeks
    sorted_weeks = sorted(weekly_data.keys())

    # Weekly breakdown
    for week in sorted_weeks:
        week_data = weekly_data[week]
        lines.append(f"## Week {week}")
        lines.append("")
        lines.append(f"**Total Hours:** {week_data['total_hours']:.2f} hours")
        lines.append(f"**Event Count:** {week_data['event_count']}")
        lines.append("")

        # Activities in this week
        if week_data["activities"]:
            lines.append("### Activities")
            lines.append("")

            for activity_name in sorted(week_data["activities"].keys()):
                activity_data = week_data["activities"][activity_name]
                activity_hours = activity_data["total_hours"]
                lines.append(f"#### {activity_name}")
                lines.append(f"**Hours:** {activity_hours:.2f}")
                lines.append("")

                # Sub-activities
                if activity_data["sub_activities"]:
                    lines.append("**Sub-Activities:**")
                    lines.append("")
                    for sub_activity_name in sorted(activity_data["sub_activities"].keys()):
                        sub_hours = activity_data["sub_activities"][sub_activity_name]
                        lines.append(f"- {sub_activity_name}: {sub_hours:.2f} hours")
                    lines.append("")

        lines.append("---")
        lines.append("")

    # Summary totals
    lines.append("## Summary Totals")
    lines.append("")

    # Total by activity
    activity_totals: Dict[str, float] = defaultdict(float)
    sub_activity_totals: Dict[Tuple[str, str], float] = defaultdict(float)

    for week_data in weekly_data.values():
        for activity_name, activity_data in week_data["activities"].items():
            activity_totals[activity_name] += activity_data["total_hours"]
            for sub_activity_name, sub_hours in activity_data["sub_activities"].items():
                sub_activity_totals[(activity_name, sub_activity_name)] += sub_hours

    lines.append("### Total Hours by Activity")
    lines.append("")
    for activity_name in sorted(activity_totals.keys()):
        total = activity_totals[activity_name]
        lines.append(f"- **{activity_name}:** {total:.2f} hours")
    lines.append("")

    lines.append("### Total Hours by Sub-Activity")
    lines.append("")
    for activity_name, sub_activity_name in sorted(sub_activity_totals.keys()):
        total = sub_activity_totals[(activity_name, sub_activity_name)]
        lines.append(f"- **{activity_name} - {sub_activity_name}:** {total:.2f} hours")
    lines.append("")

    # Grand total
    grand_total = sum(week_data["total_hours"] for week_data in weekly_data.values())
    total_events = sum(week_data["event_count"] for week_data in weekly_data.values())
    lines.append("### Grand Total")
    lines.append("")
    lines.append(f"**Total Hours:** {grand_total:.2f} hours")
    lines.append(f"**Total Events:** {total_events}")
    lines.append(f"**Weeks Covered:** {len(sorted_weeks)}")
    lines.append("")

    # Write markdown file
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Generated weekly report: {output_path}")
    return output_path


def main():
    """Main entry point for standalone execution."""
    output_path = generate_weekly_report()
    print(f"Weekly report generated: {output_path}")


if __name__ == "__main__":
    main()
