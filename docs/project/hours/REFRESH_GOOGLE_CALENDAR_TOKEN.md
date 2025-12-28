# Refresh Google Calendar OAuth Token

## Quick Fix: Re-authenticate

When your Google Calendar OAuth token expires (typically after 6 months of inactivity), you need to re-authenticate.

### Step 1: Delete the Expired Token

Delete the expired token file:

```bash
# Windows
del docs\project\hours\scripts\token.json

# Linux/Mac
rm docs/project/hours/scripts/token.json
```

### Step 2: Re-authenticate

**Option A: Use the authentication script (Recommended)**

Run the dedicated authentication script:

```bash
uv run authenticate-google-calendar
```

**What happens:**

1. The script checks for credentials.json
2. Optionally deletes the old token (if it exists)
3. A browser window opens automatically
4. Sign in with your Google account
5. Grant calendar access permissions
6. The new token is saved automatically to `token.json`
7. Tests the connection by listing your calendars

**Option B: Trigger authentication via MCP server**

If you prefer to use the MCP server:

1. Start the MCP server:

   ```bash
   uv run mcp-calendar-server
   ```

2. **Important:** The server only authenticates when you actually use a calendar tool. You need to:
   - Connect an MCP client (e.g., Claude Desktop, Cursor)
   - Call a calendar tool like `list_calendars`
   - This will trigger the OAuth flow

**Note:** The MCP server does NOT authenticate on startup - it only authenticates when a tool is invoked.

### Step 3: Verify

Test that the new token works:

```bash
uv run test-calendar-credentials
```

## Why Tokens Expire

Google OAuth tokens can expire for several reasons:

- **Inactivity**: Tokens expire after 6 months of no use
- **Revoked access**: If you revoke access in your Google Account settings
- **Security**: Google may revoke tokens for security reasons
- **Refresh token invalid**: The refresh token itself may have expired

## Troubleshooting

### "invalid_grant: Bad Request" Error

This means the refresh token is invalid. **Solution:**

1. Delete `token.json`
2. Run `uv run authenticate-google-calendar` to re-authenticate

### Token Not Created After Running MCP Server

**Problem:** You deleted `token.json` and ran `uv run mcp-calendar-server`, but the token wasn't created.

**Cause:** The MCP server only authenticates when you actually use a calendar tool. It doesn't authenticate on startup.

**Solution:** Use the dedicated authentication script instead:

```bash
uv run authenticate-google-calendar
```

This script explicitly triggers the OAuth flow and creates the token.

### Browser Doesn't Open

If the browser doesn't open automatically:

1. Check the console output for a URL
2. Copy the URL and open it manually in your browser
3. Complete the authentication flow
4. The token will be saved automatically

### "Credentials file not found" Error

You need to download `credentials.json` from Google Cloud Console first:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** > **Credentials**
4. Download the OAuth 2.0 Client ID credentials
5. Save as `docs/project/hours/scripts/credentials.json`

See the [Google Calendar API Setup Guide](scripts/setup_google_calendar_api.md) for detailed instructions.

## Related Documentation

- [Google Calendar API Setup Guide](scripts/setup_google_calendar_api.md) - Initial setup instructions
- [MCP Calendar Integration Guide](MCP_CALENDAR_INTEGRATION.md) - Integration overview
- [Test Calendar Connection](TEST_CALENDAR_CONNECTION.md) - Testing credentials

## Online Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [OAuth Token Refresh Guide](https://developers.google.com/identity/protocols/oauth2/web-server#offline)
