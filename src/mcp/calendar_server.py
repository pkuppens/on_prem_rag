#!/usr/bin/env python3
"""
MCP Calendar Server

This module provides an MCP server that exposes Google Calendar functionality
for WBSO hours registration, including read, write, edit, delete, conflict detection,
and comprehensive calendar management capabilities.

Author: AI Assistant
Created: 2025-11-15
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9
    from backports.zoneinfo import ZoneInfo

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    raise ImportError(f"Google Calendar API dependencies not installed: {e}") from e

# WBSO imports
from wbso.calendar_event import CalendarEvent
from wbso.logging_config import get_logger
from wbso.upload import GoogleCalendarUploader, SCOPES, WBSO_CALENDAR_NAME

logger = get_logger("mcp.calendar_server")

# Amsterdam timezone (handles DST automatically)
AMSTERDAM_TZ = ZoneInfo("Europe/Amsterdam")

# Initialize MCP server
app = Server("calendar-server")

# Global calendar service instance
_calendar_service = None
_uploader = None


def ensure_amsterdam_timezone(dt: datetime) -> datetime:
    """Ensure datetime is in Amsterdam timezone with DST handling.

    If datetime is timezone-naive, assumes it's already in Amsterdam timezone.
    If datetime has timezone, converts to Amsterdam timezone.

    Args:
        dt: Datetime object (may be timezone-naive or timezone-aware)

    Returns:
        Datetime object in Amsterdam timezone
    """
    if dt.tzinfo is None:
        # Timezone-naive: assume Amsterdam timezone
        return dt.replace(tzinfo=AMSTERDAM_TZ)
    else:
        # Timezone-aware: convert to Amsterdam
        return dt.astimezone(AMSTERDAM_TZ)


def get_calendar_service():
    """Get or initialize Google Calendar service."""
    global _calendar_service

    if _calendar_service is not None:
        return _calendar_service

    # Get credentials paths from environment or use defaults
    script_dir = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "scripts"
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", script_dir / "credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", script_dir / "token.json"))

    creds = None

    # Load existing token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
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
                    f"Your Google Calendar OAuth token has expired and cannot be automatically refreshed.\n"
                    f"Please follow the instructions in:\n"
                    f"  docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md\n\n"
                    f"Quick fix:\n"
                    f"  1. Delete: docs/project/hours/scripts/token.json\n"
                    f"  2. Run: uv run authenticate-google-calendar\n"
                    f"  3. Complete the OAuth flow in your browser\n\n"
                    f"Note: The MCP server only authenticates when tools are used.\n"
                    f"Use the authenticate script for explicit authentication."
                )
                logger.error(error_msg)
                print(f"\n{error_msg}", file=sys.stderr)
                raise RuntimeError(error_msg) from e
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("Obtained new credentials")
            except Exception as e:
                error_msg = (
                    f"Failed to obtain credentials: {e}\n\n"
                    f"If your token has expired, please follow:\n"
                    f"  docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md"
                )
                logger.error(error_msg)
                print(f"\n{error_msg}", file=sys.stderr)
                raise RuntimeError(error_msg) from e

        # Save credentials for next run
        try:
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            logger.info("Saved credentials for future use")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")

    # Build service
    try:
        _calendar_service = build("calendar", "v3", credentials=creds)
        logger.info("Google Calendar service initialized")
        return _calendar_service
    except Exception as e:
        logger.error(f"Failed to build Calendar service: {e}")
        raise


def get_uploader():
    """Get or initialize GoogleCalendarUploader instance."""
    global _uploader

    if _uploader is not None:
        return _uploader

    script_dir = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "scripts"
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", script_dir / "credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", script_dir / "token.json"))
    config_path = script_dir / "config" / "wbso_calendar_config.json"

    _uploader = GoogleCalendarUploader(credentials_path, token_path, config_path)
    if not _uploader.authenticate():
        raise RuntimeError("Failed to authenticate with Google Calendar")

    return _uploader


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="list_calendars",
            description="List all accessible Google Calendars with their IDs, names, and access roles.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="read_calendar_events",
            description="Read calendar events by calendar name, date range, or calendar ID. Returns list of events with full details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Calendar ID (optional, defaults to WBSO calendar)"},
                    "calendar_name": {"type": "string", "description": "Calendar name to filter by (optional)"},
                    "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD or ISO datetime)"},
                    "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD or ISO datetime)"},
                },
            },
        ),
        Tool(
            name="summarize_calendar_events",
            description="Summarize calendar events with total count, number of unique days, and total hours.",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Calendar ID (optional, defaults to WBSO calendar)"},
                    "calendar_name": {"type": "string", "description": "Calendar name to filter by (optional)"},
                    "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD or ISO datetime)"},
                    "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD or ISO datetime)"},
                },
            },
        ),
        Tool(
            name="create_calendar_event",
            description="Create a calendar event (dummy for testing). Returns event object that can be written to calendar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title/summary"},
                    "start_time": {"type": "string", "description": "Start time in ISO datetime format"},
                    "end_time": {"type": "string", "description": "End time in ISO datetime format"},
                    "description": {"type": "string", "description": "Event description (optional)"},
                    "calendar_id": {"type": "string", "description": "Target calendar ID (optional)"},
                    "location": {"type": "string", "description": "Event location (optional)"},
                    "extended_properties": {
                        "type": "object",
                        "description": "Extended properties for WBSO metadata (optional)",
                    },
                },
                "required": ["summary", "start_time", "end_time"],
            },
        ),
        Tool(
            name="write_calendar_events",
            description="Write created calendar events directly to the calendar. Accepts list of event objects.",
            inputSchema={
                "type": "object",
                "properties": {
                    "events": {
                        "type": "array",
                        "description": "List of event objects to write (from create_calendar_event or external)",
                        "items": {"type": "object"},
                    },
                    "calendar_id": {"type": "string", "description": "Target calendar ID (optional)"},
                },
                "required": ["events"],
            },
        ),
        Tool(
            name="detect_duplicates_conflicts",
            description="Detect duplicate events and conflicts (overlapping events) in calendar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Target calendar ID (optional)"},
                    "start_date": {"type": "string", "description": "Date range start in ISO format"},
                    "end_date": {"type": "string", "description": "Date range end in ISO format"},
                    "events": {
                        "type": "array",
                        "description": "Optional list of events to check against existing calendar events",
                        "items": {"type": "object"},
                    },
                },
            },
        ),
        Tool(
            name="edit_calendar_event",
            description="Edit an existing calendar event. Updates specified fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Target calendar ID (optional)"},
                    "event_id": {"type": "string", "description": "Event ID to update"},
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of fields to update (summary, description, start, end, etc.)",
                    },
                },
                "required": ["event_id", "updates"],
            },
        ),
        Tool(
            name="delete_calendar_event",
            description="Delete a calendar event by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "Target calendar ID (optional)"},
                    "event_id": {"type": "string", "description": "Event ID to delete"},
                },
                "required": ["event_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list_calendars":
            result = await handle_list_calendars()
        elif name == "read_calendar_events":
            result = await handle_read_calendar_events(arguments)
        elif name == "summarize_calendar_events":
            result = await handle_summarize_calendar_events(arguments)
        elif name == "create_calendar_event":
            result = await handle_create_calendar_event(arguments)
        elif name == "write_calendar_events":
            result = await handle_write_calendar_events(arguments)
        elif name == "detect_duplicates_conflicts":
            result = await handle_detect_duplicates_conflicts(arguments)
        elif name == "edit_calendar_event":
            result = await handle_edit_calendar_event(arguments)
        elif name == "delete_calendar_event":
            result = await handle_delete_calendar_event(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        error_result = {"error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def handle_list_calendars() -> Dict[str, Any]:
    """Handle list_calendars tool call."""
    service = get_calendar_service()

    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])

        result = []
        for calendar in calendars:
            result.append(
                {
                    "id": calendar.get("id"),
                    "summary": calendar.get("summary"),
                    "accessRole": calendar.get("accessRole"),
                    "description": calendar.get("description"),
                    "timeZone": calendar.get("timeZone"),
                }
            )

        return {"calendars": result, "count": len(result)}
    except HttpError as e:
        logger.error(f"HTTP error listing calendars: {e}")
        return {"error": f"HTTP error: {e}", "calendars": [], "count": 0}
    except Exception as e:
        logger.error(f"Error listing calendars: {e}")
        return {"error": str(e), "calendars": [], "count": 0}


async def handle_read_calendar_events(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_calendar_events tool call."""
    service = get_calendar_service()
    uploader = get_uploader()

    calendar_id = arguments.get("calendar_id")
    calendar_name = arguments.get("calendar_name")
    start_date_str = arguments.get("start_date")
    end_date_str = arguments.get("end_date")

    # Resolve calendar ID
    if calendar_name:
        # Find calendar by name
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        for cal in calendars:
            if cal.get("summary") == calendar_name:
                calendar_id = cal.get("id")
                break
        if not calendar_id:
            return {"error": f"Calendar '{calendar_name}' not found", "events": []}

    if not calendar_id:
        # Use WBSO calendar as default
        calendar_id = uploader.get_wbso_calendar_id()
        if not calendar_id:
            return {"error": "WBSO calendar not found and no calendar_id provided", "events": []}

    # Parse dates and ensure Amsterdam timezone
    try:
        if start_date_str:
            if "T" in start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            else:
                start_date = datetime.fromisoformat(f"{start_date_str}T00:00:00")
            start_date = ensure_amsterdam_timezone(start_date)
        else:
            start_date = datetime.now(AMSTERDAM_TZ) - timedelta(days=30)  # Default: last 30 days

        if end_date_str:
            if "T" in end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            else:
                end_date = datetime.fromisoformat(f"{end_date_str}T23:59:59")
            end_date = ensure_amsterdam_timezone(end_date)
        else:
            end_date = datetime.now(AMSTERDAM_TZ) + timedelta(days=30)  # Default: next 30 days
    except ValueError as e:
        return {"error": f"Invalid date format: {e}", "events": []}

    # Get events
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start_date.isoformat() + "Z",
                timeMax=end_date.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        return {"events": events, "count": len(events), "calendar_id": calendar_id}
    except HttpError as e:
        logger.error(f"HTTP error reading events: {e}")
        return {"error": f"HTTP error: {e}", "events": [], "count": 0}
    except Exception as e:
        logger.error(f"Error reading events: {e}")
        return {"error": str(e), "events": [], "count": 0}


