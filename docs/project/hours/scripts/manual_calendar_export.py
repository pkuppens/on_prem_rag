#!/usr/bin/env python3
"""
Manual Calendar Export Processor for WBSO Hours Registration

This script processes manually exported Google Calendar data (CSV or iCal format)
as an alternative to the API approach. It provides the same categorization and
conflict detection capabilities.

See docs/project/hours/TASK-005-GOOGLE-CALENDAR-INTEGRATION.md for detailed requirements.
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("manual_calendar_export.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ManualCalendarProcessor:
    """Process manually exported Google Calendar data for WBSO hours registration."""

    def __init__(self, config_dir: str = "../config"):
        """Initialize the manual calendar processor with configuration.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.events = []

        # Load configuration files
        self.categorization_rules = self._load_config("calendar_categorization_rules.json")
        self.conflict_rules = self._load_config("conflict_detection_rules.json")
        self.wbso_config = self._load_config("wbso_calendar_config.json")

    def _load_config(self, filename: str) -> Dict:
        """Load configuration file from JSON.

        Args:
            filename: Configuration file name

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If configuration file doesn't exist
        """
        config_path = self.config_dir / filename
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def process_google_calendar_csv(self, csv_file: str) -> List[Dict]:
        """Process Google Calendar CSV export file.

        Args:
            csv_file: Path to Google Calendar CSV export file

        Returns:
            List of processed calendar events
        """
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return []

        events = []

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    processed_event = self._process_csv_row(row)
                    if processed_event:
                        events.append(processed_event)

            logger.info(f"Processed {len(events)} events from CSV file")
            self.events = events
            return events

        except Exception as e:
            logger.error(f"Failed to process CSV file: {e}")
            return []

    def _process_csv_row(self, row: Dict) -> Optional[Dict]:
        """Process a single CSV row from Google Calendar export.

        Args:
            row: CSV row dictionary

        Returns:
            Processed event dictionary or None if invalid
        """
        try:
            # Extract basic information
            title = row.get("Subject", row.get("Summary", "Untitled Event"))
            description = row.get("Description", "")
            location = row.get("Location", "")

            # Parse start and end times
            start_time = self._parse_csv_datetime(row.get("Start Date", ""), row.get("Start Time", ""))
            end_time = self._parse_csv_datetime(row.get("End Date", ""), row.get("End Time", ""))

            if not start_time or not end_time:
                logger.warning(f"Skipping event with invalid times: {title}")
                return None

            # Calculate duration
            duration = int((end_time - start_time).total_seconds() / 60)

            # Get calendar information (from filename or default)
            calendar_name = row.get("Calendar", "Personal")

            # Categorize event
            event_type, is_declarable, conflict_type = self._categorize_event(title, description, calendar_name, duration)

            # Build processed event
            processed_event = {
                "DateTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "EventTitle": title,
                "CalendarName": calendar_name,
                "EventType": event_type,
                "Duration": duration,
                "Description": description,
                "Location": location,
                "Attendees": row.get("Attendees", ""),
                "Color": "#4285F4",  # Default color
                "IsDeclarable": is_declarable,
                "ConflictType": conflict_type,
                "Notes": self._generate_notes(event_type, is_declarable, conflict_type),
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat(),
            }

            return processed_event

        except Exception as e:
            logger.error(f"Failed to process CSV row: {e}")
            return None

    def _parse_csv_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time from Google Calendar CSV export.

        Args:
            date_str: Date string (e.g., "1/15/2025")
            time_str: Time string (e.g., "9:00 AM")

        Returns:
            Parsed datetime or None if invalid
        """
        try:
            if not date_str:
                return None

            # Parse date
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")

            # Parse time if provided
            if time_str:
                time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                return datetime.combine(date_obj.date(), time_obj)
            else:
                # All-day event
                return datetime.combine(date_obj.date(), datetime.min.time())

        except Exception as e:
            logger.error(f"Failed to parse datetime: {date_str} {time_str} - {e}")
            return None

    def _categorize_event(self, title: str, description: str, calendar_name: str, duration: int) -> Tuple[str, bool, str]:
        """Categorize event as declarable/non-declarable and determine conflict type.

        Args:
            title: Event title
            description: Event description
            calendar_name: Calendar name
            duration: Event duration in minutes

        Returns:
            Tuple of (event_type, is_declarable, conflict_type)
        """
        # Combine text for keyword matching
        text = f"{title} {description} {calendar_name}".lower()

        # Check non-declarable categories first (higher priority)
        non_declarable = self.categorization_rules.get("non_declarable_categories", {})
        for category, config in non_declarable.items():
            keywords = config.get("keywords", [])
            calendar_names = config.get("calendar_names", [])

            # Check keywords
            if any(keyword.lower() in text for keyword in keywords):
                return category, False, config.get("conflict_type", "personal")

            # Check calendar names
            if any(cal_name.lower() in calendar_name.lower() for cal_name in calendar_names):
                return category, False, config.get("conflict_type", "personal")

        # Check declarable categories
        declarable = self.categorization_rules.get("declarable_categories", {})
        for category, config in declarable.items():
            keywords = config.get("keywords", [])
            calendar_names = config.get("calendar_names", [])

            # Check keywords
            if any(keyword.lower() in text for keyword in keywords):
                return category, True, "None"

            # Check calendar names
            if any(cal_name.lower() in calendar_name.lower() for cal_name in calendar_names):
                return category, True, "None"

        # Default categorization
        default_category = self.categorization_rules.get("categorization_rules", {}).get("default_category", "work_sessions")
        return default_category, True, "None"

    def _generate_notes(self, event_type: str, is_declarable: bool, conflict_type: str) -> str:
        """Generate notes for the event based on categorization.

        Args:
            event_type: Categorized event type
            is_declarable: Whether event is WBSO declarable
            conflict_type: Type of conflict if any

        Returns:
            Notes string
        """
        if is_declarable:
            return f"WBSO {event_type.replace('_', ' ').title()}"
        else:
            return f"Non-declarable: {conflict_type}"

    def export_to_csv(self, output_file: str = "../data/calendar_events_2025.csv") -> bool:
        """Export events to CSV file.

        Args:
            output_file: Output CSV file path

        Returns:
            True if export was successful
        """
        if not self.events:
            logger.error("No events to export. Process calendar data first.")
            return False

        try:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Define CSV columns
            fieldnames = [
                "DateTime",
                "EventTitle",
                "CalendarName",
                "EventType",
                "Duration",
                "Description",
                "Location",
                "Attendees",
                "Color",
                "IsDeclarable",
                "ConflictType",
                "Notes",
            ]

            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for event in self.events:
                    # Only write standard fields to CSV
                    csv_event = {field: event.get(field, "") for field in fieldnames}
                    writer.writerow(csv_event)

            logger.info(f"Exported {len(self.events)} events to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export events to CSV: {e}")
            return False

    def generate_summary_report(self, output_file: str = "../data/calendar_summary_report.md") -> bool:
        """Generate a summary report of processed calendar data.

        Args:
            output_file: Output markdown file path

        Returns:
            True if report generation was successful
        """
        if not self.events:
            logger.error("No events to report. Process calendar data first.")
            return False

        try:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Calculate statistics
            total_events = len(self.events)
            declarable_events = sum(1 for event in self.events if event["IsDeclarable"])
            non_declarable_events = total_events - declarable_events

            total_declarable_hours = sum(event["Duration"] for event in self.events if event["IsDeclarable"]) / 60

            total_non_declarable_hours = sum(event["Duration"] for event in self.events if not event["IsDeclarable"]) / 60

            # Calendar breakdown
            calendar_counts = {}
            for event in self.events:
                calendar_name = event["CalendarName"]
                calendar_counts[calendar_name] = calendar_counts.get(calendar_name, 0) + 1

            # Conflict analysis
            conflict_counts = {}
            for event in self.events:
                conflict_type = event["ConflictType"]
                conflict_counts[conflict_type] = conflict_counts.get(conflict_type, 0) + 1

            # Generate report
            report = f"""# Calendar Analysis Report - Manual Export

