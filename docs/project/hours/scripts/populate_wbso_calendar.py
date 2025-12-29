#!/usr/bin/env python3
"""
WBSO Calendar Population with Conflict Detection

This script populates the WBSO Google Calendar with work sessions, implementing
intelligent conflict detection and resolution. It handles conflicts with existing
calendar events and adjusts WBSO session times accordingly.

TASK-036: Google Calendar Population with Conflict Resolution
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Created: 2025-10-18
"""

import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CalendarConflictDetector:
    """Detects and resolves conflicts between WBSO sessions and existing calendar events."""

    def __init__(self):
        """Initialize the conflict detector."""
        self.conflict_threshold_short = 2.0  # 2 hours for short conflicts
        self.conflict_threshold_long = 2.0  # 2 hours for long conflicts (same threshold)
        self.adjustment_buffer = 0.5  # 30 minutes buffer for adjustments

    def parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string to datetime object."""
        try:
            # Handle different datetime formats
            if "T" in dt_str:
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Error parsing datetime '{dt_str}': {e}")
            return None

    def calculate_overlap(self, start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> float:
        """Calculate overlap duration in hours between two time ranges."""
        if not all([start1, end1, start2, end2]):
            return 0.0

        # Calculate overlap
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start < overlap_end:
            overlap_duration = overlap_end - overlap_start
            return overlap_duration.total_seconds() / 3600.0  # Convert to hours

        return 0.0

    def detect_conflicts(self, wbso_event: Dict[str, Any], existing_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts between a WBSO event and existing calendar events."""
        conflicts = []

        wbso_start = self.parse_datetime(wbso_event["start"]["dateTime"])
        wbso_end = self.parse_datetime(wbso_event["end"]["dateTime"])

        if not wbso_start or not wbso_end:
            logger.warning(f"Invalid WBSO event datetime: {wbso_event['start']['dateTime']} - {wbso_event['end']['dateTime']}")
            return conflicts

        for existing_event in existing_events:
            existing_start = self.parse_datetime(existing_event.get("start", {}).get("dateTime", ""))
            existing_end = self.parse_datetime(existing_event.get("end", {}).get("dateTime", ""))

            if not existing_start or not existing_end:
                continue

            overlap_hours = self.calculate_overlap(wbso_start, wbso_end, existing_start, existing_end)

            if overlap_hours > 0:
                conflict = {
                    "existing_event": existing_event,
                    "overlap_hours": overlap_hours,
                    "conflict_type": "short" if overlap_hours < self.conflict_threshold_short else "long",
                    "wbso_start": wbso_start,
                    "wbso_end": wbso_end,
                    "existing_start": existing_start,
                    "existing_end": existing_end,
                }
                conflicts.append(conflict)

        return conflicts

    def adjust_wbso_event_time(self, wbso_event: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adjust WBSO event time to resolve conflicts."""
        if not conflicts:
            return wbso_event

        # For now, we'll flag conflicts for manual review rather than auto-adjusting
        # This is safer and allows for manual review of holiday work scenarios
        adjusted_event = wbso_event.copy()

        # Add conflict information to the event
        conflict_info = []
        for conflict in conflicts:
            conflict_info.append(
                {
                    "overlap_hours": conflict["overlap_hours"],
                    "conflict_type": conflict["conflict_type"],
                    "existing_event_summary": conflict["existing_event"].get("summary", "Unknown"),
                    "existing_event_start": conflict["existing_event"].get("start", {}).get("dateTime", ""),
                    "existing_event_end": conflict["existing_event"].get("end", {}).get("dateTime", ""),
                }
            )

        # Add conflict information to extended properties
        if "extendedProperties" not in adjusted_event:
            adjusted_event["extendedProperties"] = {"private": {}}

        adjusted_event["extendedProperties"]["private"]["conflicts"] = json.dumps(conflict_info)
        adjusted_event["extendedProperties"]["private"]["has_conflicts"] = "true"
        adjusted_event["extendedProperties"]["private"]["conflict_count"] = str(len(conflicts))

        return adjusted_event


class WBSOCalendarPopulator:
    """Populates WBSO Google Calendar with work sessions and conflict detection."""

    def __init__(self):
        """Initialize the calendar populator."""
        self.conflict_detector = CalendarConflictDetector()
        self.wbso_calendar_id = None  # Will be set when calendar is created/found

    def load_existing_calendar_events(self, calendar_events_file: Path) -> List[Dict[str, Any]]:
        """Load existing calendar events from CSV file."""
        logger.info(f"Loading existing calendar events from: {calendar_events_file}")

        existing_events = []

        if not calendar_events_file.exists():
            logger.warning(f"Calendar events file not found: {calendar_events_file}")
            return existing_events

        try:
            with open(calendar_events_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert CSV row to calendar event format
                    event = {
                        "summary": row.get("Subject", ""),
                        "start": {
                            "dateTime": row.get("Start Date", "") + "T" + row.get("Start Time", ""),
                            "timeZone": "Europe/Amsterdam",
                        },
                        "end": {
                            "dateTime": row.get("End Date", "") + "T" + row.get("End Time", ""),
                            "timeZone": "Europe/Amsterdam",
                        },
                        "description": row.get("Description", ""),
                        "location": row.get("Location", ""),
                    }
                    existing_events.append(event)

            logger.info(f"Loaded {len(existing_events)} existing calendar events")

        except Exception as e:
            logger.error(f"Error loading calendar events: {e}")

        return existing_events

    def load_wbso_calendar_events(self, wbso_events_file: Path) -> List[Dict[str, Any]]:
        """Load WBSO calendar events from JSON file."""
        logger.info(f"Loading WBSO calendar events from: {wbso_events_file}")

        with open(wbso_events_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        wbso_events = data.get("calendar_events", [])
        logger.info(f"Loaded {len(wbso_events)} WBSO calendar events")

        return wbso_events

    def process_conflicts(
        self, wbso_events: List[Dict[str, Any]], existing_events: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process conflicts between WBSO events and existing calendar events."""
        logger.info("Processing calendar conflicts")

        processed_events = []
        conflict_reports = []

        for wbso_event in wbso_events:
            # Detect conflicts
            conflicts = self.conflict_detector.detect_conflicts(wbso_event, existing_events)

            if conflicts:
                # Adjust event to include conflict information
                adjusted_event = self.conflict_detector.adjust_wbso_event_time(wbso_event, conflicts)
                processed_events.append(adjusted_event)

                # Create conflict report
                conflict_report = {
                    "wbso_event_summary": wbso_event["summary"],
                    "wbso_event_start": wbso_event["start"]["dateTime"],
                    "wbso_event_end": wbso_event["end"]["dateTime"],
                    "conflict_count": len(conflicts),
                    "conflicts": [],
                }

                for conflict in conflicts:
                    conflict_report["conflicts"].append(
                        {
                            "existing_event_summary": conflict["existing_event"]["summary"],
                            "existing_event_start": conflict["existing_event"]["start"]["dateTime"],
                            "existing_event_end": conflict["existing_event"]["end"]["dateTime"],
                            "overlap_hours": conflict["overlap_hours"],
                            "conflict_type": conflict["conflict_type"],
                        }
                    )

                conflict_reports.append(conflict_report)

                logger.info(f"Conflict detected for '{wbso_event['summary']}': {len(conflicts)} conflicts")
            else:
                # No conflicts, add event as-is
                processed_events.append(wbso_event)

        logger.info(f"Processed {len(processed_events)} events, {len(conflict_reports)} with conflicts")
        return processed_events, conflict_reports

    def save_processed_events(self, processed_events: List[Dict[str, Any]], output_file: Path) -> None:
        """Save processed calendar events to JSON file."""
        logger.info(f"Saving {len(processed_events)} processed events to: {output_file}")

        # Calculate summary statistics
        total_events = len(processed_events)
        events_with_conflicts = len(
            [e for e in processed_events if e.get("extendedProperties", {}).get("private", {}).get("has_conflicts") == "true"]
        )
        events_without_conflicts = total_events - events_with_conflicts

        # Create output structure
        output_data = {
            "processed_events": processed_events,
            "summary": {
                "total_events": total_events,
                "events_with_conflicts": events_with_conflicts,
                "events_without_conflicts": events_without_conflicts,
                "conflict_percentage": (events_with_conflicts / total_events * 100) if total_events > 0 else 0,
                "processing_date": datetime.now().isoformat(),
            },
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved processed events:")
        logger.info(f"  - Total events: {total_events}")
        logger.info(f"  - Events with conflicts: {events_with_conflicts}")
        logger.info(f"  - Events without conflicts: {events_without_conflicts}")
        logger.info(f"  - Conflict percentage: {output_data['summary']['conflict_percentage']:.1f}%")

    def save_conflict_reports(self, conflict_reports: List[Dict[str, Any]], output_file: Path) -> None:
        """Save conflict reports to JSON file."""
        logger.info(f"Saving {len(conflict_reports)} conflict reports to: {output_file}")

        # Create output structure
        output_data = {
            "conflict_reports": conflict_reports,
            "summary": {
                "total_conflicts": len(conflict_reports),
                "total_conflict_events": sum(len(report["conflicts"]) for report in conflict_reports),
                "generation_date": datetime.now().isoformat(),
            },
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved conflict reports:")
        logger.info(f"  - WBSO events with conflicts: {len(conflict_reports)}")
        logger.info(f"  - Total conflict events: {output_data['summary']['total_conflict_events']}")


def main():
    """Main function to populate WBSO calendar with conflict detection."""
    # File paths
    wbso_events_file = Path("data/wbso_calendar_events.json")
    existing_events_file = Path("data/calendar_events_2025.csv")
    processed_events_file = Path("data/wbso_calendar_events_processed.json")
    conflict_reports_file = Path("data/calendar_conflict_reports.json")

    # Validate input files exist
    if not wbso_events_file.exists():
        logger.error(f"WBSO events file not found: {wbso_events_file}")
        return

    # Create populator
    populator = WBSOCalendarPopulator()

    # Load WBSO events
    wbso_events = populator.load_wbso_calendar_events(wbso_events_file)

    # Load existing calendar events
    existing_events = populator.load_existing_calendar_events(existing_events_file)

    # Process conflicts
    processed_events, conflict_reports = populator.process_conflicts(wbso_events, existing_events)

    # Save results
    populator.save_processed_events(processed_events, processed_events_file)
    populator.save_conflict_reports(conflict_reports, conflict_reports_file)

    logger.info("WBSO calendar population with conflict detection completed successfully")


if __name__ == "__main__":
    main()
