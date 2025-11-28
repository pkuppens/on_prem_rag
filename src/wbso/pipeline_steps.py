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
import csv

from zoneinfo import ZoneInfo

from .validation import WBSODataValidator
from .upload import GoogleCalendarUploader
from .calendar_event import WBSODataset, CalendarEvent, WBSOSession
from .logging_config import get_logger
from .time_utils import parse_datetime_flexible

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


def step_consolidate_system_events(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step: Consolidate System Events

    Consolidates all system_events_*.csv files into all_system_events.csv.
    This is a one-off step that skips if the output file exists unless force_regenerate is True.

    Features:
    - Supports timezone offsets (+0100, +0200, +02:00)
    - Returns timezone-aware datetime objects (Amsterdam timezone)
    - Deduplicates by RecordId
    - One-off processing (skips if file exists)
    """
    logger.info("=" * 60)
    logger.info("STEP: CONSOLIDATE SYSTEM EVENTS")
    logger.info("=" * 60)

    output_csv = DATA_DIR / "all_system_events.csv"
    output_json = DATA_DIR / "all_system_events.json"
    force_regenerate = context.get("force_regenerate_system_events", False)
    force_refresh = context.get("force_refresh", False)

    # If force_refresh is True, also regenerate the consolidated file
    if force_refresh:
        force_regenerate = True
        logger.info("Force refresh enabled - will regenerate consolidated file")

    # Check if output file exists and skip if not forcing regeneration
    if output_csv.exists() and not force_regenerate:
        logger.info(f"✅ Output file {output_csv.name} already exists. Skipping consolidation.")
        logger.info("Use --force-regenerate-system-events or --force-refresh to regenerate the file.")
        return create_step_report(
            "consolidate_system_events",
            True,
            skipped=True,
            output_file=str(output_csv),
            message="Consolidation skipped - file already exists",
        )

    # Import the consolidation script function
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from collect_system_events import collect_and_deduplicate_system_events

        logger.info(f"Consolidating system events from {DATA_DIR}...")
        collect_and_deduplicate_system_events(DATA_DIR, output_csv, force_regenerate=True)

        # Check if file was created
        if output_csv.exists():
            logger.info(f"✅ System events consolidated: {output_csv}")
            return create_step_report(
                "consolidate_system_events",
                True,
                output_file=str(output_csv),
                message="System events consolidated successfully",
            )
        else:
            logger.error(f"❌ Consolidation failed - output file not created")
            return create_step_report(
                "consolidate_system_events",
                False,
                error="Output file not created",
                message="Consolidation failed",
            )
    except ImportError as e:
        logger.error(f"❌ Could not import consolidation script: {e}")
        return create_step_report(
            "consolidate_system_events",
            False,
            error=str(e),
            message="Consolidation failed - import error",
        )
    except Exception as e:
        logger.error(f"❌ Consolidation failed: {e}")
        return create_step_report(
            "consolidate_system_events",
            False,
            error=str(e),
            message="Consolidation failed",
        )


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

    logger.info(f"Force refresh flag: {force_refresh}")

    system_events_latest = _check_system_events_freshness()
    commits_latest = _check_commits_freshness()

    # Determine if refresh is needed
    # If force_refresh is True, always refresh regardless of freshness
    system_events_needed = force_refresh or not system_events_latest or system_events_latest < yesterday.date()
    commits_needed = force_refresh or not commits_latest or commits_latest < yesterday.date()

    logger.info(f"System events refresh needed: {system_events_needed} (latest: {system_events_latest}, force: {force_refresh})")
    logger.info(f"Git commits refresh needed: {commits_needed} (latest: {commits_latest}, force: {force_refresh})")

    # Only skip if NOT forcing refresh AND data is up to date
    if not force_refresh and not system_events_needed and not commits_needed:
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


def step_data_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Summarize data collection date ranges for all data sources."""
    logger.info("=" * 60)
    logger.info("STEP: DATA COLLECTION SUMMARY")
    logger.info("=" * 60)

    summary = {
        "system_events": {},
        "git_commits": {},
        "calendar_events": {},
    }

    # System events date range - check consolidated file first, then individual files
    consolidated_file = DATA_DIR / "all_system_events.csv"
    if consolidated_file.exists():
        try:
            with open(consolidated_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                dates = []
                event_count = 0
                parse_errors = 0
                for row in reader:
                    event_count += 1
                    # Try different column name variations
                    dt_str = row.get("DateTime") or row.get("datetime") or row.get("Date") or row.get("date")
                    if dt_str:
                        try:
                            # Parse various datetime formats (2025-04-27 17:22:26, 2025/04/27 17:22:26, etc.)
                            dt = parse_datetime_flexible(dt_str.strip())
                            if dt:
                                dates.append(dt.date())
                            else:
                                parse_errors += 1
                        except Exception as parse_error:
                            parse_errors += 1
                            if event_count <= 5:  # Log first few errors for debugging
                                logger.debug(f"Error parsing datetime '{dt_str}': {parse_error}")

                logger.info(
                    f"Read {event_count} events from consolidated file, {len(dates)} with valid dates, {parse_errors} parse errors"
                )

            if dates:
                system_events_files = list(DATA_DIR.glob("system_events_*.csv"))
                earliest = min(dates)
                latest = max(dates)
                summary["system_events"] = {
                    "file_count": len(system_events_files),
                    "earliest_date": earliest.isoformat(),
                    "latest_date": latest.isoformat(),
                    "date_range_days": (latest - earliest).days + 1,
                    "total_events": event_count,
                    "valid_dates": len(dates),
                    "source": "consolidated_file",
                }
                logger.info(
                    f"System events date range: {earliest.isoformat()} to {latest.isoformat()} ({len(dates)} valid dates, {event_count} total events)"
                )
            else:
                logger.warning(
                    f"Consolidated file exists but no valid dates found ({event_count} events, {parse_errors} parse errors)"
                )
        except Exception as e:
            logger.warning(f"Error reading consolidated system events file: {e}")
            import traceback

            logger.debug(traceback.format_exc())

    # Fallback to individual files if consolidated file not available
    if not summary["system_events"]:
        system_events_files = list(DATA_DIR.glob("system_events_*.csv"))
        if system_events_files:
            dates = []
            for f in system_events_files:
                try:
                    date_str = f.stem.split("_")[-1]
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    dates.append(file_date)
                except (ValueError, IndexError):
                    continue

            if dates:
                summary["system_events"] = {
                    "file_count": len(system_events_files),
                    "earliest_date": min(dates).isoformat(),
                    "latest_date": max(dates).isoformat(),
                    "date_range_days": (max(dates) - min(dates)).days + 1,
                    "source": "individual_files",
                }

    # Git commits date range
    commits_dir = DATA_DIR / "commits"
    if commits_dir.exists():
        commit_files = list(commits_dir.glob("*.csv"))
        if commit_files:
            commit_dates = []
            for commit_file in commit_files:
                try:
                    with open(commit_file, "r", encoding="utf-8") as f:
                        # Try pipe delimiter first, then comma
                        try:
                            reader = csv.DictReader(f, delimiter="|")
                        except:
                            f.seek(0)
                            reader = csv.DictReader(f, delimiter=",")

                        for row in reader:
                            dt_str = row.get("datetime") or row.get("timestamp")
                            if dt_str:
                                try:
                                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                                    commit_dates.append(dt.date())
                                except:
                                    pass
                except Exception as e:
                    logger.warning(f"Error reading commit file {commit_file}: {e}")
                    continue

            if commit_dates:
                summary["git_commits"] = {
                    "repo_count": len(commit_files),
                    "total_commits": len(commit_dates),
                    "earliest_date": min(commit_dates).isoformat(),
                    "latest_date": max(commit_dates).isoformat(),
                    "date_range_days": (max(commit_dates) - min(commit_dates)).days + 1,
                }

    # Calendar events (if available)
    uploader = context.get("uploader")
    if uploader:
        try:
            existing_events_data = uploader.get_existing_events(TARGET_START_DATE, TARGET_END_DATE + timedelta(days=1))
            existing_events = existing_events_data.get("events", [])
            if existing_events:
                event_dates = []
                for event in existing_events:
                    start_str = event.get("start", {}).get("dateTime")
                    if start_str:
                        try:
                            dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            event_dates.append(dt.date())
                        except:
                            pass

                if event_dates:
                    summary["calendar_events"] = {
                        "total_events": len(existing_events),
                        "earliest_date": min(event_dates).isoformat(),
                        "latest_date": max(event_dates).isoformat(),
                        "date_range_days": (max(event_dates) - min(event_dates)).days + 1,
                    }
        except Exception as e:
            logger.warning(f"Could not retrieve calendar events: {e}")

    # Log summary
    logger.info("Data Collection Summary:")
    if summary["system_events"]:
        se = summary["system_events"]
        logger.info(
            f"  System Events: {se['file_count']} files, {se['earliest_date']} to {se['latest_date']} ({se['date_range_days']} days)"
        )
    else:
        logger.info("  System Events: No data found")

    if summary["git_commits"]:
        gc = summary["git_commits"]
        logger.info(
            f"  Git Commits: {gc['repo_count']} repos, {gc['total_commits']} commits, {gc['earliest_date']} to {gc['latest_date']} ({gc['date_range_days']} days)"
        )
    else:
        logger.info("  Git Commits: No data found")

    if summary["calendar_events"]:
        ce = summary["calendar_events"]
        logger.info(
            f"  Calendar Events: {ce['total_events']} events, {ce['earliest_date']} to {ce['latest_date']} ({ce['date_range_days']} days)"
        )
    else:
        logger.info("  Calendar Events: No data found")

    context["data_summary"] = summary

    return create_step_report(
        "data_summary",
        True,
        summary=summary,
        message="Data collection summary generated",
    )


def step_filter_logon_logoff(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step: Filter logon/logoff events (7001/7002) and create sessions.

    Filters system events to only EventId 7001 (logon) and 7002 (logoff),
    sorts by datetime ascending, and creates sessions from logon-logoff pairs.
    Handles reboots (logoff-logon within 5 minutes - combine sessions).
    Handles day boundaries (end at 23:59, start new at 00:00 next day).

    Output: all_logon_logoff.csv with columns: DateTime, EventId, EventType, RecordId
    """
    logger.info("=" * 60)
    logger.info("STEP: FILTER LOGON/LOGOFF EVENTS")
    logger.info("=" * 60)

    input_file = DATA_DIR / "all_system_events.csv"
    output_file = DATA_DIR / "all_logon_logoff.csv"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return create_step_report("filter_logon_logoff", False, message="Input file not found")

    # Load and filter events
    logon_logoff_events = []
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                event_id = row.get("EventId", "").strip()
                if event_id in ["7001", "7002"]:
                    # Get datetime value (handle BOM and column name variations)
                    datetime_value = ""
                    for key, value in row.items():
                        if "datetime" in key.lower():
                            datetime_value = value
                            break

                    logon_logoff_events.append(
                        {
                            "DateTime": datetime_value,
                            "EventId": event_id,
                            "EventType": row.get("EventType", ""),
                            "RecordId": row.get("RecordId", ""),
                        }
                    )

        logger.info(f"Found {len(logon_logoff_events)} logon/logoff events")

        # Sort by datetime ascending
        events_with_dt = []
        for event in logon_logoff_events:
            dt = parse_datetime_flexible(event["DateTime"])
            if dt:
                events_with_dt.append((dt, event))

        events_with_dt.sort(key=lambda x: x[0])
        logger.info(f"Sorted {len(events_with_dt)} events by datetime")

        # Create sessions from logon-logoff pairs
        sessions = []
        session_counter = 1
        i = 0

        while i < len(events_with_dt):
            start_dt, start_event = events_with_dt[i]

            # Look for logon event (7001)
            if start_event["EventId"] == "7001":
                session_start = start_dt
                session_date = session_start.date()

                # Look for matching logoff event (7002)
                j = i + 1
                logoff_found = False

                while j < len(events_with_dt):
                    end_dt, end_event = events_with_dt[j]

                    # Check for reboot: logoff-logon within 5 minutes
                    if end_event["EventId"] == "7002":
                        # Check if next event is logon within 5 minutes
                        if j + 1 < len(events_with_dt):
                            next_dt, next_event = events_with_dt[j + 1]
                            if next_event["EventId"] == "7001":
                                time_gap = (next_dt - end_dt).total_seconds() / 60.0
                                if time_gap <= 5.0:
                                    # Reboot detected - skip this logoff and continue to next logoff after the reboot logon
                                    logger.debug(
                                        f"Reboot detected: logoff at {end_dt}, logon at {next_dt} (gap: {time_gap:.1f} min) - combining sessions"
                                    )
                                    j += 2
                                    continue

                        # Found logoff - check day boundary
                        session_end = end_dt
                        end_date = session_end.date()

                        # Handle day boundary: if session crosses midnight, end at 23:59:59 and start new at 00:00:00
                        if end_date > session_date:
                            # End current session at 23:59:59 on start date
                            from datetime import time as time_type

                            session_end_day1 = datetime.combine(session_date, time_type(hour=23, minute=59, second=59)).replace(
                                tzinfo=AMSTERDAM_TZ
                            )

                            logoff_found = True

                            # Create session ending at 23:59:59
                            sessions.append(
                                {
                                    "date": session_date.isoformat(),
                                    "start_time": session_start.strftime("%H:%M:%S"),
                                    "end_time": session_end_day1.strftime("%H:%M:%S"),
                                    "session_id": f"ses_{session_counter:04d}",
                                }
                            )
                            session_counter += 1

                            # Start new session at 00:00:00 next day
                            next_day = session_date + timedelta(days=1)
                            from datetime import time as time_type

                            next_session_start = datetime.combine(next_day, time_type(hour=0, minute=0, second=0)).replace(
                                tzinfo=AMSTERDAM_TZ
                            )

                            # Use the actual logoff time for the next day session
                            if session_end.date() == next_day:
                                sessions.append(
                                    {
                                        "date": next_day.isoformat(),
                                        "start_time": "00:00:00",
                                        "end_time": session_end.strftime("%H:%M:%S"),
                                        "session_id": f"ses_{session_counter:04d}",
                                    }
                                )
                                session_counter += 1

                            i = j + 1
                            break
                        else:
                            # Same day - normal session
                            logoff_found = True

                            sessions.append(
                                {
                                    "date": session_date.isoformat(),
                                    "start_time": session_start.strftime("%H:%M:%S"),
                                    "end_time": session_end.strftime("%H:%M:%S"),
                                    "session_id": f"ses_{session_counter:04d}",
                                }
                            )
                            session_counter += 1

                            i = j + 1
                            break

                    j += 1

                if not logoff_found:
                    # No matching logoff found - skip this logon
                    i += 1
            else:
                i += 1

        # Write filtered events to CSV
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["DateTime", "EventId", "EventType", "RecordId"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for _, event in events_with_dt:
                writer.writerow(event)

        logger.info(f"✅ Filtered {len(events_with_dt)} logon/logoff events to {output_file}")
        logger.info(f"✅ Created {len(sessions)} sessions from logon-logoff pairs")

        # Store sessions in context for next step
        context["logon_logoff_sessions"] = sessions
        context["logon_logoff_file"] = str(output_file)

        return create_step_report(
            "filter_logon_logoff",
            True,
            events_filtered=len(events_with_dt),
            sessions_created=len(sessions),
            output_file=str(output_file),
            message=f"Filtered {len(events_with_dt)} events, created {len(sessions)} sessions",
        )

    except Exception as e:
        logger.error(f"Error filtering logon/logoff events: {e}", exc_info=True)
        return create_step_report(
            "filter_logon_logoff",
            False,
            error=str(e),
            message="Failed to filter logon/logoff events",
        )


def step_polish_logon_logoff(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step: Polish logon/logoff timestamps (round to 5 minutes, add defined breaks).

    Reads all_logon_logoff.csv (or uses sessions from context),
    rounds timestamps to 5-minute intervals, and adds defined breaks.

    Output: all_logon_logoff_polished.csv with columns: date, start_time, end_time, session_id
    """
    logger.info("=" * 60)
    logger.info("STEP: POLISH LOGON/LOGOFF TIMESTAMPS")
    logger.info("=" * 60)

    from .time_utils import (
        round_to_quarter_hour,
        generate_lunch_break,
        generate_dinner_break,
        generate_work_break,
        calculate_work_hours_with_breaks,
    )

    # Get sessions from previous step
    sessions = context.get("logon_logoff_sessions", [])

    if not sessions:
        logger.warning("No sessions found from previous step")
        return create_step_report("polish_logon_logoff", False, message="No sessions to polish")

    output_file = DATA_DIR / "all_logon_logoff_polished.csv"

    polished_sessions = []

    for session in sessions:
        # Parse date and times
        date_str = session["date"]
        start_time_str = session["start_time"]
        end_time_str = session["end_time"]

        try:
            # Combine date and time
            start_dt = parse_datetime_flexible(f"{date_str} {start_time_str}")
            end_dt = parse_datetime_flexible(f"{date_str} {end_time_str}")

            if not start_dt or not end_dt:
                logger.warning(f"Could not parse datetime for session {session['session_id']}")
                continue

            # Round to 5-minute intervals
            polished_start = round_to_quarter_hour(start_dt)

            # Special case: if end_time is 23:59:59 or crosses day boundary, keep at 23:59:00
            original_end_date = end_dt.date()
            original_start_date = start_dt.date()
            if end_time_str == "23:59:59" or end_time_str == "00:00:00":
                # Day boundary marker - end at 23:59:00 on start date
                polished_end = polished_start.replace(hour=23, minute=59, second=0, microsecond=0)
            elif original_end_date > original_start_date:
                # Session crosses day boundary - end at 23:59:00 on start date
                polished_end = polished_start.replace(hour=23, minute=59, second=0, microsecond=0)
            else:
                # Normal rounding
                polished_end = round_to_quarter_hour(end_dt)
                # If rounding caused day boundary crossing, clip to 23:59:00
                if polished_start.date() != polished_end.date():
                    polished_end = polished_start.replace(hour=23, minute=59, second=0, microsecond=0)

            # Add breaks based on duration
            breaks = []
            duration_hours = (polished_end - polished_start).total_seconds() / 3600.0

            # Add 30-minute break for work blocks > 6 hours
            if duration_hours > 6.0:
                work_break = generate_work_break(polished_start, polished_end, session["session_id"])
                if work_break:
                    breaks.append(work_break)

            # Add lunch break for sessions >= 8 hours (full day)
            if duration_hours >= 8.0:
                lunch_break = generate_lunch_break(polished_start, session["session_id"])
                breaks.append(lunch_break)

                # Add dinner break if session extends into evening
                if polished_end.hour >= 17:
                    dinner_break = generate_dinner_break(polished_start, session["session_id"])
                    breaks.append(dinner_break)

            # Calculate work hours excluding breaks
            if breaks:
                work_hours = calculate_work_hours_with_breaks(polished_start, polished_end, breaks)
            else:
                work_hours = duration_hours

            # Store polished session
            polished_sessions.append(
                {
                    "date": polished_start.date().isoformat(),
                    "start_time": polished_start.strftime("%H:%M:%S"),
                    "end_time": polished_end.strftime("%H:%M:%S"),
                    "session_id": session["session_id"],
                }
            )

        except Exception as e:
            logger.warning(f"Error polishing session {session['session_id']}: {e}")
            continue

    # Write polished sessions to CSV
    try:
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["date", "start_time", "end_time", "session_id"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(polished_sessions)

        # Calculate total time in hours:minutes format
        total_seconds = 0
        for session in polished_sessions:
            start_dt = parse_datetime_flexible(f"{session['date']} {session['start_time']}")
            end_dt = parse_datetime_flexible(f"{session['date']} {session['end_time']}")
            if start_dt and end_dt:
                # Handle day boundary - if end is before start, it's next day
                if end_dt < start_dt:
                    end_dt = end_dt + timedelta(days=1)
                total_seconds += int((end_dt - start_dt).total_seconds())

        total_hours = total_seconds // 3600
        total_minutes = (total_seconds % 3600) // 60
        total_time_str = f"{total_hours}:{total_minutes:02d}"

        logger.info(f"✅ Polished {len(polished_sessions)} sessions to {output_file}")
        logger.info(f"   Total time: {total_time_str} (hours:minutes)")

        context["polished_logon_logoff_sessions"] = polished_sessions
        context["polished_logon_logoff_file"] = str(output_file)
        context["polished_logon_logoff_summary"] = {
            "sessions": len(polished_sessions),
            "total_time_hours_minutes": total_time_str,
            "total_seconds": total_seconds,
        }

        return create_step_report(
            "polish_logon_logoff",
            True,
            sessions_polished=len(polished_sessions),
            total_time_hours_minutes=total_time_str,
            total_seconds=total_seconds,
            output_file=str(output_file),
            message=f"Polished {len(polished_sessions)} sessions ({total_time_str} total)",
        )

    except Exception as e:
        logger.error(f"Error writing polished sessions: {e}", exc_info=True)
        return create_step_report(
            "polish_logon_logoff",
            False,
            error=str(e),
            message="Failed to write polished sessions",
        )


def step_load_polished_sessions(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step: Load polished logon/logoff sessions into WBSODataset.

    Replaces the old load_computer_on_sessions step by loading sessions from
    the polished logon/logoff CSV file (all_logon_logoff_polished.csv).
    """
    logger.info("=" * 60)
    logger.info("STEP: LOAD POLISHED LOGON/LOGOFF SESSIONS")
    logger.info("=" * 60)

    # Get polished sessions from previous step or load from file
    polished_sessions = context.get("polished_logon_logoff_sessions", [])
    polished_file = context.get("polished_logon_logoff_file")

    # If not in context, load from file
    if not polished_sessions and polished_file:
        polished_file_path = Path(polished_file)
        if polished_file_path.exists():
            try:
                with open(polished_file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    polished_sessions = list(reader)
                logger.info(f"Loaded {len(polished_sessions)} sessions from {polished_file_path.name}")
            except Exception as e:
                logger.error(f"Error loading polished sessions from file: {e}")
                return create_step_report("load_polished_sessions", False, message="Failed to load polished sessions")
        else:
            logger.error(f"Polished sessions file not found: {polished_file_path}")
            return create_step_report("load_polished_sessions", False, message="Polished sessions file not found")

    if not polished_sessions:
        logger.warning("No polished sessions found")
        return create_step_report("load_polished_sessions", False, message="No polished sessions found")

    # Convert polished sessions to WBSOSession objects
    dataset = WBSODataset()
    sessions = []

    for polished_session in polished_sessions:
        try:
            date_str = polished_session["date"]
            start_time_str = polished_session["start_time"]
            end_time_str = polished_session["end_time"]
            session_id = polished_session["session_id"]

            # Parse datetimes
            start_dt = parse_datetime_flexible(f"{date_str} {start_time_str}")
            end_dt = parse_datetime_flexible(f"{date_str} {end_time_str}")

            if not start_dt or not end_dt:
                logger.warning(f"Could not parse datetime for session {session_id}")
                continue

            # Handle day boundary - if end is before start, it's next day
            if end_dt < start_dt:
                end_dt = end_dt + timedelta(days=1)

            # Calculate duration
            duration = end_dt - start_dt
            duration_hours = duration.total_seconds() / 3600.0
            work_hours = duration_hours  # Will be adjusted by time polishing step if breaks are added

            # Determine session type based on duration
            if duration_hours >= 8.0:
                session_type = "full_day"
            elif duration_hours >= 4.0:
                session_type = "half_day"
            else:
                session_type = "short_session"

            # Determine if weekend
            session_date = start_dt.date()
            is_weekend = session_date.weekday() >= 5  # Saturday = 5, Sunday = 6

            # Create WBSOSession
            session = WBSOSession(
                session_id=session_id,
                start_time=start_dt,
                end_time=end_dt,
                work_hours=work_hours,
                duration_hours=duration_hours,
                date=date_str,
                session_type=session_type,
                is_wbso=True,  # All logon/logoff sessions are WBSO eligible
                wbso_category="GENERAL_RD",  # Default, will be updated by activity assignment
                is_synthetic=False,  # These are real sessions from system events
                commit_count=0,
                source_type="real",
                wbso_justification=f"Logon/logoff session: {start_time_str} to {end_time_str}",
                has_computer_on=True,  # Logon/logoff indicates computer was on
                is_weekend=is_weekend,
            )

            sessions.append(session)

        except Exception as e:
            logger.warning(f"Error creating session from polished data {polished_session.get('session_id', 'unknown')}: {e}")
            continue

    dataset.sessions = sessions

    if not dataset.sessions:
        logger.warning("No sessions created from polished data")
        return create_step_report("load_polished_sessions", False, message="No sessions created")

    # Store in context
    context["computer_on_dataset"] = dataset  # Keep for backward compatibility
    context["dataset"] = dataset  # Set as main dataset for subsequent steps

    total_hours = sum(s.work_hours for s in dataset.sessions)
    logger.info(f"✅ Loaded {len(dataset.sessions)} polished logon/logoff sessions ({total_hours:.2f} total hours)")

    return create_step_report(
        "load_polished_sessions",
        True,
        total_sessions=len(dataset.sessions),
        total_hours=total_hours,
        message=f"Loaded {len(dataset.sessions)} polished logon/logoff sessions",
    )


def step_system_events_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Summarize system events coverage and total hours available."""
    logger.info("=" * 60)
    logger.info("STEP: SYSTEM EVENTS SUMMARY")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset or not dataset.sessions:
        return create_step_report("system_events_summary", False, message="No dataset available")

    # Calculate total hours from all sessions
    total_hours = sum(s.work_hours for s in dataset.sessions)

    # Calculate hours in target date range
    target_hours = sum(
        s.work_hours
        for s in dataset.sessions
        if s.start_time and TARGET_START_DATE.date() <= s.start_time.date() <= TARGET_END_DATE.date()
    )

    # Calculate date range coverage
    session_dates = [
        s.start_time.date()
        for s in dataset.sessions
        if s.start_time and TARGET_START_DATE.date() <= s.start_time.date() <= TARGET_END_DATE.date()
    ]

    unique_dates = len(set(session_dates)) if session_dates else 0
    date_range_days = (TARGET_END_DATE.date() - TARGET_START_DATE.date()).days + 1
    coverage_percent = (unique_dates / date_range_days * 100) if date_range_days > 0 else 0

    # Calculate hours by session type
    full_day_hours = sum(s.work_hours for s in dataset.sessions if s.session_type == "full_day")
    half_day_hours = sum(s.work_hours for s in dataset.sessions if s.session_type == "half_day")
    short_hours = sum(s.work_hours for s in dataset.sessions if s.session_type == "short_session")

    summary = {
        "total_sessions": len(dataset.sessions),
        "total_hours": total_hours,
        "target_range_hours": target_hours,
        "target_start_date": TARGET_START_DATE.date().isoformat(),
        "target_end_date": TARGET_END_DATE.date().isoformat(),
        "unique_dates_with_sessions": unique_dates,
        "date_range_days": date_range_days,
        "coverage_percent": round(coverage_percent, 1),
        "hours_by_type": {
            "full_day": full_day_hours,
            "half_day": half_day_hours,
            "short_session": short_hours,
        },
        "wbso_requirement_hours": 510.0,
        "sufficient_for_wbso": target_hours >= 510.0,
        "excess_hours": max(0, target_hours - 510.0),
    }

    # Log summary
    logger.info("System Events Summary:")
    logger.info(f"  Total Sessions: {summary['total_sessions']}")
    logger.info(f"  Total Hours (all dates): {summary['total_hours']:.2f}")
    logger.info(
        f"  Target Range Hours ({summary['target_start_date']} to {summary['target_end_date']}): {summary['target_range_hours']:.2f}"
    )
    logger.info(
        f"  Unique Dates with Sessions: {summary['unique_dates_with_sessions']} / {summary['date_range_days']} ({summary['coverage_percent']:.1f}%)"
    )
    logger.info(f"  WBSO Requirement: {summary['wbso_requirement_hours']:.2f} hours")
    logger.info(f"  Sufficient for WBSO: {'✅ YES' if summary['sufficient_for_wbso'] else '❌ NO'}")
    if summary["excess_hours"] > 0:
        logger.info(f"  Excess Hours Available: {summary['excess_hours']:.2f} (can filter/select)")

    context["system_events_summary"] = summary

    return create_step_report(
        "system_events_summary",
        True,
        **summary,
        message=f"System events summary: {target_hours:.2f} hours in target range",
    )


def step_load_activities(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Load or generate WBSO activities list."""
    logger.info("=" * 60)
    logger.info("STEP: LOAD ACTIVITIES")
    logger.info("=" * 60)

    from .activities import WBSOActivities

    force_regenerate = context.get("force_regenerate_activities", False)

    # Load or generate activities
    activities_manager = WBSOActivities()
    activities_manager.load_activities(force_regenerate=force_regenerate)

    # Store in context for later steps
    context["activities_manager"] = activities_manager

    total_hours = activities_manager.get_total_estimated_hours()
    action = "Regenerated" if force_regenerate else "Loaded"

    logger.info(f"✅ {action} {len(activities_manager.activities)} WBSO activities ({total_hours:.2f} total estimated hours)")
    return create_step_report(
        "load_activities",
        True,
        total_activities=len(activities_manager.activities),
        total_estimated_hours=total_hours,
        regenerated=force_regenerate,
        message=f"{action} {len(activities_manager.activities)} activities",
    )


def step_validate(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Validate data sources (optional if computer-on sessions already loaded)."""
    logger.info("=" * 60)
    logger.info("STEP: VALIDATION")
    logger.info("=" * 60)

    # Skip validation if computer-on sessions are already loaded
    if context.get("computer_on_dataset"):
        logger.info("Skipping validation - computer-on sessions already loaded")
        return create_step_report(
            "validate",
            True,
            skipped=True,
            message="Validation skipped - using computer-on sessions",
        )

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
    """Step: Polish times (round to 5-minute intervals, add breaks, clip to max daily hours)."""
    logger.info("=" * 60)
    logger.info("STEP: TIME POLISHING")
    logger.info("=" * 60)

    from .time_utils import (
        round_to_quarter_hour,
        generate_lunch_break,
        generate_dinner_break,
        generate_work_break,
        calculate_work_hours_with_breaks,
        clip_to_max_daily_hours,
    )

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("time_polish", False, message="No dataset available")

    polished_count = 0
    break_added_count = 0
    clipped_count = 0

    # Track daily hours to enforce 11-hour max per day
    daily_hours: Dict[str, float] = {}  # date -> total hours

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

        # Clip to max 11 hours per day
        session_date = session.start_time.date().isoformat()
        current_daily_hours = daily_hours.get(session_date, 0.0)
        duration_hours = (session.end_time - session.start_time).total_seconds() / 3600.0

        if current_daily_hours + duration_hours > 11.0:
            # Clip end time to stay within daily limit
            remaining_hours = 11.0 - current_daily_hours
            if remaining_hours > 0:
                session.end_time = session.start_time + timedelta(hours=remaining_hours)
                session.end_time = round_to_quarter_hour(session.end_time)
                clipped_count += 1
            else:
                # Skip this session if no hours remaining
                logger.warning(f"Session {session.session_id} skipped: daily limit reached")
                continue

        # Update daily hours tracking
        duration_hours = (session.end_time - session.start_time).total_seconds() / 3600.0
        daily_hours[session_date] = daily_hours.get(session_date, 0.0) + duration_hours

        # Add breaks
        breaks = []
        duration_hours = (session.end_time - session.start_time).total_seconds() / 3600.0

        # Add 30-minute break for work blocks > 6 hours
        if duration_hours > 6.0:
            work_break = generate_work_break(session.start_time, session.end_time, session.session_id)
            if work_break:
                breaks.append(work_break)

        # Add lunch break for full_day sessions
        if session.session_type == "full_day":
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
        else:
            # Update work_hours to match duration if no breaks
            session.work_hours = duration_hours

    logger.info(
        f"✅ Time polishing complete: {polished_count} sessions rounded, {break_added_count} sessions with breaks, {clipped_count} sessions clipped"
    )
    return create_step_report(
        "time_polish",
        True,
        polished_count=polished_count,
        break_added_count=break_added_count,
        clipped_count=clipped_count,
        message="Time polishing completed",
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


def step_store_activity_blocks(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Store polished computer activity blocks for human review.

    Stores date, starttime, endtime for each activity block.
    Multiple blocks per day are supported.

    Output file is stored in the data directory for persistence and version control.
    """
    logger.info("=" * 60)
    logger.info("STEP: STORE ACTIVITY BLOCKS FOR REVIEW")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("store_activity_blocks", False, message="No dataset available")

    # Prepare output file in data directory for persistence and version control
    output_file = DATA_DIR / "system_events_time_blocks.csv"
    DATA_DIR.mkdir(exist_ok=True, parents=True)

    # Collect all sessions with their time information
    activity_blocks = []
    for session in dataset.sessions:
        if not session.start_time or not session.end_time:
            continue

        # Extract date and times
        date = session.start_time.date().isoformat()
        start_time = session.start_time.strftime("%H:%M:%S")
        end_time = session.end_time.strftime("%H:%M:%S")

        # Calculate duration
        duration_hours = session.work_hours

        activity_blocks.append(
            {
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": round(duration_hours, 2),
                "session_id": session.session_id,
                "session_type": session.session_type,
                "is_wbso": session.is_wbso,
                "source_type": session.source_type,
            }
        )

    # Sort by date, then by start time
    activity_blocks.sort(key=lambda x: (x["date"], x["start_time"]))

    # Write to CSV
    try:
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            fieldnames = [
                "date",
                "start_time",
                "end_time",
                "duration_hours",
                "session_id",
                "session_type",
                "is_wbso",
                "source_type",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(activity_blocks)

        # Count blocks by date
        blocks_by_date = {}
        for block in activity_blocks:
            date = block["date"]
            blocks_by_date[date] = blocks_by_date.get(date, 0) + 1

        total_blocks = len(activity_blocks)
        unique_dates = len(blocks_by_date)
        total_hours = sum(block["duration_hours"] for block in activity_blocks)

        logger.info(f"✅ Stored {total_blocks} activity blocks across {unique_dates} dates ({total_hours:.2f} total hours)")
        logger.info(f"   Output file: {output_file}")

        # Log sample dates with multiple blocks
        multi_block_dates = [(date, count) for date, count in blocks_by_date.items() if count > 1]
        if multi_block_dates:
            logger.info(f"   Dates with multiple blocks: {len(multi_block_dates)}")
            for date, count in sorted(multi_block_dates)[:10]:  # Show first 10
                logger.info(f"     {date}: {count} blocks")

        context["activity_blocks_file"] = str(output_file)
        context["activity_blocks_count"] = total_blocks

        return create_step_report(
            "store_activity_blocks",
            True,
            total_blocks=total_blocks,
            unique_dates=unique_dates,
            total_hours=total_hours,
            output_file=str(output_file),
            message=f"Stored {total_blocks} activity blocks for review",
        )
    except Exception as e:
        logger.error(f"❌ Failed to store activity blocks: {e}")
        return create_step_report(
            "store_activity_blocks",
            False,
            error=str(e),
            message="Failed to store activity blocks",
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


def _load_git_commits_by_repo() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load git commits from all CSV files, grouped by repository.

    Returns:
        Dictionary mapping repo_name -> list of commit dictionaries
    """
    commits_by_repo = {}
    commits_dir = DATA_DIR / "commits"

    if not commits_dir.exists():
        return commits_by_repo

    commit_files = list(commits_dir.glob("*.csv"))

    for commit_file in commit_files:
        repo_name = commit_file.stem
        commits = []

        try:
            with open(commit_file, "r", encoding="utf-8") as f:
                # Try pipe delimiter first, then comma
                try:
                    reader = csv.DictReader(f, delimiter="|")
                except:
                    f.seek(0)
                    reader = csv.DictReader(f, delimiter=",")

                for row in reader:
                    dt_str = row.get("datetime") or row.get("timestamp")
                    if dt_str:
                        try:
                            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                            commit = {
                                "repo": repo_name,
                                "hash": row.get("hash", ""),
                                "message": row.get("message", ""),
                                "author": row.get("author", ""),
                                "datetime": dt,
                                "date": dt.date().isoformat(),
                            }
                            commits.append(commit)
                        except Exception as e:
                            logger.debug(f"Error parsing commit datetime: {e}")
                            continue
        except Exception as e:
            logger.warning(f"Error reading commit file {commit_file}: {e}")
            continue

        if commits:
            commits_by_repo[repo_name] = commits

    return commits_by_repo


def _get_repo_purpose_activity_mapping() -> Dict[str, str]:
    """
    Map repository names to likely WBSO activity IDs based on repo purpose.

    Returns:
        Dictionary mapping repo_name -> activity_id
    """
    # Map repository names to activities based on their purpose
    repo_activity_map = {
        "on_prem_rag": "rag_pipeline_development",
        "on_prem_rag_updated": "rag_pipeline_development",
        "context_engineering": "ai_framework_development",
        "langflow_org": "ai_framework_development",
        "healthcare-aigent": "ai_framework_development",
        "datacation-chatbot-workspace": "ai_framework_development",
        "genai-hackathon": "ai_framework_development",
        "gemini_agent": "ai_framework_development",
        "WBSO-AICM-2025-01": "architecture_design",  # Planning/documentation
        "chrome_extensions": "api_development",
        "gmail_summarize_draft": "nlp_implementation",
        "motivatie-brieven-ai": "nlp_implementation",
        "my_chat_gpt": "ai_framework_development",
        "job_hunt": None,  # Not WBSO related
    }

    return repo_activity_map


def step_assign_activities(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Assign WBSO activities based on commit messages, repo purpose, and track days with work."""
    logger.info("=" * 60)
    logger.info("STEP: ACTIVITY ASSIGNMENT")
    logger.info("=" * 60)

    from .activities import WBSOActivities

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("assign_activities", False, message="No dataset available")

    # Get activities manager from context (should be loaded in step_load_activities)
    activities_manager = context.get("activities_manager")
    if not activities_manager:
        # Fallback: load if not in context
        from .activities import WBSOActivities

        activities_manager = WBSOActivities()
        activities_manager.load_activities(force_regenerate=False)
        context["activities_manager"] = activities_manager

    # Load git commits by repo for better matching
    commits_by_repo = _load_git_commits_by_repo()
    repo_activity_map = _get_repo_purpose_activity_mapping()

    # Track days with work: date -> {commits: [], sessions: []}
    days_with_work: Dict[str, Dict[str, Any]] = {}

    # Track previous activity per day for fallback
    previous_activity_by_date: Dict[str, str] = {}

    assigned_count = 0
    fallback_count = 0
    repo_matched_count = 0

    for session in dataset.sessions:
        if not session.is_wbso:
            continue

        # Determine if weekend
        if session.start_time:
            session.is_weekend = session.start_time.weekday() >= 5  # Saturday = 5, Sunday = 6
            session_date = session.start_time.date().isoformat()

            # Initialize day tracking if not exists
            if session_date not in days_with_work:
                days_with_work[session_date] = {
                    "commits": [],
                    "sessions": [],
                    "has_computer_on": False,
                    "has_commits": False,
                }

            # Track session
            days_with_work[session_date]["sessions"].append(session.session_id)

            # Check if session has computer on event (source_type == "real" indicates computer on)
            if session.source_type == "real":
                session.has_computer_on = True
                days_with_work[session_date]["has_computer_on"] = True

            # Get commit messages for this session
            commit_messages = session.commit_messages if hasattr(session, "commit_messages") and session.commit_messages else []

            # Try to find commits from repo data for this date
            session_commits = []
            for repo_name, commits in commits_by_repo.items():
                for commit in commits:
                    if commit["date"] == session_date:
                        session_commits.append(commit)
                        if commit["message"] not in commit_messages:
                            commit_messages.append(commit["message"])

            # Track commits
            if commit_messages:
                days_with_work[session_date]["commits"].extend(commit_messages)
                days_with_work[session_date]["has_commits"] = True

            # Try to match activity by repo first (if commits found)
            activity = None
            if session_commits:
                # Get unique repo names from commits
                repo_names = list(set(c["repo"] for c in session_commits))

                # Try to match by repo purpose
                for repo_name in repo_names:
                    if repo_name in repo_activity_map:
                        activity_id = repo_activity_map[repo_name]
                        if activity_id and activity_id in activities_manager.activity_map:
                            activity = activities_manager.activity_map[activity_id]
                            repo_matched_count += 1
                            logger.debug(f"Matched activity by repo: {repo_name} -> {activity_id}")
                            break

            # If no repo match, try commit message matching
            if not activity:
                previous_activity_id = previous_activity_by_date.get(session_date)
                activity = activities_manager.find_activity_by_commits(commit_messages, previous_activity_id)

            # Assign activity
            if activity:
                session.activity_id = activity["id"]
                session.wbso_category = activity["category"]  # Update category from activity
                if not session.wbso_justification:
                    session.wbso_justification = activity.get("description_nl", "")
                assigned_count += 1

                # Store as previous activity for this date
                previous_activity_by_date[session_date] = activity["id"]
            else:
                # Fallback to previous activity
                previous_activity_id = previous_activity_by_date.get(session_date)
                if previous_activity_id:
                    session.activity_id = previous_activity_id
                    if previous_activity_id in activities_manager.activity_map:
                        activity = activities_manager.activity_map[previous_activity_id]
                        session.wbso_category = activity["category"]
                        if not session.wbso_justification:
                            session.wbso_justification = activity.get("description_nl", "")
                    fallback_count += 1
                else:
                    # Final fallback: use existing category
                    logger.warning(f"No activity assigned for session {session.session_id}, using existing category")

    context["days_with_work"] = days_with_work
    context["activities_manager"] = activities_manager
    context["commits_by_repo"] = commits_by_repo

    logger.info(
        f"✅ Activity assignment complete: {assigned_count} assigned ({repo_matched_count} by repo), {fallback_count} fallback, {len(days_with_work)} days with work"
    )
    return create_step_report(
        "assign_activities",
        True,
        assigned_count=assigned_count,
        repo_matched_count=repo_matched_count,
        fallback_count=fallback_count,
        days_with_work=len(days_with_work),
        message=f"Assigned activities to {assigned_count} sessions ({repo_matched_count} by repo)",
    )


def step_detect_commits_without_system_events(context: Dict[str, Any]) -> Dict[str, Any]:
    """Step: Detect git commits on days that do not have system events (work on different computers)."""
    logger.info("=" * 60)
    logger.info("STEP: DETECT COMMITS WITHOUT SYSTEM EVENTS")
    logger.info("=" * 60)

    dataset = context.get("dataset")
    if not dataset:
        return create_step_report("detect_commits_without_system_events", False, message="No dataset available")

    # Get all unique dates from system events
    system_event_dates = set()
    for session in dataset.sessions:
        if session.start_time:
            system_event_dates.add(session.start_time.date().isoformat())

    # Load git commits
    commits_by_repo = context.get("commits_by_repo")
    if not commits_by_repo:
        commits_by_repo = _load_git_commits_by_repo()
        context["commits_by_repo"] = commits_by_repo

    # Find commits on dates without system events
    commits_without_system_events: Dict[str, List[Dict[str, Any]]] = {}

    for repo_name, commits in commits_by_repo.items():
        for commit in commits:
            commit_date = commit["date"]

            # Check if this date has system events
            if commit_date not in system_event_dates:
                if commit_date not in commits_without_system_events:
                    commits_without_system_events[commit_date] = []

                commits_without_system_events[commit_date].append(
                    {
                        "repo": commit["repo"],
                        "hash": commit["hash"],
                        "message": commit["message"],
                        "author": commit["author"],
                        "datetime": commit["datetime"].isoformat(),
                    }
                )

    # Sort dates
    sorted_dates = sorted(commits_without_system_events.keys())
    total_commits = sum(len(commits) for commits in commits_without_system_events.values())
    unique_repos = set()
    for commits in commits_without_system_events.values():
        for commit in commits:
            unique_repos.add(commit["repo"])

    # Log summary
    logger.info(f"Found {total_commits} commits on {len(commits_without_system_events)} dates without system events")
    logger.info(f"Affected repositories: {len(unique_repos)} ({', '.join(sorted(unique_repos))})")

    if sorted_dates:
        logger.info(f"Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
        logger.info("Sample dates (first 10):")
        for date in sorted_dates[:10]:
            commits = commits_without_system_events[date]
            logger.info(f"  {date}: {len(commits)} commits ({', '.join(set(c['repo'] for c in commits))})")

    context["commits_without_system_events"] = commits_without_system_events

    return create_step_report(
        "detect_commits_without_system_events",
        True,
        total_commits=total_commits,
        unique_dates=len(commits_without_system_events),
        unique_repos=len(unique_repos),
        date_range={
            "start": sorted_dates[0] if sorted_dates else None,
            "end": sorted_dates[-1] if sorted_dates else None,
        },
        commits_by_date=commits_without_system_events,
        message=f"Found {total_commits} commits on {len(commits_without_system_events)} dates without system events",
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

    # Get activities manager for activity names
    activities_manager = context.get("activities_manager")
    if not activities_manager:
        from .activities import WBSOActivities

        activities_manager = WBSOActivities()
        activities_manager.load_activities(force_regenerate=False)

    for session in wbso_sessions:
        try:
            # Get activity name in Dutch
            activity_name_nl = None
            if session.activity_id:
                activity_name_nl = activities_manager.get_activity_name_nl(session.activity_id)

            event = CalendarEvent.from_wbso_session(session, activity_name_nl=activity_name_nl)
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
    """Step: Generate summary report with total hours booked."""
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

    # Count sessions by type
    computer_on_sessions = [s for s in wbso_sessions if s.has_computer_on] if dataset else []
    computer_on_hours = sum(
        s.work_hours
        for s in computer_on_sessions
        if s.start_time and TARGET_START_DATE.date() <= s.start_time.date() <= TARGET_END_DATE.date()
    )

    report_data = {
        "calculated_hours": calculated_hours,
        "calendar_hours": calendar_hours,
        "computer_on_hours": computer_on_hours,
        "total_sessions": len(wbso_sessions),
        "computer_on_sessions": len(computer_on_sessions),
        "gap": calculated_hours - calendar_hours,
        "target_hours": 510.0,
        "target_gap": 510.0 - calendar_hours,
        "target_achievement_percent": (calendar_hours / 510.0 * 100) if 510.0 > 0 else 0,
    }

    context["report_data"] = report_data

    logger.info("=" * 60)
    logger.info("TIME SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Sessions: {len(wbso_sessions)}")
    logger.info(f"Computer-On Sessions: {len(computer_on_sessions)}")
    logger.info(f"Calculated Hours: {calculated_hours:.2f} hours")
    logger.info(f"Computer-On Hours: {computer_on_hours:.2f} hours")
    logger.info(f"Calendar Hours (Booked): {calendar_hours:.2f} hours")
    logger.info(f"Target Hours: 510.0 hours")
    logger.info(f"Target Achievement: {(calendar_hours / 510.0 * 100):.1f}%")
    logger.info("=" * 60)

    logger.info(f"✅ Report generated: {calendar_hours:.2f} hours in calendar, {calculated_hours:.2f} calculated")
    return create_step_report("report", True, **report_data, message="Report generated successfully")
