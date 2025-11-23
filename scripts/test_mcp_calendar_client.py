#!/usr/bin/env python3
"""
MCP Calendar Server Client Test

This script creates an MCP client that connects to the MCP calendar server
via stdio transport and tests the connection by calling the list_calendars tool.
This verifies both the MCP server connection and the Google Calendar credentials.

Usage:
    uv run python scripts/test_mcp_calendar_client.py

Author: AI Assistant
Created: 2025-11-15
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from mcp import ClientSession, StdioServerParameters, stdio_client
except ImportError as e:
    print(f"ERROR: MCP client dependencies not installed: {e}", file=sys.stderr)
    print("MCP should be installed via: uv add mcp", file=sys.stderr)
    sys.exit(1)


async def test_mcp_connection():
    """Test connection to MCP calendar server and verify credentials.

    Returns:
        tuple: (success: bool, message: str, result: dict)
    """
    print("=" * 70)
    print("MCP Calendar Server Client Test")
    print("=" * 70)
    print()

    # Get the path to the mcp-calendar-server command
    # This should work with uv run
    server_command = ["uv", "run", "mcp-calendar-server"]

    print(f"Starting MCP server: {' '.join(server_command)}")
    print()

    try:
        # Create stdio server parameters
        server_params = StdioServerParameters(
            command=server_command[0],
            args=server_command[1:],
            env=None,
        )

        print("Connecting to MCP server via stdio...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                print("Initializing MCP session...")
                await session.initialize()

                print("[OK] MCP session initialized")
                print()

                # List available tools
                print("Fetching available tools...")
                tools = await session.list_tools()
                print(f"[OK] Found {len(tools.tools)} available tool(s)")
                print()
                print("Available tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                print()

                # Test credentials by calling list_calendars
                print("Testing Google Calendar credentials via list_calendars tool...")
                print()

                try:
                    result = await session.call_tool("list_calendars", arguments={})
                    print("[OK] Tool call successful")
                    print()

                    # Parse the result
                    if result.content and len(result.content) > 0:
                        result_text = result.content[0].text
                        result_data = json.loads(result_text)

                        if "error" in result_data:
                            error_msg = result_data.get("error", "Unknown error")
                            return False, f"Tool returned error: {error_msg}", result_data

                        calendars = result_data.get("calendars", [])
                        count = result_data.get("count", 0)

                        print("=" * 70)
                        print("[PASS] TEST PASSED: MCP server connection and credentials are valid")
                        print()
                        print("Results:")
                        print(f"  Calendars found: {count}")
                        print()

                        if calendars:
                            print("  Calendars:")
                            for calendar in calendars:
                                print(f"    - {calendar.get('summary')} (ID: {calendar.get('id')})")
                                print(f"      Access Role: {calendar.get('accessRole')}")
                                print(f"      Timezone: {calendar.get('timeZone', 'N/A')}")
                                print()

                        # Check for WBSO calendar
                        from wbso.upload import WBSO_CALENDAR_NAME

                        wbso_found = any(
                            cal.get("summary") == WBSO_CALENDAR_NAME for cal in calendars
                        )
                        if wbso_found:
                            print(f"  [OK] WBSO calendar '{WBSO_CALENDAR_NAME}' is accessible")
                        else:
                            print(f"  [WARNING] WBSO calendar '{WBSO_CALENDAR_NAME}' not found in results")

                        return True, "MCP connection and credentials are valid", result_data
                    else:
                        return False, "Tool returned empty result", {}

                except Exception as e:
                    return False, f"Error calling list_calendars tool: {e}", {}

    except FileNotFoundError:
        return False, f"MCP server command not found. Make sure 'uv run mcp-calendar-server' works.", {}
    except Exception as e:
        return False, f"Error connecting to MCP server: {e}", {}


async def main():
    """Main entry point."""
    success, message, result = await test_mcp_connection()

    print()
    print("=" * 70)
    if success:
        print("Summary:")
        print(f"  Status: {message}")
        print()
        print("Next steps:")
        print("  1. Your MCP calendar server is working correctly")
        print("  2. Your Google Calendar credentials are valid")
        print("  3. You can now use the MCP server with MCP clients (e.g., Claude Desktop, Cursor)")
    else:
        print("[FAIL] TEST FAILED")
        print()
        print(f"Error: {message}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure the MCP server can start: uv run mcp-calendar-server")
        print("  2. Test credentials directly: uv run test-calendar-credentials")
        print("  3. For token refresh instructions, see:")
        print("     docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md")
        print("  4. Check that credentials.json and token.json exist")
        print("  5. Verify Google Calendar API is enabled in your Google Cloud project")
    print("=" * 70)

    sys.exit(0 if success else 1)


def main_sync():
    """Synchronous wrapper for main() to be used as entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()

