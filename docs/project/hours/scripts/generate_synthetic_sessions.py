#!/usr/bin/env python3
"""
Synthetic Work Session Generator for WBSO Hours Registration

This script generates synthetic work sessions for unassigned commits that don't have
matching computer-on records. These commits likely represent work done on different
PCs or laptops and need to be converted into reasonable work sessions for WBSO compliance.

TASK-034: Synthetic Work Session Generation from Unassigned Commits
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Date: 2025-01-15
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class SyntheticSession:
    """Represents a synthetic work session generated from unassigned commits."""

    session_id: str
    start_time: str
    end_time: str
    duration_hours: float
    work_hours: float
    date: str
    session_type: str  # 'morning', 'afternoon', 'evening'
    confidence_score: float
    source_commits: List[Dict[str, Any]]
    commit_count: int
    is_wbso: bool
    wbso_category: str
    wbso_justification: str


class SyntheticSessionGenerator:
    """Generates synthetic work sessions from unassigned commits."""

    def __init__(self):
        """Initialize the generator with session templates."""
        # Session templates based on typical work patterns
        self.session_templates = {
            "morning": {
                "start_hour": 8,
                "start_minute": 0,
                "duration_hours": 4.0,
                "work_hours": 3.5,  # 30 min break
                "description": "Morning development session",
            },
            "afternoon": {
                "start_hour": 13,
                "start_minute": 0,
                "duration_hours": 4.0,
                "work_hours": 3.5,  # 30 min break
                "description": "Afternoon development session",
            },
            "evening": {
                "start_hour": 19,
                "start_minute": 0,
                "duration_hours": 3.0,
                "work_hours": 3.0,  # No break for evening
                "description": "Evening development session",
            },
        }

        # WBSO categories and their keywords
        self.wbso_categories = {
            "AI_FRAMEWORK": {
                "keywords": ["ai", "agent", "llm", "gpt", "openai", "anthropic", "claude", "framework", "nlp", "natural language"],
                "justification": "AI framework development and natural language processing implementation",
            },
            "ACCESS_CONTROL": {
                "keywords": ["auth", "authentication", "authorization", "security", "access", "permission", "role", "jwt", "oauth"],
                "justification": "Access control and authentication system development",
            },
            "PRIVACY_CLOUD": {
                "keywords": ["privacy", "cloud", "data", "protection", "gdpr", "avg", "anonymization", "pseudonymization"],
                "justification": "Privacy-preserving cloud integration and data protection mechanisms",
            },
            "AUDIT_LOGGING": {
                "keywords": ["audit", "log", "logging", "trace", "monitor", "track", "history"],
                "justification": "Audit logging and system monitoring implementation",
            },
            "DATA_INTEGRITY": {
                "keywords": ["integrity", "validation", "corruption", "backup", "recovery", "consistency"],
                "justification": "Data integrity protection and validation systems",
            },
            "GENERAL_RD": {
                "keywords": ["research", "development", "rd", "innovation", "experiment", "prototype"],
                "justification": "General research and development activities",
            },
        }

    def determine_session_type(self, commit_timestamp: str) -> str:
        """Determine session type based on commit timestamp."""
        try:
            dt = datetime.fromisoformat(commit_timestamp.replace("Z", "+00:00"))
            hour = dt.hour

            if 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 18:
                return "afternoon"
            else:
                return "evening"
        except Exception as e:
            logger.warning(f"Error parsing timestamp {commit_timestamp}: {e}")
            return "afternoon"  # Default to afternoon

    def categorize_wbso_activity(self, commit_message: str) -> tuple[str, str]:
        """Categorize commit message for WBSO activity and generate justification."""
        message_lower = commit_message.lower()

        # Check each category
        for category, config in self.wbso_categories.items():
            for keyword in config["keywords"]:
                if keyword in message_lower:
                    return category, config["justification"]

        # Default to general R&D if no specific category matches
        return "GENERAL_RD", "General research and development activities"

    def generate_session_from_commits(self, commits: List[Dict[str, Any]], date: str) -> List[SyntheticSession]:
        """Generate synthetic sessions from commits on the same date."""
        if not commits:
            return []

        # Group commits by session type
        sessions_by_type = {"morning": [], "afternoon": [], "evening": []}

        for commit in commits:
            session_type = self.determine_session_type(commit["timestamp"])
            sessions_by_type[session_type].append(commit)

        synthetic_sessions = []

        for session_type, session_commits in sessions_by_type.items():
            if not session_commits:
                continue

            # Create synthetic session
            template = self.session_templates[session_type]

            # Use earliest commit time as reference, but adjust to session template
            earliest_commit = min(session_commits, key=lambda x: x["timestamp"])
            commit_dt = datetime.fromisoformat(earliest_commit["timestamp"].replace("Z", "+00:00"))

            # Create session start time using template
            session_start = commit_dt.replace(hour=template["start_hour"], minute=template["start_minute"], second=0, microsecond=0)
            session_end = session_start + timedelta(hours=template["duration_hours"])

            # Determine WBSO category from commit messages
            wbso_category = "GENERAL_RD"
            wbso_justification = "General research and development activities"

            # Use the most specific WBSO category found in commits
            for commit in session_commits:
                category, justification = self.categorize_wbso_activity(commit["message"])
                if category != "GENERAL_RD":
                    wbso_category = category
                    wbso_justification = justification
                    break

            # Create synthetic session
            session = SyntheticSession(
                session_id=f"synthetic_{date}_{session_type}_{len(synthetic_sessions) + 1}",
                start_time=session_start.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=session_end.strftime("%Y-%m-%d %H:%M:%S"),
                duration_hours=template["duration_hours"],
                work_hours=template["work_hours"],
                date=date,
                session_type=session_type,
                confidence_score=0.8,  # High confidence for synthetic sessions
                source_commits=session_commits,
                commit_count=len(session_commits),
                is_wbso=True,  # All synthetic sessions are WBSO-eligible
                wbso_category=wbso_category,
                wbso_justification=wbso_justification,
            )

            synthetic_sessions.append(session)

        return synthetic_sessions

    def generate_synthetic_sessions(self, work_log_file: Path) -> List[SyntheticSession]:
        """Generate synthetic sessions from unassigned commits in work log."""
        logger.info(f"Loading work log from: {work_log_file}")

        with open(work_log_file, "r", encoding="utf-8") as f:
            work_log = json.load(f)

        # Get unassigned commits
        unassigned_commits = work_log.get("unassigned_commits", {})
        logger.info(f"Found unassigned commits for {len(unassigned_commits)} dates")

        all_synthetic_sessions = []

        for date, date_data in unassigned_commits.items():
            commits = date_data.get("commits", [])
            if not commits:
                continue

            logger.info(f"Processing {len(commits)} unassigned commits for {date}")

            # Generate synthetic sessions for this date
            date_sessions = self.generate_session_from_commits(commits, date)
            all_synthetic_sessions.extend(date_sessions)

            logger.info(f"Generated {len(date_sessions)} synthetic sessions for {date}")

        logger.info(f"Total synthetic sessions generated: {len(all_synthetic_sessions)}")
        return all_synthetic_sessions

    def save_synthetic_sessions(self, sessions: List[SyntheticSession], output_file: Path) -> None:
        """Save synthetic sessions to JSON file."""
        # Convert sessions to dictionaries
        sessions_data = [asdict(session) for session in sessions]

        # Calculate summary statistics
        total_hours = sum(session.work_hours for session in sessions)
        total_sessions = len(sessions)

        # Group by WBSO category
        category_stats = {}
        for session in sessions:
            category = session.wbso_category
            if category not in category_stats:
                category_stats[category] = {"count": 0, "hours": 0.0}
            category_stats[category]["count"] += 1
            category_stats[category]["hours"] += session.work_hours

        # Create output structure
        output_data = {
            "synthetic_sessions": sessions_data,
            "summary": {
                "total_sessions": total_sessions,
                "total_hours": total_hours,
                "average_hours_per_session": total_hours / total_sessions if total_sessions > 0 else 0,
                "category_breakdown": category_stats,
                "generation_date": datetime.now().isoformat(),
                "source": "unassigned_commits_from_work_log",
            },
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {total_sessions} synthetic sessions ({total_hours:.2f} hours) to {output_file}")
        logger.info(f"Category breakdown: {category_stats}")


def main():
    """Main function to generate synthetic sessions."""
    # File paths
    work_log_file = Path("data/work_log.json")
    output_file = Path("data/synthetic_sessions.json")

    # Validate input file exists
    if not work_log_file.exists():
        logger.error(f"Work log file not found: {work_log_file}")
        return

    # Create generator
    generator = SyntheticSessionGenerator()

    # Generate synthetic sessions
    synthetic_sessions = generator.generate_synthetic_sessions(work_log_file)

    if not synthetic_sessions:
        logger.warning("No synthetic sessions generated")
        return

    # Save results
    generator.save_synthetic_sessions(synthetic_sessions, output_file)

    logger.info("Synthetic session generation completed successfully")


if __name__ == "__main__":
    main()
