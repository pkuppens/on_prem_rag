# Google Calendar API Setup Guide

This guide provides step-by-step instructions for setting up Google Calendar API access for the WBSO hours registration project.

## Prerequisites

- Google account with access to Google Calendar
- Python 3.7 or higher
- Internet connection for API access

## Step 1: Install Required Dependencies

First, install the required Python packages for Google Calendar API access:

```bash
# Using uv (recommended)
uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Or using pip (if uv is not available)
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 2: Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. In the Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application" as the application type
4. Give it a name (e.g., "WBSO Calendar Extractor")
5. Click "Create"
6. Download the credentials file (JSON format)
7. Rename the downloaded file to `credentials.json`
8. Place it in the `docs/project/hours/scripts/` directory

## Step 4: Configure Calendar Access

1. Make sure your Google account has access to all the calendars you want to extract
2. For shared calendars, ensure you have at least "See all event details" permission
3. For subscribed calendars, make sure they are visible in your Google Calendar

## Step 5: Test the Setup

Run the calendar extraction script to test the setup:

```bash
cd docs/project/hours/scripts/
python google_calendar_extractor.py
```

The first time you run this, it will:

1. Open a browser window for OAuth authentication
2. Ask you to sign in to your Google account
3. Request permission to access your calendars
4. Save the authentication token for future use

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**

   - Make sure `credentials.json` is in the correct directory
   - Check that the file name is exactly `credentials.json`

2. **"Access denied" errors**

   - Ensure the Google Calendar API is enabled in your Google Cloud project
   - Check that your OAuth consent screen is configured properly
   - Verify that you're using the correct Google account

3. **"No calendars discovered"**

   - Check that you have access to calendars in your Google Calendar
   - Ensure shared calendars are properly shared with your account
   - Verify that subscribed calendars are visible

4. **Import errors**
   - Make sure all required packages are installed
   - Check Python version (requires 3.7+)
   - Try reinstalling the packages

### OAuth Consent Screen Configuration

If you encounter OAuth consent screen issues:

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "WBSO Calendar Extractor"
   - User support email: Your email
   - Developer contact information: Your email
4. Add the following scopes:
   - `https://www.googleapis.com/auth/calendar.readonly`
5. Add your email as a test user
6. Save and continue

### API Quotas and Limits

- Google Calendar API has quotas for requests per day
- For personal use, the default quotas should be sufficient
- If you hit quota limits, you may need to request an increase

## Security Considerations

1. **Keep credentials secure**

   - Don't commit `credentials.json` or `token.json` to version control
   - Add these files to `.gitignore`
   - Keep them in a secure location

2. **Token management**

   - The script automatically refreshes expired tokens
   - Tokens are stored locally in `token.json`
   - You can delete `token.json` to force re-authentication

3. **Data privacy**
   - Calendar data is processed locally
   - No data is sent to external services
   - Review the extracted data before sharing

## Manual Export Alternative

If API access is not possible, you can manually export calendar data:

1. Go to Google Calendar
2. Click the gear icon > Settings
3. Go to "Import & Export" tab
4. Click "Export"
5. Download the ZIP file containing iCal files
6. Use a calendar viewer to extract the data manually

## Next Steps

After successful setup:

1. Run the calendar extraction script
2. Review the generated CSV file
3. Check the summary report
4. Proceed with conflict detection and WBSO calendar creation

## Support

If you encounter issues:

1. Check the log file `calendar_extraction.log` for detailed error messages
2. Verify all prerequisites are met
3. Test with a simple calendar first
4. Check Google Cloud Console for API usage and errors

## Related Documentation

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 Setup Guide](https://developers.google.com/identity/protocols/oauth2)
- [TASK-005-GOOGLE-CALENDAR-INTEGRATION.md](../TASK-005-GOOGLE-CALENDAR-INTEGRATION.md)
