#!/usr/bin/env python3
"""
Generate Activity-Repository Mapping CSV

Generates CSV output in Dutch format with Activity, Sub-Activity, Repo, and Rationale columns.

Author: AI Assistant
Created: 2025-11-30
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from .activity_repo_mapping import ActivityRepoMapping
from .logging_config import get_logger

logger = get_logger("generate_activity_repo_csv")

# Default output path
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "output"
OUTPUT_CSV = OUTPUT_DIR / "activity_repo_mapping.csv"


def generate_csv(
    mapping_manager: Optional[ActivityRepoMapping] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate CSV file with activity-repository mappings.

    Args:
        mapping_manager: ActivityRepoMapping instance (creates new if None)
        output_path: Output CSV file path (uses default if None)

    Returns:
        Path to generated CSV file
    """
    if mapping_manager is None:
        mapping_manager = ActivityRepoMapping()
        mapping_manager.load_repositories()
        mapping_manager.generate_mappings()

    output_path = output_path or OUTPUT_CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get all mappings
    mappings = list(mapping_manager.mappings.values())

    # Sort by activity name, then sub-activity, then repo
    activities_map = {act["id"]: act for act in mapping_manager.activities_manager.activities}

    def sort_key(mapping: Dict[str, Any]) -> tuple:
        activity_id = mapping.get("activity_id", "")
        sub_activity_id = mapping.get("sub_activity_id") or ""
        repo_name = mapping.get("repo_name", "")

        activity = activities_map.get(activity_id, {})
        activity_name = activity.get("name_nl", activity_id)

        if sub_activity_id:
            sub_activity = mapping_manager.activities_manager.get_sub_activity_by_id(activity_id, sub_activity_id)
            sub_activity_name = sub_activity.get("name_nl", sub_activity_id) if sub_activity else sub_activity_id
        else:
            sub_activity_name = ""

        return (activity_name, sub_activity_name, repo_name)

    mappings.sort(key=sort_key)

    # Write CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)

        # Header
        writer.writerow(["Activity", "Sub-Activity", "Repo", "Rationale"])

        # Rows
        for mapping in mappings:
            activity_id = mapping.get("activity_id", "")
            sub_activity_id = mapping.get("sub_activity_id")
            repo_name = mapping.get("repo_name", "")
            rationale = mapping.get("rationale_nl", "")

            activity = activities_map.get(activity_id, {})
            activity_name = activity.get("name_nl", activity_id)

            if sub_activity_id:
                sub_activity = mapping_manager.activities_manager.get_sub_activity_by_id(activity_id, sub_activity_id)
                sub_activity_name = sub_activity.get("name_nl", sub_activity_id) if sub_activity else sub_activity_id
            else:
                sub_activity_name = ""

            writer.writerow([activity_name, sub_activity_name, repo_name, rationale])

    logger.info(f"Generated CSV with {len(mappings)} mappings: {output_path}")
    return output_path


def main():
    """Main entry point for standalone execution."""
    mapping_manager = ActivityRepoMapping()
    mapping_manager.load_repositories()
    mapping_manager.generate_mappings()
    output_path = generate_csv(mapping_manager)
    print(f"CSV generated: {output_path}")


if __name__ == "__main__":
    main()
