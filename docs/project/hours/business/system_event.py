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
    - Event IDs are preserved for completeness
    - Session tags (logon/logoff) are used for session detection instead of EventId
    - Multiple event codes can indicate logon/logoff (7001, 6005 for logon; 7002, 6008, 41, 1074 for logoff)

    Attributes:
        datetime: Event timestamp as string (YYYY-MM-DD HH:mm:ss format)
        event_id: Windows event ID (7001=logon, 7002=logoff, 6008=unexpected shutdown, etc.)
        event_type: Human-readable event type
        username: User associated with the event
        message: Event message content
        record_id: Unique record identifier
        date: Extracted date field for processing (YYYY-MM-DD format)
        session_tag: Optional tag indicating session boundary ("logon", "logoff", or None)
    """

    datetime: str
    event_id: str
    event_type: str
    username: str
    message: str
    record_id: str
    date: Optional[str] = None  # Extracted date field for processing
    session_tag: Optional[str] = None  # "logon", "logoff", or None
