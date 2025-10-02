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
    - Focus on logon/logoff events for session detection

    Attributes:
        datetime: Event timestamp as string (YYYY-MM-DD HH:mm:ss format)
        event_id: Windows event ID (7001=logon, 7002=logoff, 6013=uptime, etc.)
        event_type: Human-readable event type
        message: Event message content
        record_id: Unique record identifier
        date: Extracted date field for processing (YYYY-MM-DD format)
    """

    datetime: str
    event_id: str
    event_type: str
    message: str
    record_id: str
    date: Optional[str] = None  # Extracted date field for processing
