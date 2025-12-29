#!/usr/bin/env python3
"""
Collect and Deduplicate System Events

This script collects all system events from multiple CSV files, deduplicates them,
and stores the result in all_system_events.csv with the following improvements:

1. DateTime format: Converts to YYYY-MM-DD HH:mm:ss (24hr, sortable format) with timezone support
2. Column filtering: Removes redundant columns (LogName, Username, ProcessName, AdditionalInfo)
3. Deduplication: Removes duplicate events based on RecordId
4. One-off processing: Skips regeneration if output file exists unless --force-regenerate is used

Usage:
    python collect_system_events.py [--input-dir INPUT_DIR] [--output-file OUTPUT_FILE] [--force-regenerate]
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

# Import shared datetime parsing with timezone support
from backend.datetime_utils import AMSTERDAM_TZ, parse_datetime_with_timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def convert_datetime_format(dt_str: str) -> tuple[str, Optional[datetime]]:
    """Convert datetime to YYYY-MM-DD HH:mm:ss format with timezone support.

    Handles multiple input formats including timezone offsets (+0100, +0200, +02:00):
    - "4/27/2025 9:21:21 AM" (M/D/YYYY H:MM:SS AM/PM)
    - "2025/08/21 08:34:17" (YYYY/MM/DD HH:mm:ss)
    - "2025/08/21 08:34:17+0100" (with timezone offset)
    - "2025/08/21 08:34:17+0200" (with timezone offset)

    Args:
        dt_str: DateTime string in original format

    Returns:
        Tuple of (standardized_datetime_string, timezone_aware_datetime_object)
    """
    # Use shared timezone-aware parser
    dt = parse_datetime_with_timezone(dt_str, default_tz=AMSTERDAM_TZ)

    if dt is None:
        logger.warning(f"Could not parse datetime: {dt_str}")
        return dt_str, None

    # Convert to standard format string (timezone-naive representation in Amsterdam timezone)
    # The datetime object is timezone-aware, but we store the string representation
    standardized = dt.strftime("%Y-%m-%d %H:%M:%S")

    return standardized, dt


def filter_redundant_columns(row: Dict[str, Any]) -> Dict[str, Any]:
    """Remove columns that have single values or are mostly N/A.

    Keeps only essential columns: DateTime, EventId, EventType, Message, RecordId

    Args:
        row: Dictionary representing a CSV row

    Returns:
        Filtered dictionary with only essential columns
    """
    # Columns to keep (matching all_system_events.csv format)
    columns_to_keep = {"DateTime", "EventId", "EventType", "Message", "RecordId"}

    # Clean column names from BOM and filter
    filtered_row = {}
    for k, v in row.items():
        clean_key = k.replace("\ufeff", "")
        # Map common variations to standard column names
        if "DateTime" in clean_key or "datetime" in clean_key.lower():
            filtered_row["DateTime"] = v
        elif "EventId" in clean_key or "event_id" in clean_key.lower():
            filtered_row["EventId"] = v
        elif "EventType" in clean_key or "event_type" in clean_key.lower():
            filtered_row["EventType"] = v
        elif "Message" in clean_key:
            filtered_row["Message"] = v
        elif "RecordId" in clean_key or "record_id" in clean_key.lower():
            filtered_row["RecordId"] = v

    return filtered_row


def collect_and_deduplicate_system_events(
    input_dir: Path, output_file: Path, force_regenerate: bool = False, sort: bool = False
) -> None:
    """Collect system events from all CSV files and deduplicate them with improvements.

    This function:
    1. Converts DateTime format to YYYY-MM-DD HH:mm:ss (24hr, sortable) with timezone support
    2. Removes redundant columns (LogName, Username, ProcessName, AdditionalInfo)
    3. Deduplicates events based on RecordId
    4. One-off processing: Skips if output file exists unless force_regenerate is True

    Args:
        input_dir: Directory containing system events CSV files
        output_file: Output CSV file for deduplicated events
        force_regenerate: If True, regenerate even if output file exists
        sort: If True, sort events by timestamp after deduplication
    """
    # Check if output file exists and skip if not forcing regeneration
    if output_file.exists() and not force_regenerate:
        logger.info(f"Output file {output_file} already exists. Skipping regeneration.")
        logger.info("Use --force-regenerate to regenerate the file.")
        return

    logger.info(f"Collecting system events from: {input_dir}")
    logger.info(f"Output file: {output_file}")

    # Find all system events CSV files
    csv_files = list(input_dir.glob("system_events_*.csv"))
    if not csv_files:
        logger.error(f"No system events CSV files found in {input_dir}")
        return

    logger.info(f"Found {len(csv_files)} system events CSV files")

    # Collect all events with deduplication by RecordId
    seen_record_ids: Set[str] = set()
    all_events: list[Dict[str, Any]] = []

    for csv_file in csv_files:
        logger.info(f"Processing {csv_file.name}")

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    record_id = row.get("RecordId", "").strip()

                    # Skip rows with empty RecordId
                    if not record_id:
                        continue

                    # Skip if we've already seen this RecordId
                    if record_id in seen_record_ids:
                        continue

                    # Convert DateTime format to sortable format
                    # Handle BOM character in column name
                    datetime_key = None
                    for key in row.keys():
                        if "DateTime" in key:
                            datetime_key = key
                            break

                    if datetime_key:
                        standardized_dt, dt_obj = convert_datetime_format(row[datetime_key])
                        row[datetime_key] = standardized_dt
                        # Note: dt_obj is available but not stored in CSV to keep columns clean
                        # The standardized_dt string is in Amsterdam timezone (timezone-naive representation)

                    # Filter out redundant columns
                    filtered_row = filter_redundant_columns(row)

                    # Skip rows without DateTime (essential field)
                    if not filtered_row.get("DateTime") or not filtered_row.get("DateTime").strip():
                        continue

                    # Add to seen set and events list
                    seen_record_ids.add(record_id)
                    all_events.append(filtered_row)

        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            continue

    logger.info(f"Collected {len(all_events)} unique system events")

    # Write deduplicated events to output file
    if all_events:
        # Get fieldnames from first event, excluding internal fields
        all_fieldnames = list(all_events[0].keys())
        # Exclude internal fields that shouldn't be in CSV
        fieldnames = [f for f in all_fieldnames if not f.startswith("_")]

        if sort:
            # Sort by DateTime using proper datetime parsing for robust chronological ordering
            def get_sort_key(event: Dict[str, Any]) -> datetime:
                dt_str = event.get("DateTime", "")
                if dt_str:
                    try:
                        # Parse the standardized datetime string (YYYY-MM-DD HH:mm:ss)
                        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        # Fallback to string comparison if parsing fails
                        logger.warning(f"Could not parse datetime for sorting: {dt_str}")
                        return datetime.min
                return datetime.min

            all_events.sort(key=get_sort_key)

        try:
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                # Write only the selected fields
                for event in all_events:
                    writer.writerow({k: v for k, v in event.items() if k in fieldnames})

            logger.info(f"Successfully wrote {len(all_events)} deduplicated events to {output_file}")

        except Exception as e:
            logger.error(f"Error writing output file {output_file}: {e}")
    else:
        logger.warning("No events to write")


def main():
    """Main function to collect and deduplicate system events."""
    parser = argparse.ArgumentParser(description="Collect and deduplicate system events from multiple CSV files")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Directory containing system events CSV files (default: docs/project/hours/data)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "all_system_events.csv",
        help="Output CSV file for deduplicated events (default: docs/project/hours/data/all_system_events.csv)",
    )
    parser.add_argument(
        "-f",
        "--force-regenerate",
        action="store_true",
        help="Force regeneration even if output file already exists",
    )

    parser.add_argument(
        "-s",
        "--sort",
        action="store_true",
        help="Sort events by timestamp after deduplication",
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return 1

    # Collect and deduplicate system events
    collect_and_deduplicate_system_events(args.input_dir, args.output_file, args.force_regenerate, sort=args.sort)

    return 0


if __name__ == "__main__":
    exit(main())
