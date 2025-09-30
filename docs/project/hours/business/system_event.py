"""
System Event Business Model

This module defines the SystemEvent business entity for representing
system events from event logs (logon/logoff, etc.).

Business Domain: Work Session Management
Entity: SystemEvent
Purpose: Represent system events that define work session boundaries
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemEvent:
    """Represents a system event from the event log.

    This business entity models system events that are used to detect
    work session boundaries. It provides a unified representation
    of system events across different processing contexts.

    Business Rules:
    - Events must have valid timestamps
    - Event IDs must be recognized (7001=logon, 7002=logoff)
    - Username must be provided for session attribution

    Attributes:
        datetime: Event timestamp as string (flexible format)
        event_id: Windows event ID (7001=logon, 7002=logoff)
        event_type: Human-readable event type
        username: User who triggered the event
        message: Event message content
        record_id: Unique record identifier
        additional_info: Additional event information (optional)
        date: Extracted date field for processing (YYYY-MM-DD format)
        log_name: Log name where event was recorded (optional)
        level: Event level (optional)
        process_name: Process name that triggered event (optional)
    """

    datetime: str
    event_id: str
    event_type: str
    username: str
    message: str
    record_id: str
    additional_info: Optional[str] = None
    date: Optional[str] = None  # Extracted date field for processing
    log_name: Optional[str] = None
    level: Optional[str] = None
    process_name: Optional[str] = None
