#!/usr/bin/env python3
"""
Collect and Deduplicate System Events

This script collects all system events from multiple CSV files, deduplicates them,
and stores the result in all_system_events.csv.

Usage:
    python collect_system_events.py [--input-dir INPUT_DIR] [--output-file OUTPUT_FILE]
"""

import argparse
import csv
import logging
from pathlib import Path
from typing import Set, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def collect_and_deduplicate_system_events(input_dir: Path, output_file: Path) -> None:
    """Collect system events from all CSV files and deduplicate them.

    Args:
        input_dir: Directory containing system events CSV files
        output_file: Output CSV file for deduplicated events
    """
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

                    # Skip if we've already seen this RecordId
                    if record_id in seen_record_ids:
                        continue

                    # Add to seen set and events list
                    seen_record_ids.add(record_id)
                    all_events.append(row)

        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            continue

    logger.info(f"Collected {len(all_events)} unique system events")

    # Write deduplicated events to output file
    if all_events:
        # Get fieldnames from first event
        fieldnames = list(all_events[0].keys())

        try:
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_events)

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

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return 1

    # Create output directory if it doesn't exist
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # Collect and deduplicate system events
    collect_and_deduplicate_system_events(args.input_dir, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
