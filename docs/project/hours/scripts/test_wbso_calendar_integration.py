#!/usr/bin/env python3
"""
WBSO Calendar Integration Testing Script

This script implements automated testing for WBSO calendar integration as specified in
the project tasks. It tests calendar detection, CRUD operations, and validates
full functionality with a test record outside the WBSO range.

Tasks Implemented:
- [x] **Subtask 1.4**: Test WBSO calendar detection and access
- [x] **Subtask 1.5**: Test basic CRUD operations on WBSO calendar
- [x] **Subtask 1.6**: Validate calendar integration is fully functional

See docs/project/hours/TASK-005-GOOGLE-CALENDAR-INTEGRATION.md for detailed requirements.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing Google Calendar API dependencies: {e}")
    print("Please install: uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wbso_calendar_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WBSOCalendarTester:
    """Comprehensive testing class for WBSO calendar integration."""

    def __init__(self, config_dir: str = "../config", data_dir: str = "../data"):
        """Initialize the WBSO calendar tester.

        Args:
            config_dir: Directory containing configuration files
            data_dir: Directory for data storage and output
        """
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.service = None
        self.wbso_calendar_id = None
        self.test_results = {}

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration files
        self.wbso_config = self._load_config("wbso_calendar_config.json")
        self.categorization_rules = self._load_config("calendar_categorization_rules.json")

        # API configuration
        self.SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]
        self.CREDENTIALS_FILE = "credentials.json"
        self.TOKEN_FILE = "token.json"

        # Test configuration
        self.test_date = "2025-05-31"  # Out of WBSO range for testing
        self.test_event_title = "WBSO Test Event - Integration Testing"
        self.test_event_description = "Test event for WBSO calendar integration validation"

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
        logger.info("Setting up Google Calendar API access...")

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

    def test_wbso_calendar_detection(self) -> bool:
        """Test WBSO calendar detection and access.

        Returns:
            True if WBSO calendar is found and accessible
        """
        logger.info("Testing WBSO calendar detection and access...")

        if not self.service:
            logger.error("Calendar service not initialized")
            return False

        try:
            # Discover all calendars
            calendar_list = self.service.calendarList().list().execute()
            if not calendar_list:
                logger.error("Failed to retrieve calendar list")
                return False

            calendars = calendar_list.get("items", [])
            if not calendars:
                logger.error("No calendars found in calendar list")
                return False

            # Look for WBSO calendar
            wbso_calendar = None
            for calendar in calendars:
                summary = calendar.get("summary", "")
                if "WBSO" in summary or "wbso" in summary.lower():
                    wbso_calendar = calendar
                    break

            if not wbso_calendar:
                logger.warning("WBSO calendar not found in calendar list")
                logger.info("Available calendars:")
                for cal in calendars:
                    logger.info(f"  - {cal.get('summary', 'Unknown')} ({cal.get('id', 'No ID')})")

                # Try to create WBSO calendar if not found
                return self.create_wbso_calendar()

            # Test access to WBSO calendar
            calendar_id = wbso_calendar["id"]
            try:
                calendar_info = self.service.calendars().get(calendarId=calendar_id).execute()
                logger.info(f"Successfully accessed WBSO calendar: {calendar_info.get('summary', 'Unknown')}")

                self.wbso_calendar_id = calendar_id
                self.test_results["calendar_detection"] = {
                    "status": "PASS",
                    "calendar_id": calendar_id,
                    "summary": calendar_info.get("summary", "Unknown"),
                    "access_role": wbso_calendar.get("accessRole", "unknown"),
                }
                return True

            except HttpError as e:
                logger.error(f"Failed to access WBSO calendar: {e}")
                self.test_results["calendar_detection"] = {"status": "FAIL", "error": str(e)}
                return False

        except Exception as e:
            logger.error(f"Failed to detect WBSO calendar: {e}")
            self.test_results["calendar_detection"] = {"status": "FAIL", "error": str(e)}
            return False

    def create_wbso_calendar(self) -> bool:
        """Create WBSO calendar if it doesn't exist.

        Returns:
            True if calendar creation was successful
        """
        logger.info("Creating new WBSO calendar...")

        try:
            calendar_body = {
                "summary": self.wbso_config["calendar_settings"]["name"],
                "description": self.wbso_config["calendar_settings"]["description"],
                "timeZone": self.wbso_config["calendar_settings"]["timezone"],
            }

            created_calendar = self.service.calendars().insert(body=calendar_body).execute()
            calendar_id = created_calendar["id"]

            logger.info(f"Successfully created WBSO calendar: {created_calendar['summary']}")
            self.wbso_calendar_id = calendar_id

            self.test_results["calendar_creation"] = {
                "status": "PASS",
                "calendar_id": calendar_id,
                "summary": created_calendar["summary"],
            }
            return True

        except Exception as e:
            logger.error(f"Failed to create WBSO calendar: {e}")
            self.test_results["calendar_creation"] = {"status": "FAIL", "error": str(e)}
            return False

    def test_crud_operations(self) -> bool:
        """Test basic CRUD operations on WBSO calendar.

        Returns:
            True if all CRUD operations pass
        """
        logger.info("Testing basic CRUD operations on WBSO calendar...")

        if not self.wbso_calendar_id:
            logger.error("WBSO calendar ID not set")
            return False

        try:
            # Test CREATE operation
            create_success = self.test_create_operation()

            # Test READ operation
            read_success = self.test_read_operation()

            # Test UPDATE operation
            update_success = self.test_update_operation()

            # Test DELETE operation
            delete_success = self.test_delete_operation()

            # Overall CRUD test result
            crud_success = all([create_success, read_success, update_success, delete_success])

            self.test_results["crud_operations"] = {
                "status": "PASS" if crud_success else "FAIL",
                "create": "PASS" if create_success else "FAIL",
                "read": "PASS" if read_success else "FAIL",
                "update": "PASS" if update_success else "FAIL",
                "delete": "PASS" if delete_success else "FAIL",
            }

            return crud_success

        except Exception as e:
            logger.error(f"Failed to test CRUD operations: {e}")
            self.test_results["crud_operations"] = {"status": "FAIL", "error": str(e)}
            return False

    def test_create_operation(self) -> bool:
        """Test CREATE operation by adding a test event.

        Returns:
            True if event creation was successful
        """
        logger.info("Testing CREATE operation...")

        try:
            # Create test event on 2025/05/31 (out of WBSO range)
            event_body = {
                "summary": self.test_event_title,
                "description": self.test_event_description,
                "start": {"dateTime": f"{self.test_date}T10:00:00+02:00", "timeZone": "Europe/Amsterdam"},
                "end": {"dateTime": f"{self.test_date}T12:00:00+02:00", "timeZone": "Europe/Amsterdam"},
                "colorId": "1",  # Blue color for WBSO activities
                "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 15}]},
            }

            created_event = self.service.events().insert(calendarId=self.wbso_calendar_id, body=event_body).execute()

            event_id = created_event["id"]
            logger.info(f"Successfully created test event: {event_id}")

            # Store event ID for subsequent tests
            self.test_event_id = event_id

            self.test_results["create_operation"] = {
                "status": "PASS",
                "event_id": event_id,
                "event_title": created_event["summary"],
            }
            return True

        except Exception as e:
            logger.error(f"Failed to create test event: {e}")
            self.test_results["create_operation"] = {"status": "FAIL", "error": str(e)}
            return False

    def test_read_operation(self) -> bool:
        """Test READ operation by retrieving the test event.

        Returns:
            True if event retrieval was successful
        """
        logger.info("Testing READ operation...")

        if not hasattr(self, "test_event_id"):
            logger.error("Test event ID not available")
            return False

        try:
            # Retrieve the test event
            retrieved_event = self.service.events().get(calendarId=self.wbso_calendar_id, eventId=self.test_event_id).execute()

            # Verify event details
            if (
                retrieved_event["summary"] == self.test_event_title
                and retrieved_event["description"] == self.test_event_description
            ):
                logger.info("Successfully retrieved test event with correct details")

                self.test_results["read_operation"] = {
                    "status": "PASS",
                    "event_id": self.test_event_id,
                    "retrieved_title": retrieved_event["summary"],
                }
                return True
            else:
                logger.error("Retrieved event details don't match created event")
                self.test_results["read_operation"] = {"status": "FAIL", "error": "Event details mismatch"}
                return False

        except Exception as e:
            logger.error(f"Failed to retrieve test event: {e}")
            self.test_results["read_operation"] = {"status": "FAIL", "error": str(e)}
            return False

    def test_update_operation(self) -> bool:
        """Test UPDATE operation by modifying the test event.

        Returns:
            True if event update was successful
        """
        logger.info("Testing UPDATE operation...")

        if not hasattr(self, "test_event_id"):
            logger.error("Test event ID not available")
            return False

        try:
            # Update event details
            updated_title = f"{self.test_event_title} - UPDATED"
            updated_description = f"{self.test_event_description} - Modified for testing"

            event_body = {"summary": updated_title, "description": updated_description}

            updated_event = (
                self.service.events().patch(calendarId=self.wbso_calendar_id, eventId=self.test_event_id, body=event_body).execute()
            )

            # Verify update
            if updated_event["summary"] == updated_title and updated_event["description"] == updated_description:
                logger.info("Successfully updated test event")

                self.test_results["update_operation"] = {
                    "status": "PASS",
                    "event_id": self.test_event_id,
                    "updated_title": updated_title,
                }
                return True
            else:
                logger.error("Event update verification failed")
                self.test_results["update_operation"] = {"status": "FAIL", "error": "Update verification failed"}
                return False

        except Exception as e:
            logger.error(f"Failed to update test event: {e}")
            self.test_results["update_operation"] = {"status": "FAIL", "error": str(e)}
            return False

    def test_delete_operation(self) -> bool:
        """Test DELETE operation by removing the test event.

        Returns:
            True if event deletion was successful
        """
        logger.info("Testing DELETE operation...")

        if not hasattr(self, "test_event_id"):
            logger.error("Test event ID not available")
            return False

        try:
            # Delete the test event
            self.service.events().delete(calendarId=self.wbso_calendar_id, eventId=self.test_event_id).execute()

            logger.info("Successfully deleted test event")

            # Verify deletion by attempting to retrieve the event
            try:
                self.service.events().get(calendarId=self.wbso_calendar_id, eventId=self.test_event_id).execute()

                # If we get here, deletion failed
                logger.error("Event deletion verification failed - event still exists")
                self.test_results["delete_operation"] = {"status": "FAIL", "error": "Event still exists after deletion"}
                return False

            except HttpError as e:
                if e.resp.status == 404:
                    logger.info("Event deletion verified - event no longer exists")

                    self.test_results["delete_operation"] = {"status": "PASS", "event_id": self.test_event_id}
                    return True
                else:
                    raise e

        except Exception as e:
            logger.error(f"Failed to delete test event: {e}")
            self.test_results["delete_operation"] = {"status": "FAIL", "error": str(e)}
            return False

    def validate_calendar_integration(self) -> bool:
        """Validate that calendar integration is fully functional.

        Returns:
            True if all validation checks pass
        """
        logger.info("Validating calendar integration functionality...")

        try:
            # Test calendar access
            if not self.wbso_calendar_id:
                logger.error("WBSO calendar ID not set for validation")
                return False

            # Test calendar properties
            calendar_info = self.service.calendars().get(calendarId=self.wbso_calendar_id).execute()

            # Verify essential properties
            required_properties = ["summary", "timeZone", "accessRole"]
            for prop in required_properties:
                if prop not in calendar_info:
                    logger.error(f"Missing required calendar property: {prop}")
                    return False

            # Test event listing capability
            events_result = self.service.events().list(calendarId=self.wbso_calendar_id, maxResults=10).execute()

            # Verify events can be listed (even if empty)
            if "items" not in events_result:
                logger.error("Calendar events listing failed")
                return False

            logger.info("Calendar integration validation successful")

            self.test_results["integration_validation"] = {
                "status": "PASS",
                "calendar_id": self.wbso_calendar_id,
                "summary": calendar_info.get("summary", "Unknown"),
                "timezone": calendar_info.get("timeZone", "Unknown"),
                "access_role": calendar_info.get("accessRole", "Unknown"),
            }
            return True

        except Exception as e:
            logger.error(f"Calendar integration validation failed: {e}")
            self.test_results["integration_validation"] = {"status": "FAIL", "error": str(e)}
            return False

    def generate_test_report(self) -> bool:
        """Generate comprehensive test report.

        Returns:
            True if report generation was successful
        """
        logger.info("Generating comprehensive test report...")

        try:
            # Calculate overall test status
            all_tests = ["calendar_detection", "crud_operations", "integration_validation"]

            passed_tests = sum(1 for test in all_tests if self.test_results.get(test, {}).get("status") == "PASS")
            total_tests = len(all_tests)

            overall_status = "PASS" if passed_tests == total_tests else "FAIL"

            # Generate report
            report = f"""# WBSO Calendar Integration Test Report

