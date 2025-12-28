#!/usr/bin/env python3
"""
Test Google Calendar Credentials Validity

This script directly tests if the configured Google Calendar credentials and token
are still valid (not expired, revoked, or otherwise invalid) by attempting to
connect to the Google Calendar API and list calendars.

Usage:
    uv run python scripts/test_calendar_credentials.py

Author: AI Assistant
Created: 2025-11-15
"""

import json
import os
import sys
from pathlib import Path

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"ERROR: Google Calendar API dependencies not installed: {e}", file=sys.stderr)
    print("Install with: uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)

from wbso.upload import SCOPES, WBSO_CALENDAR_NAME


def get_credentials_paths():
    """Get paths to credentials and token files."""
    script_dir = Path(__file__).parent.parent / "docs" / "project" / "hours" / "scripts"
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", script_dir / "credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", script_dir / "token.json"))
    return credentials_path, token_path


def test_credentials():
    """Test if Google Calendar credentials are valid.

    Returns:
        tuple: (success: bool, message: str, calendars: list)
    """
    credentials_path, token_path = get_credentials_paths()

    print("=" * 70)
    print("Google Calendar Credentials Test")
    print("=" * 70)
    print()
    print(f"Credentials file: {credentials_path}")
    print(f"Token file: {token_path}")
    print()

    # Check if files exist
    if not credentials_path.exists():
        return False, f"Credentials file not found: {credentials_path}", []

    if not token_path.exists():
        return False, f"Token file not found: {token_path}. You need to authenticate first.", []

    # Load credentials
    print("Loading credentials...")
    creds = None
    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        print("[OK] Token file loaded successfully")
    except Exception as e:
        return False, f"Failed to load token file: {e}", []

    # Check if credentials are valid
    print("Checking credential validity...")
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                print("[OK] Token refreshed successfully")
                # Save refreshed token
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                print("[OK] Refreshed token saved")
            except Exception as e:
                error_msg = (
                    f"Failed to refresh expired token: {e}\n\n"
                    f"Your token has expired and cannot be automatically refreshed.\n"
                    f"Please follow the instructions in:\n"
                    f"  docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md\n\n"
                    f"Quick fix: Delete token.json and run 'uv run authenticate-google-calendar' to re-authenticate."
                )
                return False, error_msg, []
        else:
            return False, "Credentials are invalid and cannot be refreshed. Please re-authenticate.", []

    print("[OK] Credentials are valid")
    print()

    # Test API access by listing calendars
    print("Testing API access by listing calendars...")
    try:
        service = build("calendar", "v3", credentials=creds)
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])

        print(f"[OK] Successfully connected to Google Calendar API")
        print(f"[OK] Found {len(calendars)} accessible calendar(s)")
        print()

        # Check for WBSO calendar
        wbso_calendar_found = False
        for calendar in calendars:
            if calendar.get("summary") == WBSO_CALENDAR_NAME:
                wbso_calendar_found = True
                print(f"[OK] WBSO calendar '{WBSO_CALENDAR_NAME}' found")
                print(f"  Calendar ID: {calendar.get('id')}")
                print(f"  Access Role: {calendar.get('accessRole')}")
                break

        if not wbso_calendar_found:
            print(f"[WARNING] WBSO calendar '{WBSO_CALENDAR_NAME}' not found")
            print("  Available calendars:")
            for calendar in calendars[:20]:  # Show first 5
                print(f"    - {calendar.get('summary')} (ID: {calendar.get('id')})")
            if len(calendars) > 20:
                print(f"    ... and {len(calendars) - 20} more")

        return True, "Credentials are valid and API access works", calendars

    except HttpError as e:
        error_details = json.loads(e.content.decode("utf-8"))
        error_message = error_details.get("error", {}).get("message", str(e))
        return False, f"HTTP error accessing Google Calendar API: {error_message}", []
    except Exception as e:
        return False, f"Error accessing Google Calendar API: {e}", []


def main():
    """Main entry point."""
    success, message, calendars = test_credentials()

    print()
    print("=" * 70)
    if success:
        print("[PASS] TEST PASSED: Credentials are valid")
        print()
        print("Summary:")
        print(f"  Status: {message}")
        print(f"  Calendars accessible: {len(calendars)}")
        if calendars:
            print()
            print("Available calendars:")
            for calendar in calendars:
                print(f"  - {calendar.get('summary')} ({calendar.get('accessRole')})")
    else:
        print("[FAIL] TEST FAILED: Credentials are invalid or cannot be accessed")
        print()
        print(f"Error: {message}")
        print()
        print("Troubleshooting:")
        print("  1. Check if credentials.json exists and is valid")
        print("  2. Check if token.json exists and is not corrupted")
        print("  3. For token refresh instructions, see:")
        print("     docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md")
        print("  4. Quick fix: Delete token.json and run:")
        print("     uv run authenticate-google-calendar")
        print("  5. Verify you have granted calendar access permissions")
    print("=" * 70)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
