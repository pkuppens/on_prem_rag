# Calendar Security and Least-Privilege Implementation

## Overview

This document explains the security model for Google Calendar access and how we implement least-privilege principles despite OAuth scope limitations.

## OAuth Scope Limitation

**Important:** Google Calendar API OAuth scopes don't support calendar-specific permissions. The available scopes are:

- `https://www.googleapis.com/auth/calendar` - Full read/write access to **ALL** calendars
- `https://www.googleapis.com/auth/calendar.readonly` - Read-only access to **ALL** calendars

**There is no scope that allows:**
- "Read all calendars, but write only to specific calendar X"
- "Read/write only to calendar X"

This means when you grant OAuth permission, Google will warn that the app can "See, edit, share, and permanently delete all the calendars you can access using Google Calendar."

## Our Security Implementation

Since OAuth scopes can't restrict write access to a specific calendar, we implement **code-level security** to enforce least-privilege:

### 1. Read Access (All Calendars)

**Why:** We need to read all calendars to detect duplicates and conflicts.

**Implementation:**
- Uses `calendar.readonly` scope where possible
- Reads from all accessible calendars for duplicate detection
- No restrictions on read operations

### 2. Write Access (WBSO Calendar Only)

**Why:** We only need to write to the WBSO calendar.

**Implementation:**
- **Strict validation** in `wbso.calendar_security.validate_wbso_calendar_write()`
- All write operations (create, update, delete) are validated before execution
- Only the WBSO calendar ID is allowed for write operations
- Attempts to write to other calendars are **blocked and logged as security violations**

### 3. Security Validation

The `validate_wbso_calendar_write()` function:

```python
def validate_wbso_calendar_write(
    calendar_id: str,
    allowed_calendar_id: Optional[str],
    calendar_name: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate that a write operation targets only the WBSO calendar."""
```

**What it does:**
- Compares the target calendar ID with the allowed WBSO calendar ID
- Blocks write operations to any other calendar
- Logs security violations
- Returns clear error messages

**Where it's used:**
- `handle_write_calendar_events()` - Creating new events
- `handle_edit_calendar_event()` - Updating existing events
- `handle_delete_calendar_event()` - Deleting events
- `upload_single_event()` - Uploading events via uploader

## Security Guarantees

### What We Guarantee

✅ **Read operations** can access all calendars (for duplicate detection)  
✅ **Write operations** are **only** allowed to the WBSO calendar  
✅ All write operations are validated before execution  
✅ Security violations are logged and blocked  
✅ Clear error messages when write operations are blocked  

### What We Cannot Guarantee (OAuth Limitation)

⚠️ The OAuth token has **technical capability** to write to all calendars  
⚠️ Google's OAuth consent screen will show the full scope warning  
⚠️ If the code is modified maliciously, it could bypass our validation  

### What This Means

**In practice:**
- The application **will only write** to the WBSO calendar
- Any attempt to write to another calendar is **blocked by code**
- Security violations are **logged** for audit purposes
- The OAuth scope warning is a **technical limitation**, not a practical risk

**For users:**
- You can safely grant the OAuth permission
- The app will only modify your WBSO calendar
- All write operations are validated and restricted
- Security violations are logged and prevented

## Code-Level Protections

### 1. Calendar ID Validation

All write operations validate the calendar ID:

```python
allowed_calendar_id = uploader.get_wbso_calendar_id()
is_valid, error_msg = validate_wbso_calendar_write(calendar_id, allowed_calendar_id)
if not is_valid:
    return {"error": error_msg}  # Operation blocked
```

### 2. Hardcoded WBSO Calendar

The uploader class only uses `self.wbso_calendar_id`:

```python
# Only writes to WBSO calendar
created_event = self.service.events().insert(
    calendarId=self.wbso_calendar_id,  # Hardcoded to WBSO calendar
    body=event_body
).execute()
```

### 3. Logging and Audit

All security violations are logged:

```python
logger.error(f"SECURITY: Write operation blocked: {error_msg}")
```

## Best Practices

### For Developers

1. **Always use validation** before write operations
2. **Never bypass** `validate_wbso_calendar_write()`
3. **Log security violations** for audit purposes
4. **Test security** by attempting to write to wrong calendar
5. **Document** any exceptions to the security model

### For Users

1. **Review the code** if you're concerned about security
2. **Check logs** for security violations
3. **Report** any unexpected calendar modifications
4. **Revoke access** if you no longer need the app

## Related Documentation

- [Token Refresh Guide](REFRESH_GOOGLE_CALENDAR_TOKEN.md) - OAuth authentication
- [MCP Calendar Integration](MCP_CALENDAR_INTEGRATION.md) - Integration overview
- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview) - Official API docs

## Security Contact

If you discover a security vulnerability or have concerns about the security implementation, please review the code and report any issues.

