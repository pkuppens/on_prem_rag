#!/usr/bin/env python3
"""
Calendar Security and Validation Module

This module provides security validation to ensure that write operations
only target the WBSO calendar, implementing least-privilege principles
at the code level.

Note: Google Calendar API OAuth scopes don't support calendar-specific
permissions. The scope grants access to all calendars, but we enforce
restrictions in code to only write to the WBSO calendar.

Author: AI Assistant
Created: 2025-11-15
"""

from typing import Optional

from .logging_config import get_logger
from .upload import WBSO_CALENDAR_NAME

logger = get_logger("calendar_security")


def validate_wbso_calendar_write(
    calendar_id: str,
    allowed_calendar_id: Optional[str],
    calendar_name: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate that a write operation targets only the WBSO calendar.

    This function enforces least-privilege by ensuring all write operations
    (create, update, delete) only target the WBSO calendar.

    Args:
        calendar_id: The calendar ID being targeted for the write operation
        allowed_calendar_id: The allowed WBSO calendar ID (from get_wbso_calendar_id)
        calendar_name: Optional calendar name for logging (if available)

    Returns:
        tuple: (is_valid: bool, error_message: str)
        - If valid: (True, "")
        - If invalid: (False, error_message)
    """
    if not allowed_calendar_id:
        error_msg = (
            "WBSO calendar ID not found. Cannot validate write operation. Write operations are only allowed to the WBSO calendar."
        )
        logger.error(error_msg)
        return False, error_msg

    if calendar_id != allowed_calendar_id:
        error_msg = (
            f"SECURITY: Write operation blocked - attempted to write to calendar '{calendar_id}' "
            f"(name: {calendar_name or 'unknown'}), but only WBSO calendar '{allowed_calendar_id}' "
            f"('{WBSO_CALENDAR_NAME}') is allowed. This is a security restriction to prevent "
            f"accidental modification of other calendars."
        )
        logger.error(error_msg)
        return False, error_msg

    logger.debug(f"Write operation validated: calendar '{calendar_id}' matches WBSO calendar '{WBSO_CALENDAR_NAME}'")
    return True, ""


def validate_calendar_id_for_read(calendar_id: Optional[str]) -> bool:
    """Validate that a calendar ID is provided for read operations.

    Read operations are allowed on all calendars (for duplicate detection),
    but we still validate that a calendar ID is provided.

    Args:
        calendar_id: The calendar ID for the read operation

    Returns:
        bool: True if calendar_id is provided, False otherwise
    """
    if not calendar_id:
        logger.warning("Read operation attempted without calendar_id - will use default WBSO calendar")
        return False
    return True
