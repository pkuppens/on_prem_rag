#!/usr/bin/env python3
"""
WBSO Pipeline Steps

Individual pipeline steps that can be composed into a complete pipeline.
Each step returns a step report for tracking and extensibility.

The data refresh step (step_data_refresh) includes separate subflows for system events
and git commits extraction, each with independent error handling and bottlenecks.
See docs/project/hours/DATA_REFRESH_GUIDE.md for manual refresh instructions and
automation details.

Author: AI Assistant
Created: 2025-11-28
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import subprocess
import sys

from zoneinfo import ZoneInfo

from .validation import WBSODataValidator
from .upload import GoogleCalendarUploader
from .calendar_event import WBSODataset, CalendarEvent, WBSOSession
from .logging_config import get_logger

# Amsterdam timezone (handles DST automatically)
AMSTERDAM_TZ = ZoneInfo("Europe/Amsterdam")

logger = get_logger("pipeline_steps")

# Default paths
SCRIPT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours"
DATA_DIR = SCRIPT_DIR / "data"
VALIDATION_OUTPUT_DIR = SCRIPT_DIR / "validation_output"
UPLOAD_OUTPUT_DIR = SCRIPT_DIR / "upload_output"
CREDENTIALS_PATH = SCRIPT_DIR / "scripts" / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "scripts" / "token.json"
CONFIG_PATH = SCRIPT_DIR / "config" / "wbso_calendar_config.json"
SCRIPTS_DIR = SCRIPT_DIR / "scripts"

# Target date range
TARGET_START_DATE = datetime(2025, 6, 1)
TARGET_END_DATE = datetime.now()


def create_step_report(step_name: str, success: bool, **kwargs) -> Dict[str, Any]:
    """Create a standardized step report."""
    return {"step_name": step_name, "success": success, "timestamp": datetime.now().isoformat(), **kwargs}


def _check_system_events_freshness() -> Optional[datetime.date]:
    """Check latest system events file date.

    Returns:
        Latest system events file date, or None if no files found
    """
    system_events_files = list(DATA_DIR.glob("system_events_*.csv"))
    if not system_events_files:
        return None

    dates = []
    for f in system_events_files:
        try:
            # Format: system_events_YYYYMMDD.csv
            date_str = f.stem.split("_")[-1]
            file_date = datetime.strptime(date_str, "%Y%m%d").date()
            dates.append(file_date)
        except (ValueError, IndexError):
            continue

    return max(dates) if dates else None


def _check_commits_freshness() -> Optional[datetime.date]:
    """Check latest git commits file modification date.

    Returns:
        Latest commits file modification date, or None if no files found
    """
    commits_dir = DATA_DIR / "commits"
    if not commits_dir.exists():
        return None

    commit_files = list(commits_dir.glob("*.csv"))
    if not commit_files:
        return None

    # Use file modification time as proxy for latest commit
    latest_mtime = max(f.stat().st_mtime for f in commit_files)
    return datetime.fromtimestamp(latest_mtime).date()


def _subflow_refresh_system_events(force: bool = False) -> Dict[str, Any]:
    """
    Subflow: Refresh System Events

    Executes PowerShell script to extract Windows system events.
    This subflow has its own bottleneck: requires Windows PowerShell and admin privileges.

    Args:
        force: If True, refresh even if data is up to date

    Returns:
        Subflow report with success status and details
    """
    logger.info("  [Subflow] System Events Refresh")

    # Check if refresh needed
    if not force:
        yesterday = datetime.now() - timedelta(days=1)
        latest = _check_system_events_freshness()
        if latest and latest >= yesterday.date():
            logger.info(f"  ✅ System events up to date (latest: {latest})")
            return {
                "success": True,
                "skipped": True,
                "latest": latest.isoformat() if latest else None,
                "message": "System events up to date",
            }

    # Execute PowerShell script
    script_path = SCRIPTS_DIR / "Extract-SystemEvents.ps1"
    if not script_path.exists():
        error_msg = f"System events script not found: {script_path}"
        logger.error(f"  ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "bottleneck": "Script file missing",
            "message": "System events script not found",
        }

    try:
        logger.info(f"  Executing: {script_path.name}")

        # Prepare output path in data directory
        today = datetime.now().strftime("%Y%m%d")
        output_file = DATA_DIR / f"system_events_{today}.csv"

        # Run PowerShell script with explicit output path
        # Use -ExecutionPolicy Bypass to avoid policy restrictions
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-OutputPath",
                str(output_file),
            ],
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            # Check if output file was created (already set above)
            if output_file.exists():
                latest = _check_system_events_freshness()
                logger.info(f"  ✅ System events refreshed (latest: {latest})")
                return {
                    "success": True,
                    "latest": latest.isoformat() if latest else None,
                    "output_file": str(output_file),
                    "message": "System events refreshed successfully",
                }
            else:
                logger.warning("  ⚠️ Script completed but output file not found")
                return {
                    "success": False,
                    "error": "Output file not created",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "message": "Script completed but no output file",
                }
        else:
            error_msg = f"PowerShell script failed with code {result.returncode}"
            logger.error(f"  ❌ {error_msg}")
            logger.error(f"  stderr: {result.stderr[:500]}")
            return {
                "success": False,
                "error": error_msg,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "bottleneck": "PowerShell execution failed",
                "message": "System events refresh failed",
            }

    except subprocess.TimeoutExpired:
        error_msg = "System events extraction timed out (>5 minutes)"
        logger.error(f"  ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "bottleneck": "Execution timeout",
            "message": "System events refresh timed out",
        }
    except Exception as e:
        error_msg = f"Exception during system events refresh: {str(e)}"
        logger.error(f"  ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "bottleneck": "Unexpected error",
            "message": "System events refresh failed",
        }


def _subflow_refresh_git_commits(force: bool = False) -> Dict[str, Any]:
    """
    Subflow: Refresh Git Commits

    Executes PowerShell script to extract git commits from all repositories.
    This subflow has its own bottleneck: requires Git installed and repositories cloned.

    Args:
        force: If True, refresh even if data is up to date

    Returns:
        Subflow report with success status and details
    """
    logger.info("  [Subflow] Git Commits Refresh")

    # Check if refresh needed
    if not force:
        yesterday = datetime.now() - timedelta(days=1)
        latest = _check_commits_freshness()
        if latest and latest >= yesterday.date():
            logger.info(f"  ✅ Git commits up to date (latest: {latest})")
            return {
                "success": True,
                "skipped": True,
                "latest": latest.isoformat() if latest else None,
                "message": "Git commits up to date",
            }

    # Execute PowerShell script
    script_path = SCRIPTS_DIR / "extract_git_commits.ps1"
    if not script_path.exists():
        error_msg = f"Git commits script not found: {script_path}"
        logger.error(f"  ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "bottleneck": "Script file missing",
            "message": "Git commits script not found",
        }

    try:
        logger.info(f"  Executing: {script_path.name}")

        # Run PowerShell script
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout (multiple repositories)
        )

        if result.returncode == 0:
            latest = _check_commits_freshness()
            commits_dir = DATA_DIR / "commits"
            commit_files = list(commits_dir.glob("*.csv")) if commits_dir.exists() else []

            logger.info(f"  ✅ Git commits refreshed (latest: {latest}, {len(commit_files)} files)")
            return {
                "success": True,
                "latest": latest.isoformat() if latest else None,
                "files_count": len(commit_files),
                "message": "Git commits refreshed successfully",
            }
        else:
            error_msg = f"PowerShell script failed with code {result.returncode}"
            logger.error(f"  ❌ {error_msg}")
            logger.error(f"  stderr: {result.stderr[:500]}")
            return {
                "success": False,
                "error": error_msg,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "bottleneck": "PowerShell execution failed",
                "message": "Git commits refresh failed",
            }

    except subprocess.TimeoutExpired:
        error_msg = "Git commits extraction timed out (>10 minutes)"
        logger.error(f"  ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "bottleneck": "Execution timeout",
            "message": "Git commits refresh timed out",
        }
    except Exception as e:
        error_msg = f"Exception during git commits refresh: {str(e)}"
        logger.error(f"  ❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "bottleneck": "Unexpected error",
            "message": "Git commits refresh failed",
        }


def step_data_refresh(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step: Data Refresh

    Refresh data sources (computer sessions, git commits).
    Determines if data is already up to date (present until yesterday).
    Executes separate subflows for each data source with independent error handling.
    """
    logger.info("=" * 60)
    logger.info("STEP: DATA REFRESH")
    logger.info("=" * 60)

    # Check if data is already up to date
    yesterday = datetime.now() - timedelta(days=1)
    force_refresh = context.get("force_refresh", False)

    system_events_latest = _check_system_events_freshness()
    commits_latest = _check_commits_freshness()

    # Determine if refresh is needed
    system_events_needed = force_refresh or not system_events_latest or system_events_latest < yesterday.date()
    commits_needed = force_refresh or not commits_latest or commits_latest < yesterday.date()

    if not system_events_needed and not commits_needed:
        logger.info("✅ Data is up to date (present until yesterday)")
        return create_step_report(
            "data_refresh",
            True,
            refresh_needed=False,
            system_events_latest=system_events_latest.isoformat() if system_events_latest else None,
            commits_latest=commits_latest.isoformat() if commits_latest else None,
            message="Data is up to date",
        )

    # Execute refresh subflows independently
    logger.info("Executing data refresh subflows...")

    system_events_result = None
    commits_result = None

    if system_events_needed:
        system_events_result = _subflow_refresh_system_events(force=force_refresh)
    else:
        logger.info("  [Subflow] System Events Refresh - Skipped (up to date)")
        system_events_result = {
            "success": True,
            "skipped": True,
            "latest": system_events_latest.isoformat() if system_events_latest else None,
        }

    if commits_needed:
        commits_result = _subflow_refresh_git_commits(force=force_refresh)
    else:
        logger.info("  [Subflow] Git Commits Refresh - Skipped (up to date)")
        commits_result = {
            "success": True,
            "skipped": True,
            "latest": commits_latest.isoformat() if commits_latest else None,
        }

    # Update latest dates after refresh
    system_events_latest = _check_system_events_freshness()
    commits_latest = _check_commits_freshness()

    # Determine overall success
    overall_success = (system_events_result.get("success", False) or system_events_result.get("skipped", False)) and (
        commits_result.get("success", False) or commits_result.get("skipped", False)
    )

    # Build report
    report = create_step_report(
        "data_refresh",
        overall_success,
        refresh_needed=True,
        system_events_latest=system_events_latest.isoformat() if system_events_latest else None,
        commits_latest=commits_latest.isoformat() if commits_latest else None,
        system_events_result=system_events_result,
        commits_result=commits_result,
        message="Data refresh completed",
    )

    if overall_success:
        logger.info("✅ Data refresh completed successfully")
    else:
        logger.warning("⚠️ Data refresh completed with some failures (check subflow results)")

    return report


