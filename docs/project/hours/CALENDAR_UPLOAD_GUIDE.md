# Calendar Upload Guide

This guide explains how to run the calendar upload step separately, troubleshoot API issues, and check upload results.

## Overview

The WBSO calendar upload process consists of:
1. **Data Preparation**: Pipeline steps that prepare calendar events from system events and commits
2. **Calendar Upload**: Replacing existing calendar events with new ones

If the full pipeline fails during calendar upload (e.g., due to API rate limiting), you can run the upload step separately after the data is prepared.

## Running Calendar Upload Separately

### Prerequisites

The data must be prepared first. The calendar events are prepared by running the pipeline up to `step_google_calendar_data_preparation`. This step:
- Converts sessions to calendar events
- Applies time corrections
- Filters invalid events
- Saves calendar events to CSV: `docs/project/hours/data/calendar_events.csv`

### Method 1: Run Upload Step Directly

```bash
# Run the standalone calendar upload script
uv run python scripts/run_calendar_upload.py --start-date 2025-06-01 --end-date 2025-12-02

# Dry run (test without uploading)
uv run python scripts/run_calendar_upload.py --start-date 2025-06-01 --end-date 2025-12-02 --dry-run
```

The script will:
1. Run pipeline steps up to data preparation (if needed)
2. Load prepared calendar events
3. Filter events by date range
4. Delete existing events in the date range
5. Upload new events
6. Report results and any errors

### Method 2: Run Full Pipeline (Recommended First Time)

```bash
# Run full pipeline (will prepare data and upload)
uv run python -m src.wbso.pipeline --start-date 2025-06-01 --end-date 2025-12-02
```

If the upload step fails, the data is already prepared, so you can use Method 1 to retry just the upload.

## API Rate Limiting

### Current Rate Limiting Settings

The upload code uses:
- **Rate Limit Delay**: 0.1 seconds (10 requests per second)
- **Max Retries**: 3 attempts per event
- **Exponential Backoff**: For 429 (rate limit) errors, waits 2^attempt seconds

### Google Calendar API Quotas

- **Daily Quota**: 1,000,000 requests per day
- **Per-Minute Quota**: Varies by operation type
- **Per-User Quota**: 1,000 requests per 100 seconds per user

### Adjusting Rate Limiting

If you encounter rate limiting errors (HTTP 429), you can increase the delay:

Edit `src/wbso/upload.py`:
```python
RATE_LIMIT_DELAY = 0.2  # Increase from 0.1 to 0.2 (5 requests per second)
```

Or for very large uploads:
```python
RATE_LIMIT_DELAY = 0.5  # 2 requests per second
```

## Checking Upload Results

### 1. Check Pipeline Report

After running the pipeline or upload script, check the report:
```
docs/project/hours/upload_output/pipeline_report.json
```

Look for:
- `steps[].step_name == "calendar_replace"` - Upload step results
- `steps[].uploaded_count` - Number of successfully uploaded events
- `steps[].failed_count` - Number of failed uploads
- `steps[].errors` - List of upload errors

### 2. Check Logs

The upload process logs detailed information:
- ✅ Successful uploads: `✅ Uploaded event: [summary] (ID: [event_id])`
- ❌ Failed uploads: `❌ Error uploading event: [summary] - [error]`
- ⏳ Rate limiting: `⏳ Rate limit exceeded, waiting [time]s before retry`

### 3. Check Calendar Events CSV

The prepared events are saved to:
```
docs/project/hours/data/calendar_events.csv
```

This file contains all events ready for upload with:
- Session ID
- Summary (activity name)
- Start/end datetime
- Hours
- ISO week number

### 4. Verify in Google Calendar

After upload, verify events in Google Calendar:
1. Open Google Calendar
2. Find "WBSO Activities 2025" calendar
3. Check date range: 2025-06-01 to 2025-12-02
4. Verify event count matches expected

## Troubleshooting

### Issue: Authentication Failed

**Symptoms**: `Authentication failed` error

**Solution**:
1. Check credentials file: `docs/project/hours/scripts/credentials.json`
2. Check token file: `docs/project/hours/scripts/token.json`
3. If token expired, see: `docs/project/hours/REFRESH_GOOGLE_CALENDAR_TOKEN.md`

### Issue: Rate Limiting (HTTP 429)

**Symptoms**: `Rate limit exceeded` warnings, upload failures

**Solution**:
1. Increase `RATE_LIMIT_DELAY` in `src/wbso/upload.py`
2. Wait a few minutes and retry
3. For large uploads, consider splitting into smaller date ranges

### Issue: Permission Denied (HTTP 403)

**Symptoms**: `Permission denied` errors

**Solution**:
1. Verify calendar access: Check you have "owner" or "writer" role
2. Verify calendar ID: Check `WBSO_CALENDAR_NAME` matches your calendar
3. Check OAuth scopes: Must include `https://www.googleapis.com/auth/calendar`

### Issue: Events Not Uploaded

**Symptoms**: Upload reports success but events missing in calendar

**Solution**:
1. Check date range: Events must be within `--start-date` to `--end-date`
2. Check dry-run mode: Ensure `--dry-run` is not set
3. Check upload results: Look for `failed_count > 0` in report
4. Check calendar ID: Verify correct calendar is being used

### Issue: Duplicate Events

**Symptoms**: Events appear multiple times in calendar

**Solution**:
1. The upload process includes duplicate detection
2. Events with same `session_id` or same datetime range are skipped
3. Check upload plan: `upload_plan.skip_events` shows skipped duplicates

## Data Files

### Calendar Events CSV
- **Location**: `docs/project/hours/data/calendar_events.csv`
- **Format**: CSV with session_id, summary, start_datetime, end_datetime, hours, etc.
- **Purpose**: Prepared events ready for upload (version-controlled)

### Pipeline Report
- **Location**: `docs/project/hours/upload_output/pipeline_report.json`
- **Format**: JSON with step-by-step results
- **Purpose**: Complete pipeline execution report

### Upload Log
- **Location**: Console output and log files
- **Format**: Structured logging
- **Purpose**: Real-time upload progress and errors

## Best Practices

1. **Always run dry-run first**: Test upload without actually modifying calendar
2. **Check data preparation**: Verify `calendar_events.csv` exists and has correct data
3. **Monitor rate limiting**: Watch for 429 errors and adjust delay if needed
4. **Verify results**: Check both pipeline report and Google Calendar
5. **Keep backups**: Calendar events CSV is version-controlled for recovery

## Related Documentation

- `DATA_REFRESH_GUIDE.md` - Data extraction and refresh
- `REFRESH_GOOGLE_CALENDAR_TOKEN.md` - OAuth token refresh
- Pipeline code: `src/wbso/pipeline.py`
- Upload code: `src/wbso/upload.py`
- Pipeline steps: `src/wbso/pipeline_steps.py`
