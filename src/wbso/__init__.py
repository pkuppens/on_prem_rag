"""
WBSO (Wet Bevordering Speur- en Ontwikkelingswerk) Module

This module provides data models, validation, and reporting functionality
for WBSO hours registration and compliance documentation.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)
"""

from .calendar_event import WBSOSession, CalendarEvent, ValidationResult, WBSODataset

__all__ = ["WBSOSession", "CalendarEvent", "ValidationResult", "WBSODataset"]
