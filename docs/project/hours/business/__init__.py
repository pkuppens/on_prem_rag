"""
Business Layer for Hours and Work Session Management

This module contains business layer classes for work session management,
hours calculation, and work item tracking.

Business Domain: Work Session Management
- WorkSession: Unified work session model
- WorkItem: Individual work items (Git commits, document edits, etc.)
- SystemEvent: System events (logon/logoff, etc.)

Future Enhancement: This business layer will be extended to support
additional work tracking entities and business rules.
"""

from .system_event import SystemEvent
from .work_item import WorkItem
from .work_session import WorkSession

__all__ = ["WorkSession", "SystemEvent", "WorkItem"]
