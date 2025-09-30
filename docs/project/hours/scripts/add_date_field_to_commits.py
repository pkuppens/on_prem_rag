#!/usr/bin/env python3
"""
Add Date Field to Commits JSON

This script adds a separate date field to the commits_processed.json file
for easier date-based matching.

Usage:
    python add_date_field_to_commits.py [--input-file INPUT_FILE] [--output-file OUTPUT_FILE]
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_date_from_timestamp(timestamp: str) -> str:
    """Extract date from ISO timestamp.

    Args:
        timestamp: ISO 8601 timestamp string

    Returns:
        Date string in YYYY-MM-DD format
    """
    try:
        # Parse the timestamp and extract date
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{timestamp}': {e}")
        return "unknown"


def add_date_field_to_commits(input_file: Path, output_file: Path) -> None:
    """Add date field to commits JSON file.

    Args:
        input_file: Input JSON file path
        output_file: Output JSON file path
    """
    logger.info(f"Adding date fields to commits from: {input_file}")
    logger.info(f"Output file: {output_file}")

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return

    try:
        # Read the existing JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        commits = data.get("commits", [])
        logger.info(f"Processing {len(commits)} commits")

        # Add date field to each commit
        for commit in commits:
            timestamp = commit.get("timestamp", "")
            if timestamp:
                date_str = extract_date_from_timestamp(timestamp)
                commit["date"] = date_str
            else:
                commit["date"] = "unknown"

        # Update metadata
        if "metadata" in data:
            data["metadata"]["conversion_timestamp"] = datetime.now().isoformat()
            data["metadata"]["date_field_added"] = True

        # Write updated JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully added date fields to {len(commits)} commits")
        logger.info(f"Updated file saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error processing file {input_file}: {e}")


def main():
    """Main function to add date fields to commits."""
    parser = argparse.ArgumentParser(description="Add date field to commits JSON file for easier date-based matching")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits_processed.json",
        help="Input JSON file (default: docs/project/hours/data/commits_processed.json)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits_processed.json",
        help="Output JSON file (default: docs/project/hours/data/commits_processed.json)",
    )

    args = parser.parse_args()

    # Add date fields to commits
    add_date_field_to_commits(args.input_file, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
