#!/usr/bin/env python3
"""
Explicitly trigger Google Calendar OAuth authentication.

This script forces the OAuth flow to run, which is useful when:
- Token has expired and needs to be refreshed
- Token.json doesn't exist and needs to be created
- You want to re-authenticate with a different account

Usage:
    uv run python scripts/authenticate_google_calendar.py

Author: AI Assistant
Created: 2025-11-15
"""

import os
import sys
from pathlib import Path

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"ERROR: Google Calendar API dependencies not installed: {e}", file=sys.stderr)
    print("Install with: uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)

from wbso.upload import SCOPES


def authenticate():
    """Explicitly trigger Google Calendar OAuth authentication.

    Returns:
        bool: True if authentication successful, False otherwise
    """
    # Get credentials paths
    script_dir = Path(__file__).parent.parent / "docs" / "project" / "hours" / "scripts"
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", script_dir / "credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", script_dir / "token.json"))

    print("=" * 70)
    print("Google Calendar OAuth Authentication")
    print("=" * 70)
    print()
    print(f"Credentials file: {credentials_path}")
    print(f"Token file: {token_path}")
    print()

    # Check if credentials file exists
    if not credentials_path.exists():
        print(f"[ERROR] Credentials file not found: {credentials_path}")
        print()
        print("Please download credentials.json from Google Cloud Console:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Select your project")
        print("  3. Navigate to APIs & Services > Credentials")
        print("  4. Download OAuth 2.0 Client ID credentials")
        print(f"  5. Save as: {credentials_path}")
        return False

    # Delete existing token if it exists (to force re-authentication)
    if token_path.exists():
        print(f"[INFO] Existing token found at: {token_path}")
        response = input("Delete existing token and re-authenticate? (y/n): ").strip().lower()
        if response == "y":
            try:
                token_path.unlink()
                print("[OK] Existing token deleted")
            except Exception as e:
                print(f"[ERROR] Failed to delete token: {e}")
                return False
        else:
            print("[INFO] Keeping existing token, attempting to use it...")
    else:
        print("[INFO] No existing token found, will create new one")

    print()
    print("Starting OAuth authentication flow...")
    print("A browser window should open automatically.")
    print("If it doesn't, check the console for a URL to open manually.")
    print()
    print("=" * 70)
    print("IMPORTANT: OAuth Scope Warning")
    print("=" * 70)
    print()
    print("Google will show a warning that this app can 'See, edit, share, and")
    print("permanently delete all the calendars you can access using Google Calendar.'")
    print()
    print("This is a technical limitation of Google Calendar API OAuth scopes.")
    print("However, our application implements code-level security to ensure:")
    print("  - Read access: All calendars (for duplicate detection)")
    print("  - Write access: ONLY the WBSO calendar")
    print()
    print("All write operations are validated and restricted to the WBSO calendar.")
    print("See docs/project/hours/CALENDAR_SECURITY.md for details.")
    print()
    print("=" * 70)
    print()

    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)

        # Run the OAuth flow - this will open a browser
        creds = flow.run_local_server(port=0)

        print()
        print("[OK] Authentication successful!")
        print()

        # Save the credentials
        try:
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            print(f"[OK] Token saved to: {token_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save token: {e}")
            return False

        # Test the credentials by listing calendars
        print()
        print("Testing credentials by listing calendars...")
        try:
            service = build("calendar", "v3", credentials=creds)
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            print(f"[OK] Successfully connected! Found {len(calendars)} calendar(s)")

            if calendars:
                print()
                print("Accessible calendars:")
                for calendar in calendars[:20]:  # Show first 5
                    print(f"  - {calendar.get('summary')} ({calendar.get('accessRole')})")
                if len(calendars) > 20:
                    print(f"  ... and {len(calendars) - 20} more")
        except Exception as e:
            print(f"[WARNING] Credentials saved but test failed: {e}")
            print("You may need to check your Google Calendar API access")

        print()
        print("=" * 70)
        print("[SUCCESS] Authentication complete!")
        print("=" * 70)
        return True

    except KeyboardInterrupt:
        print()
        print("[INFO] Authentication cancelled by user")
        return False
    except Exception as e:
        print()
        print(f"[ERROR] Authentication failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check that credentials.json is valid")
        print("  2. Verify Google Calendar API is enabled in your project")
        print("  3. Check your internet connection")
        print("  4. See docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md for more help")
        return False


def main():
    """Main entry point."""
    success = authenticate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
