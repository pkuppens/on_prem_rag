#!/usr/bin/env python3
"""
Generate Activity-Repository Mapping Markdown

Generates Markdown output in Dutch format with activity sections, sub-activities, and repository mappings.

Author: AI Assistant
Created: 2025-11-30
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from .activity_repo_mapping import ActivityRepoMapping
from .logging_config import get_logger

logger = get_logger("generate_activity_repo_markdown")

# Default output path
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "output"
OUTPUT_MARKDOWN = OUTPUT_DIR / "activity_repo_mapping.md"


def generate_markdown(
    mapping_manager: Optional[ActivityRepoMapping] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate Markdown file with activity-repository mappings.

    Args:
        mapping_manager: ActivityRepoMapping instance (creates new if None)
        output_path: Output Markdown file path (uses default if None)

    Returns:
        Path to generated Markdown file
    """
    if mapping_manager is None:
        mapping_manager = ActivityRepoMapping()
        mapping_manager.load_repositories()
        mapping_manager.generate_mappings()

    output_path = output_path or OUTPUT_MARKDOWN
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get all activities with their mappings
    activities = mapping_manager.activities_manager.activities
    mappings = mapping_manager.mappings

    # Group mappings by activity
    activity_mappings: Dict[str, List[Dict[str, Any]]] = {}
    for mapping in mappings.values():
        activity_id = mapping.get("activity_id", "")
        if activity_id not in activity_mappings:
            activity_mappings[activity_id] = []
        activity_mappings[activity_id].append(mapping)

    # Generate Markdown content
    lines = []
    lines.append("# WBSO Activity-Repository Mapping")
    lines.append("")
    lines.append("Dit document toont de mapping tussen WBSO activiteiten en repositories.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Process each activity
    for activity in activities:
        activity_id = activity["id"]
        activity_name_nl = activity.get("name_nl", activity_id)
        activity_description = activity.get("description_nl", "")

        # Activity header
        lines.append(f"## {activity_name_nl}")
        lines.append("")

        if activity_description:
            lines.append(f"{activity_description}")
            lines.append("")

        # Sub-activities
        sub_activities = activity.get("sub_activities", [])
        if sub_activities:
            lines.append("**Sub-Activities:**")
            lines.append("")
            for sub_activity in sub_activities:
                sub_name = sub_activity.get("name_nl", sub_activity.get("id", ""))
                sub_desc = sub_activity.get("description_nl", "")
                lines.append(f"- **{sub_name}**")
                if sub_desc:
                    lines.append(f"  - {sub_desc}")
            lines.append("")

        # Repositories for this activity
        activity_repo_mappings = activity_mappings.get(activity_id, [])
        if activity_repo_mappings:
            lines.append("**Repositories:**")
            lines.append("")

            # Group by sub-activity if present
            main_mappings = [m for m in activity_repo_mappings if not m.get("sub_activity_id")]
            sub_mappings_by_id: Dict[str, List[Dict[str, Any]]] = {}
            for m in activity_repo_mappings:
                sub_id = m.get("sub_activity_id")
                if sub_id:
                    if sub_id not in sub_mappings_by_id:
                        sub_mappings_by_id[sub_id] = []
                    sub_mappings_by_id[sub_id].append(m)

            # Main activity repositories
            if main_mappings:
                for mapping in sorted(main_mappings, key=lambda m: m.get("repo_name", "")):
                    repo_name = mapping.get("repo_name", "")
                    rationale = mapping.get("rationale_nl", "")
                    confidence = mapping.get("confidence", "medium")
                    confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
                    lines.append(f"- {confidence_emoji} `{repo_name}`: {rationale}")

            # Sub-activity repositories
            for sub_activity_id, sub_mappings in sorted(sub_mappings_by_id.items()):
                sub_activity = mapping_manager.activities_manager.get_sub_activity_by_id(activity_id, sub_activity_id)
                if sub_activity:
                    sub_name = sub_activity.get("name_nl", sub_activity_id)
                    lines.append("")
                    lines.append(f"  *{sub_name}:*")
                    for mapping in sorted(sub_mappings, key=lambda m: m.get("repo_name", "")):
                        repo_name = mapping.get("repo_name", "")
                        rationale = mapping.get("rationale_nl", "")
                        confidence = mapping.get("confidence", "medium")
                        confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
                        lines.append(f"  - {confidence_emoji} `{repo_name}`: {rationale}")
        else:
            lines.append("*Geen repositories toegewezen aan deze activiteit.*")
            lines.append("")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Write Markdown file
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    total_mappings = len(mappings)
    logger.info(f"Generated Markdown with {len(activities)} activities and {total_mappings} mappings: {output_path}")
    return output_path


def main():
    """Main entry point for standalone execution."""
    mapping_manager = ActivityRepoMapping()
    mapping_manager.load_repositories()
    mapping_manager.generate_mappings()
    output_path = generate_markdown(mapping_manager)
    print(f"Markdown generated: {output_path}")


if __name__ == "__main__":
    main()