## Summary Statistics
- Total Events: {total_events:,}
- Declarable Events: {declarable_events:,}
- Non-Declarable Events: {non_declarable_events:,}
- Total Declarable Hours: {total_declarable_hours:.1f}
- Total Non-Declarable Hours: {total_non_declarable_hours:.1f}

## Calendar Sources
"""

            for calendar_name, count in sorted(calendar_counts.items()):
                report += f"- {calendar_name}: {count:,} events\n"

            report += "\n## Conflict Analysis\n"
            for conflict_type, count in sorted(conflict_counts.items()):
                report += f"- {conflict_type}: {count:,} events\n"

            report += """
## Event Type Breakdown
"""

            event_type_counts = {}
            for event in self.events:
                event_type = event["EventType"]
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            for event_type, count in sorted(event_type_counts.items()):
                report += f"- {event_type}: {count:,} events\n"

            # Write report
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"Generated summary report: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            return False


def main():
    """Main function to run the manual calendar processing."""
    print("Manual Calendar Export Processor for WBSO Hours Registration")
    print("=" * 65)

    # Initialize processor
    processor = ManualCalendarProcessor()

    # Get input file
    csv_file = input("\nEnter the path to your Google Calendar CSV export file: ").strip()

    if not csv_file:
        print("No file specified. Exiting.")
        return

    # Process CSV file
    print(f"\n1. Processing CSV file: {csv_file}")
    events = processor.process_google_calendar_csv(csv_file)

    if not events:
        print("No events processed. Check the file format and try again.")
        return

    print(f"Processed {len(events)} events")

    # Export to CSV
    print("\n2. Exporting events to CSV...")
    if processor.export_to_csv():
        print("Events exported successfully")
    else:
        print("Failed to export events")

    # Generate summary report
    print("\n3. Generating summary report...")
    if processor.generate_summary_report():
        print("Summary report generated successfully")
    else:
        print("Failed to generate summary report")

    print("\nManual calendar processing completed!")
    print("Check the data/ directory for output files.")


if __name__ == "__main__":
    main()
