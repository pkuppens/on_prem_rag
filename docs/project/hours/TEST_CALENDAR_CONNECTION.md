# Testing Calendar Connection and Credentials

This guide explains how to test your Google Calendar credentials and MCP calendar server connection.

## Quick Start

### Option 1: Test Credentials Directly (Recommended First Step)

Test your Google Calendar credentials without the MCP server:

```bash
uv run test-calendar-credentials
```

Or:

```bash
uv run python scripts/test_calendar_credentials.py
```

**What it does:**

- Checks if `credentials.json` and `token.json` exist
- Validates the token is not expired
- Attempts to refresh expired tokens automatically
- Tests API access by listing your calendars
- Verifies the WBSO calendar is accessible

**Expected output:**

```
======================================================================
Google Calendar Credentials Test
======================================================================

Credentials file: .../credentials.json
Token file: .../token.json

Loading credentials...
✓ Token file loaded successfully
Checking credential validity...
✓ Credentials are valid

Testing API access by listing calendars...
✓ Successfully connected to Google Calendar API
✓ Found X accessible calendar(s)

✓ WBSO calendar 'WBSO Activities 2025' found
  Calendar ID: ...
  Access Role: owner

======================================================================
✓ TEST PASSED: Credentials are valid
======================================================================
```

### Option 2: Test MCP Server Connection

Test the full MCP server connection and credentials:

```bash
uv run test-mcp-calendar-client
```

Or:

```bash
uv run python scripts/test_mcp_calendar_client.py
```

**What it does:**

- Starts the MCP calendar server as a subprocess
- Connects to it via stdio transport
- Lists available MCP tools
- Calls `list_calendars` tool to verify credentials
- Tests the complete MCP protocol flow

**Expected output:**

```
======================================================================
MCP Calendar Server Client Test
======================================================================

Starting MCP server: uv run mcp-calendar-server

Connecting to MCP server via stdio...
Initializing MCP session...
✓ MCP session initialized

Fetching available tools...
✓ Found 8 available tool(s)

Available tools:
  - list_calendars: List all accessible Google Calendars...
  - read_calendar_events: Read calendar events...
  ...

Testing Google Calendar credentials via list_calendars tool...

✓ Tool call successful

======================================================================
✓ TEST PASSED: MCP server connection and credentials are valid
======================================================================
```

## Troubleshooting

### Credentials File Not Found

**Error:**

```
Credentials file not found: .../credentials.json
```

**Solution:**

1. Follow the [Google Calendar API Setup Guide](scripts/setup_google_calendar_api.md)
2. Download `credentials.json` from Google Cloud Console
3. Place it in `docs/project/hours/scripts/credentials.json`

### Token File Not Found or Invalid

**Error:**

```
Token file not found: .../token.json
```

**Solution:**

1. Run the MCP server to trigger authentication:
   ```bash
   uv run mcp-calendar-server
   ```
2. Complete the OAuth flow in your browser
3. The token will be saved automatically

### Token Expired

**Error:**

```
Failed to refresh expired token: invalid_grant: Bad Request
```

**Solution:**

See the [Token Refresh Guide](REFRESH_GOOGLE_CALENDAR_TOKEN.md) for detailed instructions.

**Quick fix:**

1. Delete the old `token.json` file:

   ```bash
   # Windows
   del docs\project\hours\scripts\token.json

   # Linux/Mac
   rm docs/project/hours/scripts/token.json
   ```

2. Run the MCP server to re-authenticate:
   ```bash
   uv run mcp-calendar-server
   ```
3. Complete the OAuth flow in your browser

### WBSO Calendar Not Found

**Warning:**

```
⚠ WARNING: WBSO calendar 'WBSO Activities 2025' not found
```

**Solution:**

1. Create the calendar in Google Calendar
2. Ensure it's named exactly "WBSO Activities 2025"
3. Grant the OAuth app access to this calendar

### MCP Server Connection Failed

**Error:**

```
Error connecting to MCP server: ...
```

**Solution:**

1. First test credentials directly: `uv run test-calendar-credentials`
2. Make sure the MCP server can start: `uv run mcp-calendar-server`
3. Check that all dependencies are installed: `uv sync`

## Script Details

### test_calendar_credentials.py

**Purpose:** Direct Google Calendar API test without MCP

**Features:**

- Validates credential files exist
- Checks token validity
- Auto-refreshes expired tokens
- Tests API connectivity
- Lists accessible calendars
- Verifies WBSO calendar access

**When to use:**

- Quick credential validation
- Troubleshooting authentication issues
- Before setting up MCP client

### test_mcp_calendar_client.py

**Purpose:** Full MCP server integration test

**Features:**

- Starts MCP server as subprocess
- Connects via stdio transport
- Tests MCP protocol communication
- Lists available tools
- Calls calendar tools to verify credentials
- End-to-end integration test

**When to use:**

- After credentials are validated
- Testing MCP server functionality
- Verifying MCP client integration
- Before connecting external MCP clients

## Next Steps

After successful tests:

1. **Use with MCP Clients:**

   - Configure Claude Desktop to use the MCP server
   - Connect Cursor or other MCP-compatible tools
   - See [MCP Calendar Integration Guide](MCP_CALENDAR_INTEGRATION.md)

2. **Automate Calendar Operations:**

   - Use the MCP tools to manage calendar events
   - Integrate with git commit workflows
   - Automate WBSO hours registration

3. **Monitor and Maintain:**
   - Run credential tests periodically
   - Refresh tokens before they expire
   - Keep credentials secure

## Related Documentation

- [Token Refresh Guide](REFRESH_GOOGLE_CALENDAR_TOKEN.md) - **How to refresh expired tokens**
- [MCP Calendar Integration Guide](MCP_CALENDAR_INTEGRATION.md) - Full integration guide
- [MCP Calendar Server Technical Docs](../../technical/MCP_CALENDAR_SERVER.md) - Technical details
- [Google Calendar API Setup](scripts/setup_google_calendar_api.md) - Initial setup
