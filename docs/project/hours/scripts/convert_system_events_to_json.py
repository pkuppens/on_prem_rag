#!/usr/bin/env python3
"""
Convert System Events CSV to JSON with Date Extraction

This script converts the all_system_events.csv file to JSON format,
extracting the date field separately for easier matching.

Usage:
    python convert_system_events_to_json.py [--input-file INPUT_FILE] [--output-file OUTPUT_FILE]
"""

import argparse
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_datetime_string(datetime_str: str) -> tuple[str, str]:
    """Parse datetime string and extract date and time components.

    Args:
        datetime_str: DateTime string in format like "4/27/2025 9:21:21 AM"

    Returns:
        Tuple of (date_string, time_string) in YYYY-MM-DD and HH:MM:SS format
    """
    if not datetime_str or datetime_str.strip() == "":
        return "unknown", "unknown"

    try:
        # Handle the BOM and quotes in the datetime string
        clean_datetime = datetime_str.strip()
        if clean_datetime.startswith('"'):
            clean_datetime = clean_datetime[1:]
        if clean_datetime.endswith('"'):
            clean_datetime = clean_datetime[:-1]
        # Remove BOM if present
        if clean_datetime.startswith("\ufeff"):
            clean_datetime = clean_datetime[1:]

        if not clean_datetime:
            return "unknown", "unknown"

        # Parse the datetime string - try different formats
        try:
            # Try format like "4/27/2025 9:21:21 AM"
            dt = datetime.strptime(clean_datetime, "%m/%d/%Y %I:%M:%S %p")
        except ValueError:
            try:
                # Try format like "2025/08/21 08:34:17"
                dt = datetime.strptime(clean_datetime, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                # Try format like "2025-08-21 08:34:17"
                dt = datetime.strptime(clean_datetime, "%Y-%m-%d %H:%M:%S")

        # Format date and time
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")

        return date_str, time_str
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{datetime_str}': {e}")
        return "unknown", "unknown"


def convert_system_events_to_json(input_file: Path, output_file: Path) -> None:
    """Convert system events CSV to JSON with date extraction.

    Args:
        input_file: Input CSV file path
        output_file: Output JSON file path
    """
    logger.info(f"Converting system events from: {input_file}")
    logger.info(f"Output file: {output_file}")

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return

    events: List[Dict[str, Any]] = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                # Extract date and time from DateTime field (handle BOM and quotes)
                # The field name has a BOM character, so we need to handle it properly
                datetime_field = ""
                for key in row.keys():
                    if "DateTime" in key:
                        datetime_field = row[key]
                        break

                if not datetime_field:
                    datetime_field = row.get("DateTime", "")
                date_str, time_str = parse_datetime_string(datetime_field)

                # Create standardized datetime string in YYYY-MM-DD HH:MM:SS format
                standardized_datetime = (
                    f"{date_str} {time_str}" if date_str != "unknown" and time_str != "unknown" else datetime_field
                )

                # Create event record with extracted date
                event = {
                    "record_id": row.get("RecordId", ""),
                    "datetime": standardized_datetime,
                    "date": date_str,
                    "time": time_str,
                    "event_id": row.get("EventId", ""),
                    "log_name": row.get("LogName", ""),
                    "event_type": row.get("EventType", ""),
                    "level": row.get("Level", ""),
                    "username": row.get("Username", ""),
                    "process_name": row.get("ProcessName", ""),
                    "message": row.get("Message", ""),
                    "additional_info": row.get("AdditionalInfo", ""),
                }

                events.append(event)

                if row_num % 100 == 0:
                    logger.info(f"Processed {row_num - 1} events...")

    except Exception as e:
        logger.error(f"Error reading input file {input_file}: {e}")
        return

    logger.info(f"Converted {len(events)} system events")

    # Write to JSON file
    try:
        output_data = {"system_events": events, "total_events": len(events), "conversion_timestamp": datetime.now().isoformat()}

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully wrote {len(events)} events to {output_file}")

    except Exception as e:
        logger.error(f"Error writing output file {output_file}: {e}")


def main():
    """Main function to convert system events CSV to JSON."""
    parser = argparse.ArgumentParser(description="Convert system events CSV to JSON with date extraction")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "all_system_events.csv",
        help="Input CSV file (default: docs/project/hours/data/all_system_events.csv)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "all_system_events.json",
        help="Output JSON file (default: docs/project/hours/data/all_system_events.json)",
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert system events
    convert_system_events_to_json(args.input_file, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