async def handle_summarize_calendar_events(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle summarize_calendar_events tool call."""
    # First read the events
    events_result = await handle_read_calendar_events(arguments)

    if "error" in events_result:
        return events_result

    events = events_result.get("events", [])

    # Calculate summary statistics
    total_items = len(events)
    unique_days = set()
    total_hours = 0.0
    earliest_date = None
    latest_date = None

    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})

        # Extract date
        start_dt_str = start.get("dateTime") or start.get("date")
        end_dt_str = end.get("dateTime") or end.get("date")

        if start_dt_str:
            try:
                if "T" in start_dt_str:
                    start_dt = datetime.fromisoformat(start_dt_str.replace("Z", "+00:00"))
                else:
                    start_dt = datetime.fromisoformat(start_dt_str)
                start_dt = ensure_amsterdam_timezone(start_dt)

                unique_days.add(start_dt.date())

                if earliest_date is None or start_dt < earliest_date:
                    earliest_date = start_dt
                if latest_date is None or start_dt > latest_date:
                    latest_date = start_dt

                # Calculate duration
                if end_dt_str:
                    if "T" in end_dt_str:
                        end_dt = datetime.fromisoformat(end_dt_str.replace("Z", "+00:00"))
                    else:
                        end_dt = datetime.fromisoformat(end_dt_str)
                    end_dt = ensure_amsterdam_timezone(end_dt)

                    duration = end_dt - start_dt
                    total_hours += duration.total_seconds() / 3600.0

                    if latest_date is None or end_dt > latest_date:
                        latest_date = end_dt
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing event date: {e}")

    return {
        "total_items": total_items,
        "total_days": len(unique_days),
        "total_hours": round(total_hours, 2),
        "date_range": {
            "earliest": earliest_date.isoformat() if earliest_date else None,
            "latest": latest_date.isoformat() if latest_date else None,
        },
    }


async def handle_create_calendar_event(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create_calendar_event tool call."""
    summary = arguments.get("summary")
    start_time_str = arguments.get("start_time")
    end_time_str = arguments.get("end_time")
    description = arguments.get("description", "")
    calendar_id = arguments.get("calendar_id")
    location = arguments.get("location", "Home Office")
    extended_properties = arguments.get("extended_properties", {})

    if not summary or not start_time_str or not end_time_str:
        return {"error": "summary, start_time, and end_time are required"}

    try:
        start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        # Ensure Amsterdam timezone with DST
        start_dt = ensure_amsterdam_timezone(start_dt)
        end_dt = ensure_amsterdam_timezone(end_dt)
    except ValueError as e:
        return {"error": f"Invalid datetime format: {e}"}

    # Create CalendarEvent object
    event = CalendarEvent(
        summary=summary,
        description=description,
        start={"dateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Amsterdam"},
        end={"dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Amsterdam"},
        location=location,
        extended_properties=extended_properties,
    )

    # Convert to Google format
    event_dict = event.to_google_format()

    return {
        "event": event_dict,
        "message": "Event created (not yet written to calendar). Use write_calendar_events to write it.",
    }


async def handle_write_calendar_events(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle write_calendar_events tool call."""
    events_data = arguments.get("events", [])
    calendar_id = arguments.get("calendar_id")

    if not events_data:
        return {"error": "events list is required"}

    uploader = get_uploader()

    # Resolve calendar ID
    if not calendar_id:
        calendar_id = uploader.get_wbso_calendar_id()
        if not calendar_id:
            return {"error": "WBSO calendar not found and no calendar_id provided"}

    # Security: Validate that we're only writing to the WBSO calendar
    from wbso.calendar_security import validate_wbso_calendar_write

    allowed_calendar_id = uploader.get_wbso_calendar_id()
    is_valid, error_msg = validate_wbso_calendar_write(calendar_id, allowed_calendar_id)
    if not is_valid:
        logger.error(f"SECURITY: Write operation blocked: {error_msg}")
        return {"error": error_msg}

    # Convert event dictionaries to CalendarEvent objects
    calendar_events = []
    for event_data in events_data:
        try:
            # If it's already a CalendarEvent-like dict, use it directly
            if isinstance(event_data, dict):
                event = CalendarEvent(
                    summary=event_data.get("summary", ""),
                    description=event_data.get("description", ""),
                    start=event_data.get("start", {}),
                    end=event_data.get("end", {}),
                    location=event_data.get("location", "Home Office"),
                    extended_properties=event_data.get("extendedProperties", {}),
                )
                calendar_events.append(event)
        except Exception as e:
            logger.warning(f"Error converting event: {e}")

    # Upload events
    result = uploader.upload_events(calendar_events, dry_run=False)

    return {
        "success": result.get("success", False),
        "uploaded_count": len(result.get("upload_results", [])),
        "errors": result.get("errors", []),
        "session_mapping": result.get("session_mapping", {}),
    }


async def handle_detect_duplicates_conflicts(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle detect_duplicates_conflicts tool call."""
    service = get_calendar_service()
    uploader = get_uploader()

    calendar_id = arguments.get("calendar_id")
    start_date_str = arguments.get("start_date")
    end_date_str = arguments.get("end_date")
    events_to_check = arguments.get("events", [])

    # Resolve calendar ID
    if not calendar_id:
        calendar_id = uploader.get_wbso_calendar_id()
        if not calendar_id:
            return {"error": "WBSO calendar not found and no calendar_id provided"}

    # Parse dates and ensure Amsterdam timezone
    try:
        if start_date_str:
            if "T" in start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            else:
                start_date = datetime.fromisoformat(f"{start_date_str}T00:00:00")
            start_date = ensure_amsterdam_timezone(start_date)
        else:
            start_date = datetime.now(AMSTERDAM_TZ) - timedelta(days=30)

        if end_date_str:
            if "T" in end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            else:
                end_date = datetime.fromisoformat(f"{end_date_str}T23:59:59")
            end_date = ensure_amsterdam_timezone(end_date)
        else:
            end_date = datetime.now(AMSTERDAM_TZ) + timedelta(days=30)
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}

    # Get existing events
    existing_events_data = uploader.get_existing_events(start_date, end_date)
    existing_events = existing_events_data.get("events", [])

    # Check for duplicates by session_id
    duplicates_by_session_id = []
    duplicates_by_datetime = []

    for event in existing_events:
        private_props = event.get("extendedProperties", {}).get("private", {})
        session_id = private_props.get("session_id")
        if session_id:
            # Check if this session_id appears in events_to_check
            for check_event in events_to_check:
                check_session = check_event.get("extendedProperties", {}).get("private", {}).get("session_id")
                if check_session == session_id:
                    duplicates_by_session_id.append({"session_id": session_id, "existing_event_id": event.get("id")})

        # Check for duplicate datetime ranges
        start = event.get("start", {}).get("dateTime")
        end = event.get("end", {}).get("dateTime")
        if start and end:
            for check_event in events_to_check:
                check_start = check_event.get("start", {}).get("dateTime")
                check_end = check_event.get("end", {}).get("dateTime")
                if check_start == start and check_end == end:
                    duplicates_by_datetime.append({"datetime_range": f"{start}-{end}", "existing_event_id": event.get("id")})

    # Check for conflicts (overlapping events)
    conflicts = []
    for i, event1 in enumerate(existing_events):
        start1 = event1.get("start", {}).get("dateTime")
        end1 = event1.get("end", {}).get("dateTime")
        if not start1 or not end1:
            continue

        try:
            dt1_start = datetime.fromisoformat(start1.replace("Z", "+00:00"))
            dt1_end = datetime.fromisoformat(end1.replace("Z", "+00:00"))
            dt1_start = ensure_amsterdam_timezone(dt1_start)
            dt1_end = ensure_amsterdam_timezone(dt1_end)
        except (ValueError, TypeError):
            continue

        for j, event2 in enumerate(existing_events[i + 1 :], i + 1):
            start2 = event2.get("start", {}).get("dateTime")
            end2 = event2.get("end", {}).get("dateTime")
            if not start2 or not end2:
                continue

            try:
                dt2_start = datetime.fromisoformat(start2.replace("Z", "+00:00"))
                dt2_end = datetime.fromisoformat(end2.replace("Z", "+00:00"))
                dt2_start = ensure_amsterdam_timezone(dt2_start)
                dt2_end = ensure_amsterdam_timezone(dt2_end)
            except (ValueError, TypeError):
                continue

            # Check for overlap
            overlap_start = max(dt1_start, dt2_start)
            overlap_end = min(dt1_end, dt2_end)

            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                overlap_hours = overlap_duration.total_seconds() / 3600.0

                conflicts.append(
                    {
                        "event1_id": event1.get("id"),
                        "event1_summary": event1.get("summary"),
                        "event2_id": event2.get("id"),
                        "event2_summary": event2.get("summary"),
                        "overlap_start": overlap_start.isoformat(),
                        "overlap_end": overlap_end.isoformat(),
                        "overlap_hours": round(overlap_hours, 2),
                    }
                )

    return {
        "duplicates": {
            "by_session_id": duplicates_by_session_id,
            "by_datetime": duplicates_by_datetime,
        },
        "conflicts": conflicts,
        "summary": {
            "duplicate_session_ids": len(duplicates_by_session_id),
            "duplicate_datetime_ranges": len(duplicates_by_datetime),
            "conflicts": len(conflicts),
        },
    }


async def handle_edit_calendar_event(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle edit_calendar_event tool call."""
    service = get_calendar_service()
    uploader = get_uploader()

    calendar_id = arguments.get("calendar_id")
    event_id = arguments.get("event_id")
    updates = arguments.get("updates", {})

    if not event_id:
        return {"error": "event_id is required"}

    # Resolve calendar ID
    if not calendar_id:
        calendar_id = uploader.get_wbso_calendar_id()
        if not calendar_id:
            return {"error": "WBSO calendar not found and no calendar_id provided"}

    # Security: Validate that we're only editing events in the WBSO calendar
    from wbso.calendar_security import validate_wbso_calendar_write

    allowed_calendar_id = uploader.get_wbso_calendar_id()
    is_valid, error_msg = validate_wbso_calendar_write(calendar_id, allowed_calendar_id)
    if not is_valid:
        logger.error(f"SECURITY: Edit operation blocked: {error_msg}")
        return {"error": error_msg}

    try:
        # Get existing event
        existing_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Apply updates
        for key, value in updates.items():
            if key == "start" or key == "end":
                # Handle datetime updates - ensure Amsterdam timezone
                if isinstance(value, str):
                    try:
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        dt = ensure_amsterdam_timezone(dt)
                        existing_event[key] = {"dateTime": dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Amsterdam"}
                    except (ValueError, TypeError):
                        # If parsing fails, use value as-is but ensure timezone
                        existing_event[key] = {
                            "dateTime": value,
                            "timeZone": existing_event.get(key, {}).get("timeZone", "Europe/Amsterdam"),
                        }
                else:
                    existing_event[key] = value
            else:
                existing_event[key] = value

        # Update event
        updated_event = service.events().patch(calendarId=calendar_id, eventId=event_id, body=existing_event).execute()

        return {
            "success": True,
            "event_id": updated_event.get("id"),
            "updated_fields": list(updates.keys()),
            "event": updated_event,
        }
    except HttpError as e:
        logger.error(f"HTTP error updating event: {e}")
        return {"error": f"HTTP error: {e}"}
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return {"error": str(e)}


async def handle_delete_calendar_event(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle delete_calendar_event tool call."""
    service = get_calendar_service()
    uploader = get_uploader()

    calendar_id = arguments.get("calendar_id")
    event_id = arguments.get("event_id")

    if not event_id:
        return {"error": "event_id is required"}

    # Resolve calendar ID
    if not calendar_id:
        calendar_id = uploader.get_wbso_calendar_id()
        if not calendar_id:
            return {"error": "WBSO calendar not found and no calendar_id provided"}

    # Security: Validate that we're only deleting events from the WBSO calendar
    from wbso.calendar_security import validate_wbso_calendar_write

    allowed_calendar_id = uploader.get_wbso_calendar_id()
    is_valid, error_msg = validate_wbso_calendar_write(calendar_id, allowed_calendar_id)
    if not is_valid:
        logger.error(f"SECURITY: Delete operation blocked: {error_msg}")
        return {"error": error_msg}

    try:
        # Delete event
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

        return {"success": True, "event_id": event_id, "message": "Event deleted successfully"}
    except HttpError as e:
        if e.resp.status == 404:
            return {"error": "Event not found", "event_id": event_id}
        logger.error(f"HTTP error deleting event: {e}")
        return {"error": f"HTTP error: {e}"}
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return {"error": str(e)}


async def main():
    """Main entry point for MCP server."""
    # Log startup information to stderr (stdio is used for MCP protocol)
    print("=" * 70, file=sys.stderr)
    print("MCP Calendar Server - Starting", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("", file=sys.stderr)
    print("Transport: stdio (standard input/output)", file=sys.stderr)
    print("Protocol: MCP (Model Context Protocol)", file=sys.stderr)
    print("", file=sys.stderr)
    print("Server Status: Ready and waiting for MCP client connections", file=sys.stderr)
    print("", file=sys.stderr)
    print("Available Tools:", file=sys.stderr)
    print("  - list_calendars", file=sys.stderr)
    print("  - read_calendar_events", file=sys.stderr)
    print("  - summarize_calendar_events", file=sys.stderr)
    print("  - create_calendar_event", file=sys.stderr)
    print("  - write_calendar_events", file=sys.stderr)
    print("  - detect_duplicates_conflicts", file=sys.stderr)
    print("  - edit_calendar_event", file=sys.stderr)
    print("  - delete_calendar_event", file=sys.stderr)
    print("", file=sys.stderr)
    print("Connection:", file=sys.stderr)
    print("  This server communicates via stdio. Connect using an MCP client", file=sys.stderr)
    print("  that supports stdio transport (e.g., Claude Desktop, Cursor, etc.)", file=sys.stderr)
    print("", file=sys.stderr)
    print("Configuration:", file=sys.stderr)
    script_dir = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "scripts"
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", script_dir / "credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", script_dir / "token.json"))
    print(f"  Credentials: {credentials_path}", file=sys.stderr)
    print(f"  Token: {token_path}", file=sys.stderr)
    print("", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("Server is now running. Waiting for MCP client connections...", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("", file=sys.stderr)

    logger.info("MCP Calendar Server starting with stdio transport")
    logger.info(f"Credentials path: {credentials_path}")
    logger.info(f"Token path: {token_path}")

    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP server initialized, entering event loop")
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except KeyboardInterrupt:
        print("\n" + "=" * 70, file=sys.stderr)
        print("MCP Calendar Server - Shutting down", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        logger.info("MCP Calendar Server shutdown requested")
    except Exception as e:
        print(f"\nError in MCP server: {e}", file=sys.stderr)
        logger.error(f"MCP server error: {e}", exc_info=True)
        raise


def main_sync():
    """Synchronous wrapper for main() to be used as entry point."""
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        logger.error(f"Fatal error in main_sync: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main_sync()
