#!/usr/bin/env python3
"""
CSV Commit Data Processing Script for WBSO Hours Registration

This script processes CSV commit history files to generate structured JSON output
for WBSO hours registration and work block analysis.

Usage:
    python process_commit_csvs.py [--input-dir INPUT_DIR] [--output-file OUTPUT_FILE]

Output:
    - Structured JSON with commit records and metadata
    - WBSO commit identification and work block integration ready format
"""

import argparse
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_datetime_to_iso(datetime_str: str) -> Optional[str]:
    """Parse datetime string to ISO 8601 format.

    Args:
        datetime_str: Datetime string in format "YYYY-MM-DD HH:MM:SS +HHMM"

    Returns:
        ISO 8601 formatted datetime string or None if parsing fails
    """
    try:
        # Handle format: "2025-05-30 20:33:36 +0200"
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S %z")
        return dt.isoformat()
    except ValueError:
        try:
            # Handle format without timezone: "2025-05-30 20:33:36"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
        except ValueError:
            logger.warning(f"Failed to parse datetime: {datetime_str}")
            return None


def extract_repo_name(filename: str) -> str:
    """Extract repository name from CSV filename.

    Args:
        filename: CSV filename (e.g., "on_prem_rag.csv")

    Returns:
        Repository name without .csv extension
    """
    return Path(filename).stem


def is_wbso_author(author: str) -> bool:
    """Check if commit author is WBSO holder (case-insensitive 'kuppens' matching).

    Args:
        author: Commit author name

    Returns:
        True if author contains 'kuppens' (case-insensitive)
    """
    return "kuppens" in author.lower()


def is_wbso_commit(author: str, timestamp: str) -> bool:
    """Check if commit is eligible for WBSO (author AND date criteria).

    Args:
        author: Commit author name
        timestamp: ISO 8601 timestamp string

    Returns:
        True if author is WBSO holder AND timestamp >= 2025-06-01
    """
    if not is_wbso_author(author):
        return False

    try:
        # Parse timestamp and check if it's >= 2025-06-01
        from datetime import datetime

        commit_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        wbso_start_date = datetime.fromisoformat("2025-06-01T00:00:00+00:00")
        return commit_date >= wbso_start_date
    except (ValueError, TypeError):
        logger.warning(f"Invalid timestamp for WBSO check: {timestamp}")
        return False


def process_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single CSV file and return commit records.

    Args:
        file_path: Path to CSV file

    Returns:
        List of commit records (only WBSO authors)
    """
    commits = []
    repo_name = extract_repo_name(file_path.name)

    try:
        # Try different encodings to handle various file formats
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        f = None
        for encoding in encodings:
            try:
                f = open(file_path, "r", encoding=encoding)
                break
            except UnicodeDecodeError:
                if f:
                    f.close()
                continue

        if not f:
            logger.error(f"Could not read file {file_path} with any supported encoding")
            return []

        with f:
            # Use pipe delimiter as specified in the format
            reader = csv.DictReader(f, delimiter="|")

            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    # Validate required fields
                    required_fields = ["datetime", "timestamp", "message", "author", "hash"]
                    if not all(field in row and row[field].strip() for field in required_fields):
                        logger.warning(f"Skipping row {row_num} in {file_path.name}: missing required fields")
                        continue

                    # Filter out non-WBSO authors
                    if not is_wbso_author(row["author"]):
                        continue  # Skip commits by non-WBSO authors

                    # Parse datetime to ISO format
                    iso_timestamp = parse_datetime_to_iso(row["datetime"])
                    if not iso_timestamp:
                        logger.warning(f"Skipping row {row_num} in {file_path.name}: invalid datetime")
                        continue

                    # Create commit record
                    commit = {
                        "timestamp": iso_timestamp,
                        "repo_name": repo_name,
                        "author": row["author"].strip(),
                        "message": row["message"].strip(),
                        "hash": row["hash"].strip(),
                        "is_wbso": is_wbso_commit(row["author"], iso_timestamp),
                        "work_block_id": None,  # Will be populated in integration phase
                        "outside_work_block": False,  # Will be determined in integration phase
                    }

                    commits.append(commit)

                except Exception as e:
                    logger.error(f"Error processing row {row_num} in {file_path.name}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    logger.info(f"Processed {len(commits)} WBSO author commits from {file_path.name}")
    return commits


def generate_metadata(commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate metadata from processed commits.

    Args:
        commits: List of commit records

    Returns:
        Metadata dictionary
    """
    if not commits:
        return {"total_commits": 0, "wbso_commits": 0, "repositories": [], "date_range": {"start": None, "end": None}}

    # Count commits (all are WBSO authors, but only some are WBSO eligible by date)
    total_commits = len(commits)  # All commits are from WBSO authors
    wbso_commits = sum(1 for commit in commits if commit["is_wbso"])  # Commits eligible for WBSO (date >= 2025-06-01)

    # Get unique repositories
    repositories = sorted(list(set(commit["repo_name"] for commit in commits)))

    # Get date range
    timestamps = [commit["timestamp"] for commit in commits if commit["timestamp"]]
    if timestamps:
        timestamps.sort()
        date_range = {"start": timestamps[0], "end": timestamps[-1]}
    else:
        date_range = {"start": None, "end": None}

    return {"total_commits": total_commits, "wbso_commits": wbso_commits, "repositories": repositories, "date_range": date_range}


def process_commit_csvs(input_dir: Path, output_file: Path) -> None:
    """Process all CSV files in input directory and generate JSON output.

    Args:
        input_dir: Directory containing CSV files
        output_file: Output JSON file path
    """
    logger.info(f"Processing CSV files from: {input_dir}")
    logger.info(f"Output file: {output_file}")

    # Find all CSV files
    csv_files = list(input_dir.glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {input_dir}")
        return

    logger.info(f"Found {len(csv_files)} CSV files")

    # Process all CSV files
    all_commits = []
    for csv_file in csv_files:
        commits = process_csv_file(csv_file)
        all_commits.extend(commits)

    # Sort commits by timestamp
    all_commits.sort(key=lambda x: x["timestamp"])

    # Generate metadata
    metadata = generate_metadata(all_commits)

    # Create output structure
    output_data = {"commits": all_commits, "metadata": metadata}

    # Write JSON output
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully wrote {len(all_commits)} WBSO author commits to {output_file}")
        logger.info(f"WBSO eligible commits (>=2025-06-01): {metadata['wbso_commits']}/{metadata['total_commits']}")
        logger.info(f"Repositories: {', '.join(metadata['repositories'])}")
        logger.info(f"Date range: {metadata['date_range']['start']} to {metadata['date_range']['end']}")

    except Exception as e:
        logger.error(f"Error writing output file {output_file}: {e}")


def main():
    """Main function to process commit CSV files."""
    parser = argparse.ArgumentParser(description="Process CSV commit data files to JSON format for WBSO hours registration")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits",
        help="Directory containing CSV commit files (default: docs/project/hours/data/commits)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits_processed.json",
        help="Output JSON file path (default: docs/project/hours/data/commits_processed.json)",
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return 1

    # Create output directory if it doesn't exist
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # Process CSV files
    process_commit_csvs(args.input_dir, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