## Test Summary
- **Overall Status**: {overall_status}
- **Tests Passed**: {passed_tests}/{total_tests}
- **Test Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **WBSO Calendar ID**: {self.wbso_calendar_id or "Not Set"}

## Test Results

### 1. Calendar Detection and Access
- **Status**: {self.test_results.get("calendar_detection", {}).get("status", "NOT RUN")}
- **Details**: {self._format_test_details("calendar_detection")}

### 2. CRUD Operations
- **Status**: {self.test_results.get("crud_operations", {}).get("status", "NOT RUN")}
- **Details**: {self._format_test_details("crud_operations")}

### 3. Integration Validation
- **Status**: {self.test_results.get("integration_validation", {}).get("status", "NOT RUN")}
- **Details**: {self._format_test_details("integration_validation")}

## Test Event Details
- **Test Date**: {self.test_date} (Out of WBSO range for testing)
- **Event Title**: {self.test_event_title}
- **Event Description**: {self.test_event_description}

## Configuration
- **WBSO Calendar Name**: {self.wbso_config["calendar_settings"]["name"]}
- **Timezone**: {self.wbso_config["calendar_settings"]["timezone"]}
- **Access Level**: {self.wbso_config["calendar_settings"]["access_level"]}

## Recommendations
"""

            if overall_status == "PASS":
                report += "- ✅ All tests passed successfully\n"
                report += "- ✅ WBSO calendar integration is fully functional\n"
                report += "- ✅ Ready for production use\n"
            else:
                report += "- ❌ Some tests failed - review error details\n"
                report += "- ⚠️ Calendar integration may have issues\n"
                report += "- 🔧 Fix identified issues before production use\n"

            # Write report to file
            report_path = self.data_dir / "wbso_calendar_test_report.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # Also save test results as JSON for programmatic access
            results_path = self.data_dir / "wbso_calendar_test_results.json"
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, indent=2, default=str)

            logger.info(f"Test report generated: {report_path}")
            logger.info(f"Test results saved: {results_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to generate test report: {e}")
            return False

    def _format_test_details(self, test_name: str) -> str:
        """Format test details for report generation.

        Args:
            test_name: Name of the test to format

        Returns:
            Formatted test details string
        """
        test_result = self.test_results.get(test_name, {})

        if test_result.get("status") == "PASS":
            details = []
            for key, value in test_result.items():
                if key != "status":
                    details.append(f"{key}: {value}")
            return ", ".join(details) if details else "All checks passed"
        elif test_result.get("status") == "FAIL":
            return f"Error: {test_result.get('error', 'Unknown error')}"
        else:
            return "Test not run"

    def run_all_tests(self) -> bool:
        """Run all WBSO calendar integration tests.

        Returns:
            True if all tests pass
        """
        logger.info("Starting WBSO calendar integration tests...")

        try:
            # Test 1: Calendar Detection and Access
            logger.info("\n" + "=" * 60)
            logger.info("TEST 1: WBSO Calendar Detection and Access")
            logger.info("=" * 60)

            if not self.test_wbso_calendar_detection():
                logger.error("Calendar detection test failed")
                return False

            # Test 2: CRUD Operations
            logger.info("\n" + "=" * 60)
            logger.info("TEST 2: Basic CRUD Operations")
            logger.info("=" * 60)

            if not self.test_crud_operations():
                logger.error("CRUD operations test failed")
                return False

            # Test 3: Integration Validation
            logger.info("\n" + "=" * 60)
            logger.info("TEST 3: Calendar Integration Validation")
            logger.info("=" * 60)

            if not self.validate_calendar_integration():
                logger.error("Integration validation test failed")
                return False

            # Generate comprehensive report
            logger.info("\n" + "=" * 60)
            logger.info("GENERATING TEST REPORT")
            logger.info("=" * 60)

            if not self.generate_test_report():
                logger.error("Test report generation failed")
                return False

            logger.info("\n" + "=" * 60)
            logger.info("ALL TESTS COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return False


def main():
    """Main function to run the WBSO calendar integration tests."""
    print("WBSO Calendar Integration Testing Script")
    print("=" * 60)
    print("This script tests WBSO calendar detection, CRUD operations, and")
    print("validates full calendar integration functionality.")
    print()

    # Initialize tester
    tester = WBSOCalendarTester()

    # Setup API access
    print("1. Setting up Google Calendar API access...")
    if not tester.setup_api_access():
        print("❌ Failed to setup API access. Please check credentials.")
        print("   Ensure you have downloaded credentials.json from Google Cloud Console")
        return

    print("✅ API access established successfully")

    # Run all tests
    print("\n2. Running WBSO calendar integration tests...")
    if tester.run_all_tests():
        print("\n🎉 All tests completed successfully!")
        print("📊 Check the generated test report for detailed results")
        print(f"📁 Report location: {tester.data_dir}/wbso_calendar_test_report.md")
    else:
        print("\n❌ Some tests failed. Check the logs for details.")
        print("📊 Partial test results available in the generated report")

    print("\nTest execution completed!")
    print("Check wbso_calendar_test.log for detailed execution logs")


if __name__ == "__main__":
    main()
