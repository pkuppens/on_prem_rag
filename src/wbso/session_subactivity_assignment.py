#!/usr/bin/env python3
"""
Session-Subactivity Assignment Module

Assigns sub-activities to work sessions based on:
1. First commit after 2025/06/01 determines initial subactivity
2. Commits indicating different work trigger subactivity changes
3. Subactivity hour estimates - when reached, move to next subactivity

Author: AI Assistant
Created: 2025-11-30
"""

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .activities import WBSOActivities
from .activity_repo_mapping import ActivityRepoMapping
from .logging_config import get_logger
from .time_utils import parse_datetime_flexible

logger = get_logger("session_subactivity_assignment")

# Default paths
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "data"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "output"
WORK_SESSIONS_CSV = DATA_DIR / "work_session.csv"
COMMITS_DIR = DATA_DIR / "commits"
OUTPUT_CSV = OUTPUT_DIR / "session_subactivity_mapping.csv"

# Project start date
PROJECT_START_DATE = date(2025, 6, 1)


class SessionSubactivityAssignment:
    """Assigns sub-activities to work sessions based on commits and hour estimates."""

    def __init__(
        self,
        activities_manager: Optional[WBSOActivities] = None,
        mapping_manager: Optional[ActivityRepoMapping] = None,
    ):
        """Initialize assignment manager."""
        self.activities_manager = activities_manager or WBSOActivities()
        self.activities_manager.load_activities()

        self.mapping_manager = mapping_manager or ActivityRepoMapping()
        self.mapping_manager.load_repositories()
        self.mapping_manager.generate_mappings()

        # All sub-activities with parent activity info
        self.all_sub_activities: List[Dict[str, Any]] = []
        self._build_sub_activity_list()

        # Work sessions and commits
        self.work_sessions: List[Dict[str, Any]] = []
        self.commits_by_date: Dict[str, List[Dict[str, Any]]] = {}
        self.commits_by_session: Dict[str, List[Dict[str, Any]]] = {}

        # Assignment results
        self.assignments: List[Dict[str, Any]] = []

    def _build_sub_activity_list(self) -> None:
        """Build flat list of all sub-activities with parent info."""
        self.all_sub_activities = []
        for activity in self.activities_manager.activities:
            activity_id = activity["id"]
            activity_name_nl = activity.get("name_nl", "")
            for sub_activity in activity.get("sub_activities", []):
                sub_activity_with_parent = sub_activity.copy()
                sub_activity_with_parent["parent_activity_id"] = activity_id
                sub_activity_with_parent["parent_activity_name_nl"] = activity_name_nl
                self.all_sub_activities.append(sub_activity_with_parent)

        # Sort by estimated hours (descending) for priority
        self.all_sub_activities.sort(key=lambda x: x.get("estimated_hours", 0), reverse=True)
        logger.info(f"Built list of {len(self.all_sub_activities)} sub-activities")

    def load_work_sessions(self) -> None:
        """Load work sessions from CSV."""
        if not WORK_SESSIONS_CSV.exists():
            logger.warning(f"Work sessions CSV not found: {WORK_SESSIONS_CSV}")
            return

        self.work_sessions = []
        try:
            with open(WORK_SESSIONS_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session = {
                        "session_id": row.get("session_id", ""),
                        "date": row.get("date", ""),
                        "start_time": row.get("start_time", ""),
                        "end_time": row.get("end_time", ""),
                    }
                    if session["session_id"] and session["date"]:
                        self.work_sessions.append(session)

            # Sort by date and time
            self.work_sessions.sort(key=lambda s: (s["date"], s["start_time"]))
            logger.info(f"Loaded {len(self.work_sessions)} work sessions")
        except Exception as e:
            logger.error(f"Error loading work sessions: {e}")

    def load_commits(self) -> None:
        """Load commits and group by date and session."""
        # Load commits using the same method as pipeline_steps
        from .pipeline_steps import _load_git_commits_by_repo

        commits_by_repo = _load_git_commits_by_repo()

        # Flatten all commits
        all_commits = []
        for repo_name, commits in commits_by_repo.items():
            for commit in commits:
                commit_with_repo = commit.copy()
                commit_with_repo["repo"] = repo_name
                all_commits.append(commit_with_repo)

        # Group by date
        self.commits_by_date = defaultdict(list)
        for commit in all_commits:
            # Use date field if available, otherwise extract from datetime
            commit_date_str = commit.get("date")
            if not commit_date_str:
                commit_dt = commit.get("datetime")
                if commit_dt:
                    if isinstance(commit_dt, datetime):
                        commit_date_str = commit_dt.date().isoformat()
                    elif isinstance(commit_dt, str):
                        try:
                            commit_date_str = datetime.fromisoformat(commit_dt.replace("Z", "+00:00")).date().isoformat()
                        except:
                            continue

            if commit_date_str:
                self.commits_by_date[commit_date_str].append(commit)

        # Sort commits within each date
        for date_str in self.commits_by_date:
            self.commits_by_date[date_str].sort(key=lambda c: c.get("datetime", datetime.min))

        # Assign commits to sessions based on time overlap
        self.commits_by_session = defaultdict(list)
        for session in self.work_sessions:
            session_date = session["date"]
            session_start = parse_datetime_flexible(f"{session_date} {session['start_time']}")
            session_end = parse_datetime_flexible(f"{session_date} {session['end_time']}")

            if session_start and session_end:
                # Check commits on this date
                date_commits = self.commits_by_date.get(session_date, [])
                for commit in date_commits:
                    commit_dt = commit.get("datetime")
                    if commit_dt:
                        # Handle both datetime object and string
                        if isinstance(commit_dt, str):
                            try:
                                commit_dt = datetime.fromisoformat(commit_dt.replace("Z", "+00:00"))
                            except:
                                continue
                        if session_start <= commit_dt <= session_end:
                            self.commits_by_session[session["session_id"]].append(commit)

        logger.info(f"Loaded commits for {len(self.commits_by_date)} dates")
        logger.info(f"Assigned commits to {len(self.commits_by_session)} sessions")

    def find_initial_subactivity(self) -> Optional[Dict[str, Any]]:
        """
        Find initial subactivity based on first commit after PROJECT_START_DATE.

        Returns:
            Subactivity dictionary or None if no commit found
        """
        # Find first commit after project start
        first_commit = None
        first_commit_date = None

        for date_str, commits in self.commits_by_date.items():
            try:
                commit_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if commit_date >= PROJECT_START_DATE:
                    if first_commit_date is None or commit_date < first_commit_date:
                        first_commit_date = commit_date
                        first_commit = commits[0] if commits else None
            except ValueError:
                continue

        if not first_commit:
            logger.warning("No commits found after project start date, using first subactivity")
            return self.all_sub_activities[0] if self.all_sub_activities else None

        # Find best matching subactivity for first commit
        commit_text = f"{first_commit.get('message', '')} {first_commit.get('repo', '')}".lower()
        best_match = None
        best_score = 0

        for sub_activity in self.all_sub_activities:
            keywords = sub_activity.get("keywords", [])
            score = sum(1 for keyword in keywords if keyword.lower() in commit_text)
            if score > best_score:
                best_score = score
                best_match = sub_activity

        if best_match:
            logger.info(f"Initial subactivity determined from first commit ({first_commit_date}): {best_match.get('name_nl', '')}")
        else:
            best_match = self.all_sub_activities[0] if self.all_sub_activities else None
            logger.info(f"Using default initial subactivity: {best_match.get('name_nl', '') if best_match else 'None'}")

        return best_match

    def find_best_subactivity_for_commits(self, commits: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find best matching subactivity for a list of commits.

        Args:
            commits: List of commit dictionaries

        Returns:
            Best matching subactivity or None
        """
        if not commits:
            return None

        # Combine commit messages and repos
        commit_text = " ".join(f"{c.get('message', '')} {c.get('repo', '')}" for c in commits).lower()

        best_match = None
        best_score = 0

        for sub_activity in self.all_sub_activities:
            keywords = sub_activity.get("keywords", [])
            score = sum(1 for keyword in keywords if keyword.lower() in commit_text)
            if score > best_score:
                best_score = score
                best_match = sub_activity

        return best_match

    def assign_subactivities(self) -> None:
        """Assign sub-activities to work sessions based on commits and hour estimates."""
        if not self.work_sessions:
            logger.error("No work sessions loaded")
            return

        # Find initial subactivity
        current_subactivity = self.find_initial_subactivity()
        if not current_subactivity:
            logger.error("No subactivities available")
            return

        current_subactivity_hours = 0.0
        current_subactivity_estimate = current_subactivity.get("estimated_hours", 0.0)

        self.assignments = []

        # Process sessions chronologically
        for session in self.work_sessions:
            session_id = session["session_id"]
            session_date = session["date"]

            # Calculate session hours
            session_start = parse_datetime_flexible(f"{session_date} {session['start_time']}")
            session_end = parse_datetime_flexible(f"{session_date} {session['end_time']}")

            if not session_start or not session_end:
                logger.warning(f"Invalid session times for {session_id}, skipping")
                continue

            session_hours = (session_end - session_start).total_seconds() / 3600.0

            # Get commits for this session
            session_commits = self.commits_by_session.get(session_id, [])

            # Check if commits suggest different subactivity
            if session_commits:
                commit_based_subactivity = self.find_best_subactivity_for_commits(session_commits)
                if commit_based_subactivity and commit_based_subactivity["id"] != current_subactivity["id"]:
                    # Commits indicate different work - switch subactivity
                    logger.debug(
                        f"Switching subactivity based on commits: "
                        f"{current_subactivity.get('name_nl')} -> {commit_based_subactivity.get('name_nl')}"
                    )
                    current_subactivity = commit_based_subactivity
                    current_subactivity_hours = 0.0
                    current_subactivity_estimate = current_subactivity.get("estimated_hours", 0.0)

            # Check if current subactivity estimate is reached (with 50% overtime allowed)
            # Allow 50% overtime: multiply estimate by 1.5
            allowed_hours = current_subactivity_estimate * 1.5 if current_subactivity_estimate > 0 else 0
            if current_subactivity_estimate > 0 and current_subactivity_hours >= allowed_hours:
                # Find next subactivity (cycle through list)
                current_index = next(
                    (i for i, sub in enumerate(self.all_sub_activities) if sub["id"] == current_subactivity["id"]),
                    -1,
                )
                if current_index >= 0 and current_index < len(self.all_sub_activities) - 1:
                    current_subactivity = self.all_sub_activities[current_index + 1]
                    current_subactivity_hours = 0.0
                    current_subactivity_estimate = current_subactivity.get("estimated_hours", 0.0)
                    logger.debug(
                        f"Subactivity estimate reached (with 50% overtime: {current_subactivity_hours:.1f}h >= {allowed_hours:.1f}h), "
                        f"switching to: {current_subactivity.get('name_nl')}"
                    )
                else:
                    # Reached end of list, restart from beginning
                    current_subactivity = self.all_sub_activities[0]
                    current_subactivity_hours = 0.0
                    current_subactivity_estimate = current_subactivity.get("estimated_hours", 0.0)
                    logger.debug(f"Reached end of subactivities, restarting with: {current_subactivity.get('name_nl')}")

            # Assign current subactivity to session
            assignment = {
                "session_id": session_id,
                "date": session_date,
                "start_time": session["start_time"],
                "end_time": session["end_time"],
                "session_hours": session_hours,
                "activity_id": current_subactivity["parent_activity_id"],
                "activity_name_nl": current_subactivity["parent_activity_name_nl"],
                "sub_activity_id": current_subactivity["id"],
                "sub_activity_name_nl": current_subactivity.get("name_nl", ""),
                "sub_activity_estimated_hours": current_subactivity_estimate,
                "cumulative_hours": current_subactivity_hours + session_hours,
                "commit_count": len(session_commits),
            }

            self.assignments.append(assignment)

            # Update cumulative hours
            current_subactivity_hours += session_hours

        logger.info(f"Assigned sub-activities to {len(self.assignments)} sessions")

    def save_csv(self, output_path: Optional[Path] = None) -> Path:
        """
        Save session-subactivity assignments to CSV.

        Args:
            output_path: Output CSV path (uses default if None)

        Returns:
            Path to generated CSV file
        """
        output_path = output_path or OUTPUT_CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            fieldnames = [
                "session_id",
                "date",
                "start_time",
                "end_time",
                "session_hours",
                "activity_id",
                "activity_name_nl",
                "sub_activity_id",
                "sub_activity_name_nl",
                "sub_activity_estimated_hours",
                "cumulative_hours",
                "commit_count",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.assignments)

        logger.info(f"Saved {len(self.assignments)} assignments to {output_path}")
        return output_path


def main():
    """Main entry point for standalone execution."""
    assignment = SessionSubactivityAssignment()
    assignment.load_work_sessions()
    assignment.load_commits()
    assignment.assign_subactivities()
    output_path = assignment.save_csv()
    print(f"Session-subactivity assignments saved to: {output_path}")


if __name__ == "__main__":
    main()
