#!/usr/bin/env python3
"""
Google Calendar Extractor for WBSO Hours Registration

This script extracts calendar events from Google Calendar for WBSO hours registration,
including personal, subscribed, and shared calendars. It provides comprehensive
calendar data extraction with conflict detection capabilities.

See docs/project/hours/TASK-005-GOOGLE-CALENDAR-INTEGRATION.md for detailed requirements.
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request  # type: ignore
    from google.oauth2.credentials import Credentials  # type: ignore
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.errors import HttpError  # type: ignore
except ImportError as e:
    print(f"Missing Google Calendar API dependencies: {e}")
    print("Please install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("calendar_extraction.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class GoogleCalendarExtractor:
    """Extract and process Google Calendar events for WBSO hours registration."""

    def __init__(self, config_dir: str = "../config"):
        """Initialize the calendar extractor with configuration.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.service = None
        self.calendars = {}
        self.events = []

        # Load configuration files
        self.categorization_rules = self._load_config("calendar_categorization_rules.json")
        self.conflict_rules = self._load_config("conflict_detection_rules.json")
        self.wbso_config = self._load_config("wbso_calendar_config.json")

        # API configuration
        self.SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        self.CREDENTIALS_FILE = "credentials.json"
        self.TOKEN_FILE = "token.json"

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

    def setup_api_access(self) -> bool:
        """Set up Google Calendar API access using OAuth2.

        Returns:
            True if API access is successfully established
        """
        creds = None

        # Check if token file exists
        if os.path.exists(self.TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load existing credentials: {e}")

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    logger.error(f"Credentials file not found: {self.CREDENTIALS_FILE}")
                    logger.error("Please download credentials.json from Google Cloud Console")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS_FILE, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("Obtained new credentials via OAuth flow")
                except Exception as e:
                    logger.error(f"Failed to obtain credentials: {e}")
                    return False

            # Save credentials for next run
            try:
                with open(self.TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials to token file")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")

        # Build the service
        try:
            self.service = build("calendar", "v3", credentials=creds)
            logger.info("Successfully built Google Calendar service")
            return True
        except Exception as e:
            logger.error(f"Failed to build calendar service: {e}")
            return False

    def discover_calendars(self) -> Dict[str, Dict]:
        """Discover all accessible calendars.

        Returns:
            Dictionary of calendar information
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return {}

        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = {}

            for calendar in calendar_list.get("items", []):
                calendar_id = calendar["id"]
                calendar_info = {
                    "id": calendar_id,
                    "summary": calendar.get("summary", "Unknown"),
                    "description": calendar.get("description", ""),
                    "accessRole": calendar.get("accessRole", "none"),
                    "primary": calendar.get("primary", False),
                    "selected": calendar.get("selected", False),
                    "backgroundColor": calendar.get("backgroundColor", "#4285F4"),
                    "foregroundColor": calendar.get("foregroundColor", "#ffffff"),
                }
                calendars[calendar_id] = calendar_info

                logger.info(f"Discovered calendar: {calendar_info['summary']} ({calendar_id})")

            self.calendars = calendars
            logger.info(f"Discovered {len(calendars)} calendars")
            return calendars

        except HttpError as e:
            logger.error(f"Failed to discover calendars: {e}")
            return {}

    def extract_calendar_events(self, calendar_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Extract events from a specific calendar.

        Args:
            calendar_id: Google Calendar ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of calendar events
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return []

        events = []
        page_token = None

        try:
            while True:
                # Build time range
                time_min = f"{start_date}T00:00:00Z"
                time_max = f"{end_date}T23:59:59Z"

                # Get events
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy="startTime",
                        pageToken=page_token,
                    )
                    .execute()
                )

                # Process events
                for event in events_result.get("items", []):
                    processed_event = self._process_event(event, calendar_id)
                    if processed_event:
                        events.append(processed_event)

                # Check for more pages
                page_token = events_result.get("nextPageToken")
                if not page_token:
                    break

            logger.info(f"Extracted {len(events)} events from calendar {calendar_id}")
            return events

        except HttpError as e:
            logger.error(f"Failed to extract events from calendar {calendar_id}: {e}")
            return []

    def _process_event(self, event: Dict, calendar_id: str) -> Optional[Dict]:
        """Process a raw calendar event into standardized format.

        Args:
            event: Raw event from Google Calendar API
            calendar_id: Calendar ID for the event

        Returns:
            Processed event dictionary or None if invalid
        """
        try:
            # Extract basic event information
            event_id = event.get("id", "")
            title = event.get("summary", "Untitled Event")
            description = event.get("description", "")
            location = event.get("location", "")

            # Process start and end times
            start_time, end_time = self._parse_event_times(event)
            if not start_time or not end_time:
                logger.warning(f"Skipping event with invalid times: {title}")
                return None

            # Calculate duration
            duration = int((end_time - start_time).total_seconds() / 60)

            # Extract attendees
            attendees = []
            for attendee in event.get("attendees", []):
                attendees.append(attendee.get("email", ""))

            # Get calendar information
            calendar_info = self.calendars.get(calendar_id, {})
            calendar_name = calendar_info.get("summary", "Unknown")
            calendar_color = calendar_info.get("backgroundColor", "#4285F4")

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
                "Attendees": ",".join(attendees),
                "Color": calendar_color,
                "IsDeclarable": is_declarable,
                "ConflictType": conflict_type,
                "Notes": self._generate_notes(event_type, is_declarable, conflict_type),
                "EventId": event_id,
                "CalendarId": calendar_id,
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat(),
            }

            return processed_event

        except Exception as e:
            logger.error(f"Failed to process event {event.get('id', 'unknown')}: {e}")
            return None

    def _parse_event_times(self, event: Dict) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse start and end times from event.

        Args:
            event: Raw event from Google Calendar API

        Returns:
            Tuple of (start_time, end_time) or (None, None) if invalid
        """
        try:
            # Parse start time
            start_data = event.get("start", {})
            if "dateTime" in start_data:
                start_time = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
            elif "date" in start_data:
                start_time = datetime.fromisoformat(start_data["date"] + "T00:00:00+00:00")
            else:
                return None, None

            # Parse end time
            end_data = event.get("end", {})
            if "dateTime" in end_data:
                end_time = datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00"))
            elif "date" in end_data:
                end_time = datetime.fromisoformat(end_data["date"] + "T23:59:59+00:00")
            else:
                return None, None

            return start_time, end_time

        except Exception as e:
            logger.error(f"Failed to parse event times: {e}")
            return None, None

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

    def extract_all_events(self, year: int = 2025) -> List[Dict]:
        """Extract all events from all accessible calendars for a specific year.

        Args:
            year: Year to extract events for

        Returns:
            List of all processed events
        """
        if not self.calendars:
            logger.error("No calendars discovered. Run discover_calendars() first.")
            return []

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        all_events = []

        for calendar_id, calendar_info in self.calendars.items():
            logger.info(f"Extracting events from calendar: {calendar_info['summary']}")

            events = self.extract_calendar_events(calendar_id, start_date, end_date)
            all_events.extend(events)

        # Sort events by start time
        all_events.sort(key=lambda x: x["DateTime"])

        self.events = all_events
        logger.info(f"Total events extracted: {len(all_events)}")

        return all_events

    def export_to_csv(self, output_file: str = "../data/calendar_events_2025.csv") -> bool:
        """Export events to CSV file.

        Args:
            output_file: Output CSV file path

        Returns:
            True if export was successful
        """
        if not self.events:
            logger.error("No events to export. Run extract_all_events() first.")
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
        """Generate a summary report of extracted calendar data.

        Args:
            output_file: Output markdown file path

        Returns:
            True if report generation was successful
        """
        if not self.events:
            logger.error("No events to report. Run extract_all_events() first.")
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
            report = f"""# Calendar Analysis Report - 2025

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
    """Main function to run the calendar extraction process."""
    print("Google Calendar Extractor for WBSO Hours Registration")
    print("=" * 60)

    # Initialize extractor
    extractor = GoogleCalendarExtractor()

    # Setup API access
    print("\n1. Setting up Google Calendar API access...")
    if not extractor.setup_api_access():
        print("Failed to setup API access. Please check credentials.")
        return

    # Discover calendars
    print("\n2. Discovering accessible calendars...")
    calendars = extractor.discover_calendars()
    if not calendars:
        print("No calendars discovered.")
        return

    print(f"Found {len(calendars)} calendars:")
    for _, info in calendars.items():
        print(f"  - {info['summary']} ({info['accessRole']})")

    # Extract events
    print("\n3. Extracting calendar events for 2025...")
    events = extractor.extract_all_events(2025)
    if not events:
        print("No events extracted.")
        return

    print(f"Extracted {len(events)} events")

    # Export to CSV
    print("\n4. Exporting events to CSV...")
    if extractor.export_to_csv():
        print("Events exported successfully")
    else:
        print("Failed to export events")

    # Generate summary report
    print("\n5. Generating summary report...")
    if extractor.generate_summary_report():
        print("Summary report generated successfully")
    else:
        print("Failed to generate summary report")

    print("\nCalendar extraction completed!")
    print("Check the data/ directory for output files.")


if __name__ == "__main__":
    main()
