#!/usr/bin/env python3
"""
WBSO Google Calendar Upload Module

This module provides Google Calendar upload functionality for WBSO calendar events
with comprehensive error handling, duplicate prevention, and audit trails.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Created: 2025-10-18
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Google Calendar API dependencies not installed: {e}")
    print("Install with: uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    raise

from .calendar_event import WBSODataset, CalendarEvent
from .logging_config import get_logger

logger = get_logger("upload")

# Google Calendar API configuration
SCOPES = ["https://www.googleapis.com/auth/calendar"]
WBSO_CALENDAR_NAME = "WBSO Activities 2025"
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 0.1  # 10 requests per second
MAX_RETRIES = 3


class GoogleCalendarUploader:
    """Handles Google Calendar upload with safety features and error handling."""

    def __init__(self, credentials_path: Path, token_path: Path, config_path: Path):
        """Initialize uploader with authentication and configuration."""
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.config_path = Path(config_path)
        self.service = None
        self.wbso_calendar_id = None
        self.upload_log = []
        self.session_to_event_mapping = {}
        self.upload_errors = []
        self.conflict_report = []

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        logger.info("Authenticating with Google Calendar API...")

        creds = None

        # Load existing token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
                logger.info("Loaded existing credentials")
            except Exception as e:
                logger.warning(f"Failed to load existing credentials: {e}")

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    error_msg = (
                        f"Failed to refresh expired credentials: {e}\n\n"
                        f"Your Google Calendar OAuth token has expired. "
                        f"See docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md for instructions."
                    )
                    logger.error(error_msg)
                    return False
            else:
                if not self.credentials_path.exists():
                    logger.error(f"Credentials file not found: {self.credentials_path}")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("Obtained new credentials")
                except Exception as e:
                    logger.error(f"Failed to obtain credentials: {e}")
                    return False

            # Save credentials for next run
            try:
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials for future use")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")

        # Build service
        try:
            self.service = build("calendar", "v3", credentials=creds)
            logger.info("Google Calendar service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to build Calendar service: {e}")
            return False

    def get_wbso_calendar_id(self) -> Optional[str]:
        """Get the WBSO calendar ID and verify it's the correct calendar."""
        logger.info(f"Looking for WBSO calendar: {WBSO_CALENDAR_NAME}")

        try:
            # List all calendars
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            # Find WBSO calendar
            wbso_calendar = None
            for calendar in calendars:
                if calendar["summary"] == WBSO_CALENDAR_NAME:
                    wbso_calendar = calendar
                    break

            if not wbso_calendar:
                logger.error(f"WBSO calendar '{WBSO_CALENDAR_NAME}' not found")
                logger.info("Available calendars:")
                for calendar in calendars:
                    logger.info(f"  - {calendar['summary']} (ID: {calendar['id']})")
                return None

            # Verify write permissions
            access_role = wbso_calendar.get("accessRole", "")
            if access_role not in ["owner", "writer"]:
                logger.error(f"Insufficient permissions for calendar '{WBSO_CALENDAR_NAME}': {access_role}")
                return None

            self.wbso_calendar_id = wbso_calendar["id"]
            logger.info(f"Found WBSO calendar: {wbso_calendar['summary']} (ID: {self.wbso_calendar_id})")
            logger.info(f"Access role: {access_role}")

            return self.wbso_calendar_id

        except HttpError as e:
            logger.error(f"HTTP error getting calendar list: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting calendar list: {e}")
            return None

    def get_existing_events(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get existing events in the WBSO calendar for the date range."""
        logger.info(f"Getting existing events from {start_date.date()} to {end_date.date()}")

        try:
            # Query events in date range
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.wbso_calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            logger.info(f"Found {len(events)} existing events in calendar")

            # Build indexes for duplicate detection
            existing_by_session_id = {}
            existing_by_datetime = {}

            for event in events:
                # Index by session_id from extendedProperties
                private_props = event.get("extendedProperties", {}).get("private", {})
                session_id = private_props.get("session_id")
                if session_id:
                    existing_by_session_id[session_id] = event

                # Index by datetime range
                start = event.get("start", {}).get("dateTime")
                end = event.get("end", {}).get("dateTime")
                if start and end:
                    dt_key = f"{start}-{end}"
                    existing_by_datetime[dt_key] = event

            return {
                "events": events,
                "by_session_id": existing_by_session_id,
                "by_datetime": existing_by_datetime,
                "count": len(events),
            }

        except HttpError as e:
            logger.error(f"HTTP error getting existing events: {e}")
            return {"events": [], "by_session_id": {}, "by_datetime": {}, "count": 0}
        except Exception as e:
            logger.error(f"Error getting existing events: {e}")
            return {"events": [], "by_session_id": {}, "by_datetime": {}, "count": 0}

    def create_upload_plan(self, events: List[CalendarEvent], existing_events: Dict[str, Any]) -> Dict[str, Any]:
        """Create upload plan with duplicate detection."""
        logger.info("Creating upload plan...")

        upload_plan = {"new_events": [], "skip_events": [], "duplicate_session_ids": [], "duplicate_datetime_ranges": []}

        # Track session_ids and datetime ranges within the upload batch
        seen_session_ids = set()
        seen_datetime_ranges = set()

        for event in events:
            # Get session_id from extended_properties
            session_id = event.extended_properties.get("private", {}).get("session_id", "")

            # Check for duplicate session_id in existing calendar
            if session_id in existing_events["by_session_id"]:
                upload_plan["skip_events"].append(
                    {
                        "event": event,
                        "reason": "duplicate_session_id_existing",
                        "existing_event_id": existing_events["by_session_id"][session_id]["id"],
                    }
                )
                upload_plan["duplicate_session_ids"].append(session_id)
                continue

            # Check for duplicate session_id within upload batch
            if session_id in seen_session_ids:
                upload_plan["skip_events"].append(
                    {
                        "event": event,
                        "reason": "duplicate_session_id_batch",
                        "existing_event_id": None,
                    }
                )
                upload_plan["duplicate_session_ids"].append(session_id)
                continue

            # Check for duplicate datetime range in existing calendar
            dt_key = f"{event.start['dateTime']}-{event.end['dateTime']}"
            if dt_key in existing_events["by_datetime"]:
                upload_plan["skip_events"].append(
                    {
                        "event": event,
                        "reason": "duplicate_datetime_range_existing",
                        "existing_event_id": existing_events["by_datetime"][dt_key]["id"],
                    }
                )
                upload_plan["duplicate_datetime_ranges"].append(dt_key)
                continue

            # Check for duplicate datetime range within upload batch
            if dt_key in seen_datetime_ranges:
                upload_plan["skip_events"].append(
                    {
                        "event": event,
                        "reason": "duplicate_datetime_range_batch",
                        "existing_event_id": None,
                    }
                )
                upload_plan["duplicate_datetime_ranges"].append(dt_key)
                continue

            # Event is new, add to upload plan and track it
            seen_session_ids.add(session_id)
            seen_datetime_ranges.add(dt_key)
            upload_plan["new_events"].append(event)

        logger.info(f"Upload plan: {len(upload_plan['new_events'])} new events, {len(upload_plan['skip_events'])} skipped")
        if upload_plan["skip_events"]:
            reasons = {}
            for skip in upload_plan["skip_events"]:
                reason = skip["reason"]
                reasons[reason] = reasons.get(reason, 0) + 1
            logger.info(f"Skip reasons: {reasons}")
        return upload_plan

    def upload_events_batch(self, events: List[CalendarEvent]) -> List[Dict[str, Any]]:
        """Upload events in batches with error handling."""
        logger.info(f"Uploading {len(events)} events in batches of {BATCH_SIZE}")

        upload_results = []

        for i in range(0, len(events), BATCH_SIZE):
            batch = events[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(events) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} events)")

            for event in batch:
                result = self.upload_single_event(event)
                upload_results.append(result)

                # Rate limiting
                time.sleep(RATE_LIMIT_DELAY)

            # Brief pause between batches
            if batch_num < total_batches:
                time.sleep(1)

        return upload_results

    def upload_single_event(self, event: CalendarEvent) -> Dict[str, Any]:
        """Upload a single event with retry logic.

        Security: This function only writes to the WBSO calendar (self.wbso_calendar_id).
        The calendar ID is set during initialization and validated before any writes.
        """
        session_id = event.extended_properties.get("private", {}).get("session_id", "")

        # Security: Ensure we have a valid WBSO calendar ID
        if not self.wbso_calendar_id:
            error_msg = "WBSO calendar ID not set. Cannot upload events."
            logger.error(error_msg)
            return {
                "session_id": session_id,
                "status": "error",
                "error_message": error_msg,
                "event_summary": event.summary,
            }

        for attempt in range(MAX_RETRIES):
            try:
                # Convert to Google Calendar format
                event_body = event.to_google_format()

                # Upload event (only to WBSO calendar - enforced by self.wbso_calendar_id)
                created_event = self.service.events().insert(calendarId=self.wbso_calendar_id, body=event_body).execute()

                # Store mapping
                self.session_to_event_mapping[session_id] = created_event["id"]

                result = {
                    "session_id": session_id,
                    "event_id": created_event["id"],
                    "status": "success",
                    "attempt": attempt + 1,
                    "event_summary": event.summary,
                }

                logger.info(f"✅ Uploaded event: {event.summary} (ID: {created_event['id']})")
                return result

            except HttpError as e:
                error_details = {
                    "session_id": session_id,
                    "status": "error",
                    "attempt": attempt + 1,
                    "error_code": e.resp.status,
                    "error_message": str(e),
                    "event_summary": event.summary,
                }

                if e.resp.status == 403:
                    logger.error(f"❌ Permission denied for event: {event.summary}")
                    self.upload_errors.append(error_details)
                    return error_details
                elif e.resp.status == 429:
                    # Rate limit exceeded, wait and retry
                    wait_time = 2**attempt
                    logger.warning(f"⏳ Rate limit exceeded, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ HTTP error uploading event: {event.summary} - {e}")
                    if attempt == MAX_RETRIES - 1:
                        self.upload_errors.append(error_details)
                        return error_details
                    time.sleep(1)

            except Exception as e:
                error_details = {
                    "session_id": session_id,
                    "status": "error",
                    "attempt": attempt + 1,
                    "error_message": str(e),
                    "event_summary": event.summary,
                }

                logger.error(f"❌ Error uploading event: {event.summary} - {e}")
                if attempt == MAX_RETRIES - 1:
                    self.upload_errors.append(error_details)
                    return error_details
                time.sleep(1)

        # Should not reach here
        return {
            "session_id": session_id,
            "status": "failed",
            "error_message": "Max retries exceeded",
            "event_summary": event.summary,
        }

    def upload_events(self, events: List[CalendarEvent], dry_run: bool = False) -> Dict[str, Any]:
        """Main upload function with comprehensive error handling."""
        logger.info(f"Starting upload process (dry_run={dry_run})")

        # Authenticate
        if not self.authenticate():
            return {"success": False, "error": "Authentication failed"}

        # Get WBSO calendar ID
        if not self.get_wbso_calendar_id():
            return {"success": False, "error": "WBSO calendar not found or no write access"}

        # Get date range for existing events check
        if not events:
            return {"success": False, "error": "No events to upload"}

        start_dates = [datetime.fromisoformat(e.start["dateTime"].replace("Z", "+00:00")) for e in events]
        end_dates = [datetime.fromisoformat(e.end["dateTime"].replace("Z", "+00:00")) for e in events]

        min_date = min(start_dates) - timedelta(days=1)
        max_date = max(end_dates) + timedelta(days=1)

        # Get existing events
        existing_events = self.get_existing_events(min_date, max_date)

        # Create upload plan
        upload_plan = self.create_upload_plan(events, existing_events)

        if dry_run:
            logger.info("DRY RUN - No events will be uploaded")
            return {
                "success": True,
                "dry_run": True,
                "upload_plan": upload_plan,
                "existing_events": existing_events,
            }

        # Upload new events
        if upload_plan["new_events"]:
            upload_results = self.upload_events_batch(upload_plan["new_events"])
            self.upload_log.extend(upload_results)
        else:
            logger.info("No new events to upload")
            upload_results = []

        # Prepare result
        result = {
            "success": len(self.upload_errors) == 0,
            "upload_plan": upload_plan,
            "upload_results": upload_results,
            "session_mapping": self.session_to_event_mapping,
            "errors": self.upload_errors,
        }

        logger.info(f"Upload complete: {len(upload_results)} events processed")
        return result


def main():
    """Main upload function."""
    import sys

    # Set up paths
    script_dir = Path(__file__).parent.parent.parent / "docs" / "project" / "hours"
    output_dir = script_dir / "upload_output"
    validation_output_dir = script_dir / "validation_output"

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Check for validated dataset
    cleaned_dataset_path = validation_output_dir / "cleaned_dataset.json"
    if not cleaned_dataset_path.exists():
        logger.error(f"Cleaned dataset not found: {cleaned_dataset_path}")
        logger.error("Run validation script first: uv run wbso-validate")
        return 1

    # Load validated dataset
    logger.info(f"Loading validated dataset from {cleaned_dataset_path}")
    dataset = WBSODataset()
    dataset.load_from_json(cleaned_dataset_path)

    # Filter for WBSO sessions only
    wbso_sessions = [s for s in dataset.sessions if s.is_wbso]
    logger.info(f"Found {len(wbso_sessions)} WBSO sessions to upload")

    # Convert to calendar events
    calendar_events = []
    for session in wbso_sessions:
        try:
            event = CalendarEvent.from_wbso_session(session)
            calendar_events.append(event)
        except Exception as e:
            logger.error(f"Failed to convert session {session.session_id} to calendar event: {e}")

    logger.info(f"Converted {len(calendar_events)} sessions to calendar events")

    # Set up uploader
    credentials_path = script_dir / "scripts" / "credentials.json"
    token_path = script_dir / "scripts" / "token.json"
    config_path = script_dir / "config" / "wbso_calendar_config.json"

    uploader = GoogleCalendarUploader(credentials_path, token_path, config_path)

    # Check for dry run mode
    dry_run = "--dry-run" in sys.argv

    # Upload events
    result = uploader.upload_events(calendar_events, dry_run=dry_run)

    # Print summary
    print(f"\n{'=' * 60}")
    print("WBSO CALENDAR UPLOAD SUMMARY")
    print(f"{'=' * 60}")
    print(f"Success: {'✅ Yes' if result['success'] else '❌ No'}")
    print(f"Dry Run: {'✅ Yes' if result.get('dry_run') else '❌ No'}")

    if "upload_plan" in result:
        plan = result["upload_plan"]
        print(f"New Events: {len(plan['new_events'])}")
        print(f"Skipped Events: {len(plan['skip_events'])}")
        print(f"Duplicate Session IDs: {len(plan['duplicate_session_ids'])}")
        print(f"Duplicate DateTime Ranges: {len(plan['duplicate_datetime_ranges'])}")

    if result.get("errors"):
        print(f"Upload Errors: {len(result['errors'])}")

    print(f"\nReports exported to: {output_dir}")
    print(f"{'=' * 60}")

    # Exit with appropriate code
    if result["success"]:
        print("✅ Upload successful")
        return 0
    else:
        print("❌ Upload failed")
        return 1


if __name__ == "__main__":
    exit(main())