def step_validate(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Validate data sources."""
    logger.info("=" * 60)
    logger.info("STEP: VALIDATION")
    logger.info("=" * 60)

    force_validation = context.get("force_validation", False)
    cleaned_dataset_path = VALIDATION_OUTPUT_DIR / "cleaned_dataset.json"
    dataset = WBSODataset()

    # Check if validation is needed
    if not force_validation and cleaned_dataset_path.exists():
        logger.info(f"Using existing validated dataset: {cleaned_dataset_path}")
        try:
            dataset.load_from_json(cleaned_dataset_path)
            logger.info(f"Loaded {len(dataset.sessions)} sessions from validated dataset")
            context["dataset"] = dataset
            return create_step_report(
                "validate",
                True,
                total_sessions=len(dataset.sessions),
                from_cache=True,
                message="Loaded from existing validated dataset",
            )
        except Exception as e:
            logger.warning(f"Failed to load existing validated dataset: {e}")
            logger.info("Running validation...")

    # Run validation
    logger.info("Running comprehensive validation...")
    validator = WBSODataValidator(DATA_DIR)
    validation_results = validator.run_comprehensive_validation()

    # Check validation results
    summary = validation_results.get("summary", {})
    if not summary.get("ready_for_upload", False):
        errors = summary.get("total_errors", 0)
        warnings = summary.get("total_warnings", 0)
        logger.error(f"Validation failed: {errors} errors, {warnings} warnings")
        if errors > 0:
            logger.error("Cannot proceed with upload due to validation errors")
            return create_step_report("validate", False, errors=errors, warnings=warnings, message="Validation failed with errors")
        logger.warning("Validation has warnings but proceeding...")

    # Export validation reports
    validator.export_validation_reports(VALIDATION_OUTPUT_DIR)
    dataset = validator.dataset
    context["dataset"] = dataset
    context["validator"] = validator
    context["validation_results"] = validation_results

    logger.info(f"✅ Validation complete: {len(dataset.sessions)} sessions validated")
    return create_step_report(
        "validate",
        True,
        total_sessions=len(dataset.sessions),
        errors=summary.get("total_errors", 0),
        warnings=summary.get("total_warnings", 0),
        from_cache=False,
        message="Validation completed successfully",
    )


def step_time_polish(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Polish times (round to 5-minute intervals, add breaks)."""
    logger.info("=" * 60)
    logger.info("STEP: TIME POLISHING")
    logger.info("=" * 60)

    from .time_utils import round_to_quarter_hour, generate_lunch_break, generate_dinner_break, calculate_work_hours_with_breaks

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("time_polish", False, message="No dataset available")

    polished_count = 0
    break_added_count = 0

    for session in dataset.sessions:
        if not session.start_time or not session.end_time:
            continue

        # Round times
        original_start = session.start_time
        original_end = session.end_time
        session.start_time = round_to_quarter_hour(session.start_time)
        session.end_time = round_to_quarter_hour(session.end_time)

        if original_start != session.start_time or original_end != session.end_time:
            polished_count += 1

        # Add breaks to full_day sessions
        if session.session_type == "full_day":
            breaks = []

            # Add lunch break
            lunch_break = generate_lunch_break(session.start_time, session.session_id)
            breaks.append(lunch_break)

            # Add dinner break if session extends into evening
            if session.end_time.hour >= 17:
                dinner_break = generate_dinner_break(session.start_time, session.session_id)
                breaks.append(dinner_break)

            # Recalculate work_hours excluding breaks
            if breaks:
                session.work_hours = calculate_work_hours_with_breaks(session.start_time, session.end_time, breaks)
                break_added_count += 1
                # Store breaks in session metadata if available
                if hasattr(session, "breaks"):
                    session.breaks = breaks

    logger.info(f"✅ Time polishing complete: {polished_count} sessions rounded, {break_added_count} sessions with breaks")
    return create_step_report(
        "time_polish", True, polished_count=polished_count, break_added_count=break_added_count, message="Time polishing completed"
    )


def step_deduplicate(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Remove duplicate sessions."""
    logger.info("=" * 60)
    logger.info("STEP: DEDUPLICATION")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("deduplicate", False, message="No dataset available")

    # Find duplicates
    duplicates = dataset.find_duplicates()
    duplicate_session_ids = duplicates.get("session_ids", {})
    duplicate_datetime_ranges = duplicates.get("datetime_ranges", {})

    # Remove duplicates (keep first occurrence)
    removed_count = 0
    sessions_to_remove = set()

    # Remove by session_id
    for session_id, session_list in duplicate_session_ids.items():
        if len(session_list) > 1:
            # Keep first, mark others for removal
            for session_id_to_remove in session_list[1:]:
                sessions_to_remove.add(session_id_to_remove)

    # Remove by datetime range
    for dt_key, session_list in duplicate_datetime_ranges.items():
        if len(session_list) > 1:
            # Keep first, mark others for removal
            for session_id_to_remove in session_list[1:]:
                sessions_to_remove.add(session_id_to_remove)

    # Remove duplicate sessions
    original_count = len(dataset.sessions)
    dataset.sessions = [s for s in dataset.sessions if s.session_id not in sessions_to_remove]
    removed_count = original_count - len(dataset.sessions)

    logger.info(f"✅ Deduplication complete: {removed_count} duplicate sessions removed")
    return create_step_report(
        "deduplicate",
        True,
        removed_count=removed_count,
        duplicate_session_ids=len(duplicate_session_ids),
        duplicate_datetime_ranges=len(duplicate_datetime_ranges),
        message=f"Removed {removed_count} duplicate sessions",
    )


def _normalize_datetime(dt: datetime) -> datetime:
    """
    Normalize datetime to timezone-aware (Europe/Amsterdam) if it's timezone-naive.

    Args:
        dt: Datetime object (may be timezone-naive or timezone-aware)

    Returns:
        Timezone-aware datetime (Europe/Amsterdam with DST support)
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in Amsterdam timezone (with DST)
        return dt.replace(tzinfo=AMSTERDAM_TZ)
    return dt


def step_conflict_detect(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Detect conflicts with existing calendar events."""
    logger.info("=" * 60)
    logger.info("STEP: CONFLICT DETECTION")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("conflict_detect", False, message="No dataset available")

    # Initialize uploader for calendar access
    uploader = GoogleCalendarUploader(CREDENTIALS_PATH, TOKEN_PATH, CONFIG_PATH)
    if not uploader.authenticate():
        logger.warning("Cannot authenticate - skipping conflict detection")
        return create_step_report("conflict_detect", False, message="Authentication failed")

    calendar_id = uploader.get_wbso_calendar_id()
    if not calendar_id:
        logger.warning("WBSO calendar not found - skipping conflict detection")
        return create_step_report("conflict_detect", False, message="Calendar not found")

    # Get existing events
    existing_events_data = uploader.get_existing_events(TARGET_START_DATE, TARGET_END_DATE + timedelta(days=1))
    existing_events = existing_events_data.get("events", [])

    # Detect conflicts
    conflicts = []
    for session in dataset.sessions:
        if not session.is_wbso or not session.start_time or not session.end_time:
            continue

        # Normalize session times to timezone-aware for comparison
        session_start = _normalize_datetime(session.start_time)
        session_end = _normalize_datetime(session.end_time)

        for event in existing_events:
            event_start_str = event.get("start", {}).get("dateTime")
            event_end_str = event.get("end", {}).get("dateTime")

            if not event_start_str or not event_end_str:
                continue

            try:
                event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00"))
                event_end = datetime.fromisoformat(event_end_str.replace("Z", "+00:00"))

                # Check for overlap (both datetimes are now timezone-aware)
                if session_start < event_end and session_end > event_start:
                    overlap_start = max(session_start, event_start)
                    overlap_end = min(session_end, event_end)
                    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0

                    conflicts.append(
                        {
                            "session_id": session.session_id,
                            "event_id": event.get("id"),
                            "event_summary": event.get("summary"),
                            "overlap_hours": overlap_hours,
                            "conflict_type": "short" if overlap_hours < 2.0 else "long",
                        }
                    )
            except (ValueError, AttributeError):
                continue

    context["uploader"] = uploader
    context["existing_events"] = existing_events_data
    context["conflicts"] = conflicts

    short_conflicts = [c for c in conflicts if c["conflict_type"] == "short"]
    long_conflicts = [c for c in conflicts if c["conflict_type"] == "long"]

    logger.info(f"✅ Conflict detection complete: {len(short_conflicts)} short, {len(long_conflicts)} long conflicts")
    return create_step_report(
        "conflict_detect",
        True,
        total_conflicts=len(conflicts),
        short_conflicts=len(short_conflicts),
        long_conflicts=len(long_conflicts),
        message=f"Detected {len(conflicts)} conflicts",
    )


def step_content_polish(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Polish event content (names, descriptions, locations)."""
    logger.info("=" * 60)
    logger.info("STEP: CONTENT POLISHING")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("content_polish", False, message="No dataset available")

    # Content polishing is done during CalendarEvent.from_wbso_session()
    # This step is a placeholder for future content enhancements
    # (e.g., linking to WBSO acceptable activities by title or tag)

    polished_count = len([s for s in dataset.sessions if s.is_wbso])

    logger.info(f"✅ Content polishing complete: {polished_count} sessions ready for calendar")
    return create_step_report("content_polish", True, polished_count=polished_count, message="Content polishing completed")


def step_event_convert(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Convert sessions to calendar events."""
    logger.info("=" * 60)
    logger.info("STEP: EVENT CONVERSION")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("event_convert", False, message="No dataset available")

    # Filter for WBSO sessions in target date range
    wbso_sessions = []
    for session in dataset.sessions:
        if not session.is_wbso:
            continue

        # Filter by date range
        if session.start_time:
            if session.start_time.date() < TARGET_START_DATE.date():
                continue
            if session.start_time.date() > TARGET_END_DATE.date():
                continue

        wbso_sessions.append(session)

    logger.info(f"Found {len(wbso_sessions)} WBSO sessions in date range {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}")

    # Convert to calendar events
    calendar_events = []
    conversion_errors = []

    for session in wbso_sessions:
        try:
            event = CalendarEvent.from_wbso_session(session)
            calendar_events.append(event)
        except Exception as e:
            error_msg = f"Failed to convert session {session.session_id}: {e}"
            logger.error(error_msg)
            conversion_errors.append({"session_id": session.session_id, "error": str(e)})

    context["calendar_events"] = calendar_events

    logger.info(f"✅ Conversion complete: {len(calendar_events)} events created, {len(conversion_errors)} errors")

    if conversion_errors:
        logger.warning(f"Conversion errors: {len(conversion_errors)} sessions failed")
        for error in conversion_errors[:5]:  # Show first 5
            logger.warning(f"  - {error['session_id']}: {error['error']}")

    return create_step_report(
        "event_convert",
        True,
        events_created=len(calendar_events),
        conversion_errors=len(conversion_errors),
        message=f"Converted {len(calendar_events)} sessions to calendar events",
    )


def step_calendar_replace(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Replace calendar events (delete old, upload new)."""
    logger.info("=" * 60)
    logger.info("STEP: CALENDAR REPLACEMENT")
    logger.info("=" * 60)

    dry_run = context.get("dry_run", False)
    calendar_events = context.get("calendar_events", [])
    uploader = context.get("uploader")

    if not calendar_events:
        return create_step_report("calendar_replace", False, message="No calendar events to upload")

    if not uploader:
        uploader = GoogleCalendarUploader(CREDENTIALS_PATH, TOKEN_PATH, CONFIG_PATH)
        if not uploader.authenticate():
            return create_step_report("calendar_replace", False, message="Authentication failed")
        if not uploader.get_wbso_calendar_id():
            return create_step_report("calendar_replace", False, message="WBSO calendar not found")
        context["uploader"] = uploader

    # Delete existing events in date range
    logger.info(f"Deleting existing events from {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}...")
    existing_events_data = uploader.get_existing_events(TARGET_START_DATE, TARGET_END_DATE + timedelta(days=1))
    existing_events = existing_events_data.get("events", [])

    deleted_count = 0
    if not dry_run:
        for event in existing_events:
            try:
                uploader.service.events().delete(calendarId=uploader.wbso_calendar_id, eventId=event["id"]).execute()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete event {event.get('id')}: {e}")
    else:
        deleted_count = len(existing_events)
        logger.info(f"DRY RUN - Would delete {deleted_count} existing events")

    logger.info(f"Deleted {deleted_count} existing events")

    # Upload new events
    logger.info(f"Uploading {len(calendar_events)} events to WBSO calendar...")
    upload_results = uploader.upload_events(calendar_events, dry_run=dry_run)

    if dry_run:
        logger.info("DRY RUN - No events were actually uploaded")
        plan = upload_results.get("upload_plan", {})
        logger.info(f"Would upload: {len(plan.get('new_events', []))} new events")
        return create_step_report(
            "calendar_replace",
            True,
            deleted_count=deleted_count,
            would_upload=len(plan.get("new_events", [])),
            dry_run=True,
            message="Dry run completed",
        )

    # Check upload success
    success = upload_results.get("success", False)
    upload_results_list = upload_results.get("upload_results", [])
    successful_uploads = [r for r in upload_results_list if r.get("status") == "success"]
    failed_uploads = [r for r in upload_results_list if r.get("status") != "success"]

    context["upload_results"] = upload_results

    if success:
        logger.info(f"✅ Upload complete: {len(successful_uploads)} successful, {len(failed_uploads)} failed")
    else:
        logger.error("❌ Upload failed")
        errors = upload_results.get("errors", [])
        for error in errors[:5]:  # Show first 5 errors
            logger.error(f"  - {error.get('event_summary', 'Unknown')}: {error.get('error_message', 'Unknown error')}")

    return create_step_report(
        "calendar_replace",
        success,
        deleted_count=deleted_count,
        uploaded_count=len(successful_uploads),
        failed_count=len(failed_uploads),
        message=f"Replaced {deleted_count} events, uploaded {len(successful_uploads)} new events",
    )


def step_verify(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Verify events were actually created in calendar."""
    logger.info("=" * 60)
    logger.info("STEP: VERIFICATION")
    logger.info("=" * 60)

    dry_run = context.get("dry_run", False)
    uploader = context.get("uploader")

    if dry_run:
        logger.info("DRY RUN - Skipping verification")
        return create_step_report("verify", True, dry_run=True, message="Dry run - verification skipped")

    if not uploader:
        return create_step_report("verify", False, message="Uploader not initialized")

    calendar_id = uploader.get_wbso_calendar_id()
    if not calendar_id:
        return create_step_report("verify", False, message="Calendar not found")

    # Query calendar for events in date range
    logger.info(f"Querying calendar for events from {TARGET_START_DATE.date()} to {TARGET_END_DATE.date()}...")
    existing_events_data = uploader.get_existing_events(TARGET_START_DATE, TARGET_END_DATE + timedelta(days=1))
    events = existing_events_data.get("events", [])

    # Calculate hours from calendar events
    total_hours = 0.0
    verified_events = []

    for event in events:
        start_str = event.get("start", {}).get("dateTime")
        end_str = event.get("end", {}).get("dateTime")

        if not start_str or not end_str:
            continue

        try:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

            # Filter by date range
            if start_dt.date() < TARGET_START_DATE.date() or start_dt.date() > TARGET_END_DATE.date():
                continue

            duration = end_dt - start_dt
            hours = duration.total_seconds() / 3600.0
            total_hours += hours

            verified_events.append(
                {
                    "event_id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": start_str,
                    "end": end_str,
                    "hours": hours,
                }
            )
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing event times: {e}")
            continue

    verification_results = {
        "verified": True,
        "calendar_id": calendar_id,
        "total_events": len(verified_events),
        "total_hours": total_hours,
        "date_range": {
            "start": TARGET_START_DATE.isoformat(),
            "end": TARGET_END_DATE.isoformat(),
        },
    }

    context["verification_results"] = verification_results

    logger.info(f"✅ Verification complete: {len(verified_events)} events, {total_hours:.2f} hours in calendar")
    return create_step_report(
        "verify",
        True,
        total_events=len(verified_events),
        total_hours=total_hours,
        message=f"Verified {len(verified_events)} events with {total_hours:.2f} hours",
    )


def step_report(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Generate summary report."""
    logger.info("=" * 60)
    logger.info("STEP: REPORTING")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    verification_results = context.get("verification_results", {})

    # Calculate totals
    wbso_sessions = [s for s in dataset.sessions if s.is_wbso] if dataset else []
    calculated_hours = sum(
        s.work_hours
        for s in wbso_sessions
        if s.start_time and TARGET_START_DATE.date() <= s.start_time.date() <= TARGET_END_DATE.date()
    )
    calendar_hours = verification_results.get("total_hours", 0.0)

    report_data = {
        "calculated_hours": calculated_hours,
        "calendar_hours": calendar_hours,
        "gap": calculated_hours - calendar_hours,
        "target_hours": 510.0,
        "target_gap": 510.0 - calendar_hours,
        "target_achievement_percent": (calendar_hours / 510.0 * 100) if 510.0 > 0 else 0,
    }

    context["report_data"] = report_data

    logger.info(f"✅ Report generated: {calendar_hours:.2f} hours in calendar, {calculated_hours:.2f} calculated")
    return create_step_report("report", True, **report_data, message="Report generated successfully")
