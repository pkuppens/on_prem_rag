#!/usr/bin/env python3
"""
Work Sessions Merger for WBSO Hours Registration

This script merges synthetic work sessions with existing work sessions to create
a complete work log for WBSO hours registration. It combines real sessions from
system events with synthetic sessions generated from unassigned commits.

TASK-034: Synthetic Work Session Generation from Unassigned Commits (Part 2)
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Date: 2025-01-15
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WorkSessionsMerger:
    """Merges real and synthetic work sessions into a complete work log."""

    def __init__(self):
        """Initialize the merger."""
        pass

    def load_work_log(self, work_log_file: Path) -> Dict[str, Any]:
        """Load existing work log with real sessions."""
        logger.info(f"Loading work log from: {work_log_file}")

        with open(work_log_file, "r", encoding="utf-8") as f:
            work_log = json.load(f)

        logger.info(f"Loaded {len(work_log.get('work_sessions', []))} real work sessions")
        return work_log

    def load_synthetic_sessions(self, synthetic_sessions_file: Path) -> Dict[str, Any]:
        """Load synthetic sessions."""
        logger.info(f"Loading synthetic sessions from: {synthetic_sessions_file}")

        with open(synthetic_sessions_file, "r", encoding="utf-8") as f:
            synthetic_data = json.load(f)

        synthetic_sessions = synthetic_data.get("synthetic_sessions", [])
        logger.info(f"Loaded {len(synthetic_sessions)} synthetic sessions")
        return synthetic_data

    def convert_synthetic_to_work_session_format(self, synthetic_session: Dict[str, Any]) -> Dict[str, Any]:
        """Convert synthetic session format to work session format."""
        return {
            "session_id": synthetic_session["session_id"],
            "block_id": f"synthetic_{synthetic_session['session_id']}",
            "start_time": synthetic_session["start_time"],
            "end_time": synthetic_session["end_time"],
            "total_duration_minutes": int(synthetic_session["duration_hours"] * 60),
            "work_duration_minutes": int(synthetic_session["work_hours"] * 60),
            "duration_hours": synthetic_session["duration_hours"],
            "work_hours": synthetic_session["work_hours"],
            "date": synthetic_session["date"],
            "crosses_midnight": False,
            "confidence_score": synthetic_session["confidence_score"],
            "evidence": [f"synthetic_session_{synthetic_session['session_id']}"],
            "session_type": synthetic_session["session_type"],
            "lunch_break": None,
            "dinner_break": None,
            "work_items": [],
            "work_item_count": 0,
            "work_item_types": {},
            "work_efficiency": 1.0,
            "break_efficiency": 0.0,
            "assigned_commits": synthetic_session["source_commits"],
            "commit_count": synthetic_session["commit_count"],
            "is_wbso": synthetic_session["is_wbso"],
            "wbso_category": synthetic_session["wbso_category"],
            "wbso_justification": synthetic_session["wbso_justification"],
            "is_synthetic": True,  # Flag to identify synthetic sessions
        }

    def merge_sessions(self, work_log: Dict[str, Any], synthetic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge real and synthetic sessions."""
        logger.info("Merging real and synthetic work sessions")

        # Get existing work sessions
        real_sessions = work_log.get("work_sessions", [])
        synthetic_sessions = synthetic_data.get("synthetic_sessions", [])

        # Convert synthetic sessions to work session format
        converted_synthetic = []
        for synthetic_session in synthetic_sessions:
            converted = self.convert_synthetic_to_work_session_format(synthetic_session)
            converted_synthetic.append(converted)

        # Combine all sessions
        all_sessions = real_sessions + converted_synthetic

        # Sort by start time
        all_sessions.sort(key=lambda x: x["start_time"])

        # Calculate new summary statistics
        total_sessions = len(all_sessions)
        wbso_sessions = [s for s in all_sessions if s.get("is_wbso", False)]
        total_work_hours = sum(s.get("work_hours", 0) for s in all_sessions)
        wbso_work_hours = sum(s.get("work_hours", 0) for s in wbso_sessions)

        # Count synthetic vs real sessions
        synthetic_count = len(converted_synthetic)
        real_count = len(real_sessions)

        # Calculate WBSO category breakdown
        wbso_category_stats = {}
        for session in wbso_sessions:
            category = session.get("wbso_category", "UNKNOWN")
            if category not in wbso_category_stats:
                wbso_category_stats[category] = {"count": 0, "hours": 0.0}
            wbso_category_stats[category]["count"] += 1
            wbso_category_stats[category]["hours"] += session.get("work_hours", 0)

        # Create merged work log
        merged_work_log = {
            "work_sessions": all_sessions,
            "unassigned_commits": work_log.get("unassigned_commits", {}),
            "summary": {
                "total_work_sessions": total_sessions,
                "real_sessions": real_count,
                "synthetic_sessions": synthetic_count,
                "wbso_eligible_sessions": len(wbso_sessions),
                "total_work_hours": total_work_hours,
                "wbso_work_hours": wbso_work_hours,
                "wbso_percentage": (wbso_work_hours / total_work_hours * 100) if total_work_hours > 0 else 0,
                "wbso_category_breakdown": wbso_category_stats,
                "merge_date": datetime.now().isoformat(),
                "source": "merged_real_and_synthetic_sessions",
            },
        }

        logger.info(f"Merged {real_count} real + {synthetic_count} synthetic = {total_sessions} total sessions")
        logger.info(f"Total work hours: {total_work_hours:.2f} (WBSO: {wbso_work_hours:.2f})")
        logger.info(f"WBSO percentage: {merged_work_log['summary']['wbso_percentage']:.1f}%")

        return merged_work_log

    def save_merged_work_log(self, merged_work_log: Dict[str, Any], output_file: Path) -> None:
        """Save merged work log to file."""
        logger.info(f"Saving merged work log to: {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_work_log, f, indent=2, ensure_ascii=False)

        summary = merged_work_log["summary"]
        logger.info(f"Saved complete work log:")
        logger.info(f"  - Total sessions: {summary['total_work_sessions']}")
        logger.info(f"  - Real sessions: {summary['real_sessions']}")
        logger.info(f"  - Synthetic sessions: {summary['synthetic_sessions']}")
        logger.info(f"  - WBSO sessions: {summary['wbso_eligible_sessions']}")
        logger.info(f"  - Total hours: {summary['total_work_hours']:.2f}")
        logger.info(f"  - WBSO hours: {summary['wbso_work_hours']:.2f}")
        logger.info(f"  - WBSO percentage: {summary['wbso_percentage']:.1f}%")


def main():
    """Main function to merge work sessions."""
    # File paths
    work_log_file = Path("data/work_log.json")
    synthetic_sessions_file = Path("data/synthetic_sessions.json")
    output_file = Path("data/work_log_complete.json")

    # Validate input files exist
    if not work_log_file.exists():
        logger.error(f"Work log file not found: {work_log_file}")
        return

    if not synthetic_sessions_file.exists():
        logger.error(f"Synthetic sessions file not found: {synthetic_sessions_file}")
        return

    # Create merger
    merger = WorkSessionsMerger()

    # Load data
    work_log = merger.load_work_log(work_log_file)
    synthetic_data = merger.load_synthetic_sessions(synthetic_sessions_file)

    # Merge sessions
    merged_work_log = merger.merge_sessions(work_log, synthetic_data)

    # Save results
    merger.save_merged_work_log(merged_work_log, output_file)

    logger.info("Work sessions merger completed successfully")


if __name__ == "__main__":
    main()
