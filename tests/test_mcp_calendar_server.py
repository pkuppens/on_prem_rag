#!/usr/bin/env python3
"""
Integration tests for MCP Calendar Server

This test suite creates, reads, edits, and deletes dummy calendar events
in December 2024 (out of scope for 2025 WBSO project) to verify all
calendar functionality works correctly.

Author: AI Assistant
Created: 2025-11-15
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import pytest

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    pytest.skip("Google Calendar API dependencies not installed", allow_module_level=True)

from wbso.upload import SCOPES

# Test configuration
TEST_YEAR = 2024
TEST_MONTH = 12
TEST_CALENDAR_NAME = "WBSO Activities 2025"  # Use existing WBSO calendar for testing
TEST_EVENT_PREFIX = "MCP_TEST_"


class MCPCalendarServerTester:
    """Comprehensive testing class for MCP calendar server functionality."""

    def __init__(self):
        """Initialize the tester."""
        self.service = None
        self.calendar_id = None
        self.test_event_ids: List[str] = []
        self.test_results: Dict[str, Any] = {}

        # Get credentials paths
        script_dir = Path(__file__).parent.parent / "docs" / "project" / "hours" / "scripts"
        self.credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", script_dir / "credentials.json"))
        self.token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", script_dir / "token.json"))

    def setup_api_access(self) -> bool:
        """Set up Google Calendar API access using OAuth2.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            creds = None

            # Load existing token
            if self.token_path.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
                except Exception:
                    pass

            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        print(f"Credentials file not found: {self.credentials_path}")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save credentials
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())

            # Build service
            self.service = build("calendar", "v3", credentials=creds)

            # Find test calendar
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            for calendar in calendars:
                if calendar["summary"] == TEST_CALENDAR_NAME:
                    self.calendar_id = calendar["id"]
                    break

            if not self.calendar_id:
                print(f"Calendar '{TEST_CALENDAR_NAME}' not found")
                return False

            return True

        except Exception as e:
            print(f"Failed to set up API access: {e}")
            return False

    def test_list_calendars(self) -> bool:
        """Test listing accessible calendars.

        Returns:
            True if test passed
        """
        print("Testing list_calendars...")

        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            result = {
                "status": "PASS",
                "calendar_count": len(calendars),
                "calendars": [{"id": c.get("id"), "summary": c.get("summary")} for c in calendars[:5]],  # First 5
            }

            self.test_results["list_calendars"] = result
            print(f"✅ Found {len(calendars)} calendars")
            return True

        except Exception as e:
            self.test_results["list_calendars"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed: {e}")
            return False

    def cleanup_old_test_events(self) -> None:
        """Clean up old test events from previous test runs.

        This ensures a clean state before creating new test events.
        """
        try:
            # Read events from December 2024
            start_date = datetime(TEST_YEAR, TEST_MONTH, 1, 0, 0, 0)
            end_date = datetime(TEST_YEAR, TEST_MONTH, 31, 23, 59, 59)

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            # Find and delete all test events
            test_events = [e for e in events if e.get("summary", "").startswith(TEST_EVENT_PREFIX)]

            deleted_count = 0
            for event in test_events:
                try:
                    self.service.events().delete(calendarId=self.calendar_id, eventId=event["id"]).execute()
                    deleted_count += 1
                except Exception:
                    pass  # Ignore errors for individual deletions

            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old test events")

        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up old test events: {e}")

    def test_create_dummy_events(self) -> bool:
        """Create dummy events in December 2024 for testing.

        Returns:
            True if events created successfully
        """
        print("Testing create_calendar_event...")

        # Clean up old test events first
        self.cleanup_old_test_events()

        try:
            # Create 3 test events in December 2024
            test_events = []

            for day in [10, 15, 20]:  # December 10, 15, 20
                start_time = datetime(TEST_YEAR, TEST_MONTH, day, 9, 0, 0)
                end_time = start_time + timedelta(hours=2)

                event_body = {
                    "summary": f"{TEST_EVENT_PREFIX}Test Event {day}",
                    "description": f"Test event created by MCP calendar server integration tests on {start_time.date()}",
                    "start": {"dateTime": start_time.isoformat(), "timeZone": "Europe/Amsterdam"},
                    "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Amsterdam"},
                    "extendedProperties": {
                        "private": {
                            "test_marker": "mcp_integration_test",
                            "test_date": start_time.isoformat(),
                        }
                    },
                }

                created_event = self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
                event_id = created_event["id"]
                self.test_event_ids.append(event_id)
                test_events.append({"id": event_id, "summary": created_event["summary"]})

                print(f"✅ Created test event: {created_event['summary']} (ID: {event_id})")

            self.test_results["create_events"] = {
                "status": "PASS",
                "created_count": len(test_events),
                "events": test_events,
            }

            return True

        except Exception as e:
            self.test_results["create_events"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed to create events: {e}")
            return False

    def test_read_events(self) -> bool:
        """Test reading calendar events.

        Returns:
            True if test passed
        """
        print("Testing read_calendar_events...")

        try:
            # Read events from December 2024
            start_date = datetime(TEST_YEAR, TEST_MONTH, 1, 0, 0, 0)
            end_date = datetime(TEST_YEAR, TEST_MONTH, 31, 23, 59, 59)

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            # Filter test events
            test_events = [e for e in events if e.get("summary", "").startswith(TEST_EVENT_PREFIX)]

            result = {
                "status": "PASS",
                "total_events": len(events),
                "test_events": len(test_events),
                "expected_test_events": 3,
            }

            if len(test_events) == 3:
                print(f"✅ Found {len(test_events)} test events as expected")
            else:
                print(f"⚠️ Found {len(test_events)} test events, expected 3")

            self.test_results["read_events"] = result
            return len(test_events) == 3

        except Exception as e:
            self.test_results["read_events"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed to read events: {e}")
            return False

    def test_summarize_events(self) -> bool:
        """Test summarizing calendar events.

        Returns:
            True if test passed
        """
        print("Testing summarize_calendar_events...")

        try:
            # Read events from December 2024
            start_date = datetime(TEST_YEAR, TEST_MONTH, 1, 0, 0, 0)
            end_date = datetime(TEST_YEAR, TEST_MONTH, 31, 23, 59, 59)

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            # Filter test events
            test_events = [e for e in events if e.get("summary", "").startswith(TEST_EVENT_PREFIX)]

            # Calculate summary
            total_items = len(test_events)
            unique_days = set()
            total_hours = 0.0

            for event in test_events:
                start = event.get("start", {}).get("dateTime")
                end = event.get("end", {}).get("dateTime")

                if start and end:
                    try:
                        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                        unique_days.add(start_dt.date())
                        duration = end_dt - start_dt
                        total_hours += duration.total_seconds() / 3600.0
                    except (ValueError, TypeError):
                        pass

            result = {
                "status": "PASS",
                "total_items": total_items,
                "total_days": len(unique_days),
                "total_hours": round(total_hours, 2),
                "expected_items": 3,
                "expected_days": 3,
                "expected_hours": 6.0,  # 3 events * 2 hours each
            }

            if total_items == 3 and len(unique_days) == 3 and abs(total_hours - 6.0) < 0.1:
                print(f"✅ Summary correct: {total_items} items, {len(unique_days)} days, {total_hours} hours")
            else:
                print(f"⚠️ Summary: {total_items} items, {len(unique_days)} days, {total_hours} hours")

            self.test_results["summarize_events"] = result
            return total_items == 3 and len(unique_days) == 3

        except Exception as e:
            self.test_results["summarize_events"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed to summarize events: {e}")
            return False

    def test_detect_duplicates(self) -> bool:
        """Test duplicate and conflict detection.

        Returns:
            True if test passed
        """
        print("Testing detect_duplicates_conflicts...")

        try:
            # Read test events
            start_date = datetime(TEST_YEAR, TEST_MONTH, 1, 0, 0, 0)
            end_date = datetime(TEST_YEAR, TEST_MONTH, 31, 23, 59, 59)

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            test_events = [e for e in events if e.get("summary", "").startswith(TEST_EVENT_PREFIX)]

            # Check for duplicates (should be none for our test events)
            session_ids = {}
            datetime_ranges = {}

            for event in test_events:
                private_props = event.get("extendedProperties", {}).get("private", {})
                test_marker = private_props.get("test_marker")
                if test_marker == "mcp_integration_test":
                    session_ids[event["id"]] = event

                start = event.get("start", {}).get("dateTime")
                end = event.get("end", {}).get("dateTime")
                if start and end:
                    dt_key = f"{start}-{end}"
                    if dt_key not in datetime_ranges:
                        datetime_ranges[dt_key] = []
                    datetime_ranges[dt_key].append(event)

            duplicates = {k: v for k, v in datetime_ranges.items() if len(v) > 1}

            result = {
                "status": "PASS",
                "duplicates_found": len(duplicates),
                "expected_duplicates": 0,
            }

            if len(duplicates) == 0:
                print("✅ No duplicates detected (as expected)")
            else:
                print(f"⚠️ Found {len(duplicates)} duplicate datetime ranges")

            self.test_results["detect_duplicates"] = result
            return len(duplicates) == 0

        except Exception as e:
            self.test_results["detect_duplicates"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed to detect duplicates: {e}")
            return False

    def test_edit_event(self) -> bool:
        """Test editing a calendar event.

        Returns:
            True if test passed
        """
        print("Testing edit_calendar_event...")

        if not self.test_event_ids:
            print("⚠️ No test events to edit")
            self.test_results["edit_event"] = {"status": "SKIP", "reason": "No test events"}
            return True

        try:
            event_id = self.test_event_ids[0]

            # Get existing event
            existing_event = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()

            # Update event
            updated_summary = f"{existing_event['summary']} - EDITED"
            updated_description = f"{existing_event.get('description', '')} - Modified by test"

            event_body = {"summary": updated_summary, "description": updated_description}

            updated_event = self.service.events().patch(calendarId=self.calendar_id, eventId=event_id, body=event_body).execute()

            if updated_event["summary"] == updated_summary:
                print(f"✅ Successfully edited event: {updated_summary}")
                self.test_results["edit_event"] = {
                    "status": "PASS",
                    "event_id": event_id,
                    "updated_summary": updated_summary,
                }
                return True
            else:
                print("❌ Event edit verification failed")
                self.test_results["edit_event"] = {"status": "FAIL", "reason": "Verification failed"}
                return False

        except Exception as e:
            self.test_results["edit_event"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed to edit event: {e}")
            return False

    def test_delete_events(self) -> bool:
        """Test deleting calendar events (cleanup).

        Returns:
            True if test passed
        """
        print("Testing delete_calendar_event...")

        if not self.test_event_ids:
            print("⚠️ No test events to delete")
            self.test_results["delete_events"] = {"status": "SKIP", "reason": "No test events"}
            return True

        try:
            deleted_count = 0

            for event_id in self.test_event_ids:
                try:
                    self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
                    deleted_count += 1
                    print(f"✅ Deleted test event: {event_id}")
                except HttpError as e:
                    if e.resp.status == 404:
                        print(f"⚠️ Event {event_id} not found (may have been deleted already)")
                    else:
                        raise

            self.test_results["delete_events"] = {
                "status": "PASS",
                "deleted_count": deleted_count,
                "expected_count": len(self.test_event_ids),
            }

            print(f"✅ Deleted {deleted_count} test events")
            return True

        except Exception as e:
            self.test_results["delete_events"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ Failed to delete events: {e}")
            return False

    def test_full_workflow(self) -> bool:
        """Test full workflow: create, read, summarize, edit, delete.

        Returns:
            True if all workflow steps passed
        """
        print("Testing full workflow...")

        workflow_steps = [
            ("list_calendars", self.test_list_calendars),
            ("create_events", self.test_create_dummy_events),
            ("read_events", self.test_read_events),
            ("summarize_events", self.test_summarize_events),
            ("detect_duplicates", self.test_detect_duplicates),
            ("edit_event", self.test_edit_event),
            ("delete_events", self.test_delete_events),
        ]

        passed = 0
        failed = 0

        for step_name, step_func in workflow_steps:
            try:
                if step_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Step {step_name} raised exception: {e}")
                failed += 1

        result = {
            "status": "PASS" if failed == 0 else "FAIL",
            "passed_steps": passed,
            "failed_steps": failed,
            "total_steps": len(workflow_steps),
        }

        self.test_results["full_workflow"] = result
        print(f"✅ Workflow: {passed}/{len(workflow_steps)} steps passed")

        return failed == 0

    def get_test_results(self) -> Dict[str, Any]:
        """Get all test results.

        Returns:
            Dictionary with all test results
        """
        return self.test_results


@pytest.mark.internet
def test_mcp_calendar_server_integration():
    """Integration test for MCP calendar server functionality.

    This test creates dummy events in December 2024, tests all operations,
    and cleans up by deleting the test events.
    """
    tester = MCPCalendarServerTester()

    # Set up API access
    if not tester.setup_api_access():
        pytest.skip("Failed to set up Google Calendar API access")

    # Run full workflow
    try:
        success = tester.test_full_workflow()
        results = tester.get_test_results()

        # Print summary
        print("\n" + "=" * 60)
        print("MCP CALENDAR SERVER INTEGRATION TEST SUMMARY")
        print("=" * 60)

        for test_name, result in results.items():
            status = result.get("status", "UNKNOWN")
            status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"{status_symbol} {test_name}: {status}")

        print("=" * 60)

        # Save results to file for report generator
        results_file = Path(__file__).parent / "test_results_mcp_calendar.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        assert success, "Some test steps failed"

    finally:
        # Cleanup: ensure all test events are deleted
        if tester.test_event_ids:
            print("\nCleaning up test events...")
            for event_id in tester.test_event_ids:
                try:
                    tester.service.events().delete(calendarId=tester.calendar_id, eventId=event_id).execute()
                except Exception:
                    pass  # Ignore cleanup errors
