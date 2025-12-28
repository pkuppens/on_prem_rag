"""Data migration from JSON files to normalized WBSO database.

This module handles the migration of existing WBSO data from JSON files
to the normalized database schema, ensuring data integrity and relationships.

See docs/technical/WBSO_DATABASE_SCHEMA.md for schema details.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .database import (
    CalendarEvent,
    Commit,
    Repository,
    ValidationResult,
    WBSOCategory,
    WorkSession,
    get_wbso_session,
)
from .logging_config import get_logger

logger = get_logger("migration")


class WBSODataMigrator:
    """Handles migration of WBSO data from JSON files to normalized database."""

    def __init__(self, data_dir: Path):
        """Initialize the migrator with data directory path.

        Args:
            data_dir: Path to directory containing JSON data files
        """
        self.data_dir = data_dir
        self.session = get_wbso_session()

        # Cache for lookups during migration
        self._repository_cache: Dict[str, int] = {}
        self._category_cache: Dict[str, int] = {}

        logger.info(f"WBSODataMigrator initialized with data directory: {data_dir}")

    def migrate_all_data(self) -> Dict[str, int]:
        """Migrate all WBSO data from JSON files to database.

        Returns:
            Dictionary with migration statistics
        """
        logger.info("Starting WBSO data migration")

        try:
            # Initialize reference data
            self._initialize_categories()
            self._initialize_repositories()

            # Migrate core data
            session_stats = self._migrate_work_sessions()
            commit_stats = self._migrate_commits()
            calendar_stats = self._migrate_calendar_events()

            # Commit all changes
            self.session.commit()

            stats = {
                "repositories": len(self._repository_cache),
                "categories": len(self._category_cache),
                "work_sessions": session_stats["imported"],
                "commits": commit_stats["imported"],
                "calendar_events": calendar_stats["imported"],
                "errors": session_stats["errors"] + commit_stats["errors"] + calendar_stats["errors"],
            }

            logger.info(f"WBSO data migration completed successfully: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def _initialize_categories(self) -> None:
        """Initialize WBSO categories in the database."""
        categories = [
            {
                "code": "AI_FRAMEWORK",
                "name": "AI Framework Development",
                "description": "Development of AI agent frameworks and natural language processing systems",
                "justification_template": "AI framework development and natural language processing implementation",
            },
            {
                "code": "ACCESS_CONTROL",
                "name": "Access Control Systems",
                "description": "Research and development of role-based access control systems and authentication mechanisms",
                "justification_template": "Access control and authentication system development",
            },
            {
                "code": "PRIVACY_CLOUD",
                "name": "Privacy-Preserving Cloud Integration",
                "description": "Privacy-preserving cloud integration techniques including data anonymization and AVG compliance",
                "justification_template": "Privacy-preserving cloud integration and data protection mechanisms",
            },
            {
                "code": "AUDIT_LOGGING",
                "name": "Audit Logging Systems",
                "description": "Development of comprehensive audit logging systems for AI agent activities",
                "justification_template": "Audit logging and system monitoring implementation",
            },
            {
                "code": "DATA_INTEGRITY",
                "name": "Data Integrity Protection",
                "description": "Data integrity protection mechanisms and corruption prevention systems",
                "justification_template": "Data integrity protection and validation systems",
            },
            {
                "code": "GENERAL_RD",
                "name": "General Research and Development",
                "description": "General research and development activities supporting the project",
                "justification_template": "General research and development activities",
            },
        ]

        for cat_data in categories:
            existing = self.session.query(WBSOCategory).filter_by(code=cat_data["code"]).first()
            if not existing:
                category = WBSOCategory(**cat_data)
                self.session.add(category)
                self.session.flush()  # Get the ID
                self._category_cache[cat_data["code"]] = category.id
                logger.debug(f"Created category: {cat_data['code']}")
            else:
                self._category_cache[cat_data["code"]] = existing.id
                logger.debug(f"Using existing category: {cat_data['code']}")

    def _initialize_repositories(self) -> None:
        """Initialize repositories in the database."""
        # Load repository data from CSV if available
        repos_csv = self.data_dir / "repositories.csv"
        if repos_csv.exists():
            import csv

            with open(repos_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    repo_name = row.get("repo_name", "").strip()
                    if repo_name:
                        existing = self.session.query(Repository).filter_by(name=repo_name).first()
                        if not existing:
                            repository = Repository(
                                name=repo_name, url=row.get("url", ""), description=row.get("repo_description", "")
                            )
                            self.session.add(repository)
                            self.session.flush()
                            self._repository_cache[repo_name] = repository.id
                            logger.debug(f"Created repository: {repo_name}")
                        else:
                            self._repository_cache[repo_name] = existing.id
                            logger.debug(f"Using existing repository: {repo_name}")
        else:
            # Default repository if no CSV found
            default_repo = "on_prem_rag"
            existing = self.session.query(Repository).filter_by(name=default_repo).first()
            if not existing:
                repository = Repository(name=default_repo, description="On-premises RAG system repository")
                self.session.add(repository)
                self.session.flush()
                self._repository_cache[default_repo] = repository.id
            else:
                self._repository_cache[default_repo] = existing.id

    def _migrate_work_sessions(self) -> Dict[str, int]:
        """Migrate work sessions from JSON files."""
        imported = 0
        errors = 0

        # Load from work_log_complete.json
        work_log_file = self.data_dir / "work_log_complete.json"
        if work_log_file.exists():
            with open(work_log_file, "r", encoding="utf-8") as f:
                work_log_data = json.load(f)

            for session_data in work_log_data.get("sessions", []):
                try:
                    self._import_work_session(session_data, source_type="real")
                    imported += 1
                except Exception as e:
                    logger.error(f"Failed to import session {session_data.get('session_id', 'unknown')}: {e}")
                    errors += 1

        # Load from synthetic_sessions.json
        synthetic_file = self.data_dir / "synthetic_sessions.json"
        if synthetic_file.exists():
            with open(synthetic_file, "r", encoding="utf-8") as f:
                synthetic_data = json.load(f)

            for session_data in synthetic_data.get("sessions", []):
                try:
                    self._import_work_session(session_data, source_type="synthetic")
                    imported += 1
                except Exception as e:
                    logger.error(f"Failed to import synthetic session {session_data.get('session_id', 'unknown')}: {e}")
                    errors += 1

        return {"imported": imported, "errors": errors}

    def _import_work_session(self, session_data: Dict, source_type: str) -> None:
        """Import a single work session into the database."""
        session_id = session_data.get("session_id", "")

        # Check if session already exists
        existing = self.session.query(WorkSession).filter_by(session_id=session_id).first()
        if existing:
            logger.debug(f"Session {session_id} already exists, skipping")
            return

        # Parse datetime fields
        start_time = datetime.fromisoformat(session_data["start_time"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(session_data["end_time"].replace("Z", "+00:00"))

        # Get repository ID
        repository_id = None
        if "repository_name" in session_data and session_data["repository_name"]:
            repo_name = session_data["repository_name"]
            repository_id = self._repository_cache.get(repo_name)

        # Get category ID
        wbso_category_id = None
        if "wbso_category" in session_data and session_data["wbso_category"]:
            category_code = session_data["wbso_category"]
            wbso_category_id = self._category_cache.get(category_code)

        # Create work session
        work_session = WorkSession(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            work_hours=str(session_data.get("work_hours", 0.0)),
            duration_hours=str(session_data.get("duration_hours", 0.0)),
            date=session_data.get("date", ""),
            session_type=session_data.get("session_type", ""),
            is_wbso=session_data.get("is_wbso", False),
            wbso_category_id=wbso_category_id,
            is_synthetic=session_data.get("is_synthetic", False),
            repository_id=repository_id,
            wbso_justification=session_data.get("wbso_justification", ""),
            confidence_score=str(session_data.get("confidence_score", 1.0)),
            source_type=source_type,
        )

        self.session.add(work_session)
        self.session.flush()  # Get the ID for relationships

    def _migrate_commits(self) -> Dict[str, int]:
        """Migrate commit data from CSV files."""
        imported = 0
        errors = 0

        commits_dir = self.data_dir / "commits"
        if not commits_dir.exists():
            logger.warning("Commits directory not found, skipping commit migration")
            return {"imported": 0, "errors": 0}

        for commit_file in commits_dir.glob("*.csv"):
            repo_name = commit_file.stem
            repository_id = self._repository_cache.get(repo_name)

            if not repository_id:
                logger.warning(f"Repository {repo_name} not found, skipping commits")
                continue

            try:
                import csv

                with open(commit_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            commit = Commit(
                                repository_id=repository_id,
                                commit_hash=row.get("hash", ""),
                                author=row.get("author", ""),
                                message=row.get("message", ""),
                                datetime=datetime.fromisoformat(row.get("datetime", "").replace("Z", "+00:00")),
                            )
                            self.session.add(commit)
                            imported += 1
                        except Exception as e:
                            logger.error(f"Failed to import commit {row.get('hash', 'unknown')}: {e}")
                            errors += 1
            except Exception as e:
                logger.error(f"Failed to process commit file {commit_file}: {e}")
                errors += 1

        return {"imported": imported, "errors": errors}

    def _migrate_calendar_events(self) -> Dict[str, int]:
        """Migrate calendar events from JSON files."""
        imported = 0
        errors = 0

        calendar_file = self.data_dir / "wbso_calendar_events.json"
        if not calendar_file.exists():
            logger.warning("Calendar events file not found, skipping calendar migration")
            return {"imported": 0, "errors": 0}

        with open(calendar_file, "r", encoding="utf-8") as f:
            calendar_data = json.load(f)

        for event_data in calendar_data.get("events", []):
            try:
                session_id = event_data.get("session_id", "")

                # Check if session exists
                session = self.session.query(WorkSession).filter_by(session_id=session_id).first()
                if not session:
                    logger.warning(f"Session {session_id} not found for calendar event")
                    continue

                # Check if calendar event already exists
                existing = self.session.query(CalendarEvent).filter_by(session_id=session_id).first()
                if existing:
                    logger.debug(f"Calendar event for session {session_id} already exists, skipping")
                    continue

                calendar_event = CalendarEvent(
                    session_id=session_id,
                    summary=event_data.get("summary", ""),
                    description=event_data.get("description", ""),
                    start_datetime=datetime.fromisoformat(event_data["start"]["dateTime"].replace("Z", "+00:00")),
                    end_datetime=datetime.fromisoformat(event_data["end"]["dateTime"].replace("Z", "+00:00")),
                    color_id=event_data.get("colorId", "1"),
                    location=event_data.get("location", "Home Office"),
                    transparency=event_data.get("transparency", "opaque"),
                )

                self.session.add(calendar_event)
                imported += 1

            except Exception as e:
                logger.error(f"Failed to import calendar event for session {event_data.get('session_id', 'unknown')}: {e}")
                errors += 1

        return {"imported": imported, "errors": errors}


def main():
    """Main function for running the migration."""
    import sys
    from pathlib import Path

    # Default data directory
    data_dir = Path("docs/project/hours/data")

    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    migrator = WBSODataMigrator(data_dir)
    stats = migrator.migrate_all_data()

    print("Migration completed successfully!")
    print(f"Statistics: {stats}")


if __name__ == "__main__":
    main()
