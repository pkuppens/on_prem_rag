#!/usr/bin/env python3
"""
Activity-Repository Mapping Module

Manages many-to-many relationships between WBSO activities and repositories.
Supports automatic mapping generation based on commit analysis and manual overrides.

Author: AI Assistant
Created: 2025-11-30
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .activities import WBSOActivities
from .logging_config import get_logger

logger = get_logger("activity_repo_mapping")

# Default paths
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "data"
CONFIG_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "config"
REPOSITORIES_CSV = DATA_DIR / "repositories.csv"
COMMITS_DIR = DATA_DIR / "commits"
MAPPINGS_CONFIG = CONFIG_DIR / "activity_repo_mappings.json"


class ActivityRepoMapping:
    """Manages many-to-many activity-repository mappings."""

    def __init__(
        self,
        activities_manager: Optional[WBSOActivities] = None,
        repositories_csv: Optional[Path] = None,
        mappings_config: Optional[Path] = None,
    ):
        """Initialize mapping manager."""
        self.activities_manager = activities_manager or WBSOActivities()
        self.repositories_csv = repositories_csv or REPOSITORIES_CSV
        self.mappings_config = mappings_config or MAPPINGS_CONFIG

        # Load activities
        self.activities_manager.load_activities()

        # Load repositories
        self.repositories: List[Dict[str, Any]] = []
        self.repo_map: Dict[str, Dict[str, Any]] = {}  # repo_name -> repo dict

        # Mappings: (activity_id, sub_activity_id, repo_name) -> mapping dict
        self.mappings: Dict[Tuple[str, Optional[str], str], Dict[str, Any]] = {}

        # Manual overrides
        self.manual_overrides: List[Dict[str, Any]] = []

    def load_repositories(self) -> None:
        """Load repositories from CSV file."""
        if not self.repositories_csv.exists():
            logger.warning(f"Repositories CSV not found: {self.repositories_csv}")
            return

        self.repositories = []
        self.repo_map = {}

        try:
            with open(self.repositories_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    repo_name = row.get("repo_name", "").strip()
                    if not repo_name:
                        continue

                    repo_dict = {
                        "repo_name": repo_name,
                        "repo_description": row.get("repo_description", "").strip(),
                        "wbso_relevance": row.get("wbso_relevance", "").strip(),
                    }
                    self.repositories.append(repo_dict)
                    self.repo_map[repo_name] = repo_dict

            logger.info(f"Loaded {len(self.repositories)} repositories")
        except Exception as e:
            logger.error(f"Error loading repositories: {e}")

    def load_manual_overrides(self) -> None:
        """Load manual mapping overrides from config file."""
        if not self.mappings_config.exists():
            logger.info(f"No manual overrides file found: {self.mappings_config}")
            self.manual_overrides = []
            return

        try:
            with open(self.mappings_config, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.manual_overrides = data.get("mappings", [])
            logger.info(f"Loaded {len(self.manual_overrides)} manual mapping overrides")
        except Exception as e:
            logger.warning(f"Error loading manual overrides: {e}, using empty list")
            self.manual_overrides = []

    def load_git_commits_by_repo(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load git commits from all CSV files, grouped by repository.

        Returns:
            Dictionary mapping repo_name -> list of commit dictionaries
        """
        commits_by_repo = {}

        if not COMMITS_DIR.exists():
            logger.warning(f"Commits directory not found: {COMMITS_DIR}")
            return commits_by_repo

        commit_files = list(COMMITS_DIR.glob("*.csv"))

        for commit_file in commit_files:
            repo_name = commit_file.stem
            commits = []

            try:
                with open(commit_file, "r", encoding="utf-8") as f:
                    # Try pipe delimiter first, then comma
                    try:
                        reader = csv.DictReader(f, delimiter="|")
                    except:
                        f.seek(0)
                        reader = csv.DictReader(f, delimiter=",")

                    for row in reader:
                        commit = {
                            "repo": repo_name,
                            "hash": row.get("hash", ""),
                            "message": row.get("message", ""),
                            "author": row.get("author", ""),
                        }
                        commits.append(commit)
            except Exception as e:
                logger.warning(f"Error reading commit file {commit_file}: {e}")
                continue

            if commits:
                commits_by_repo[repo_name] = commits

        logger.info(f"Loaded commits for {len(commits_by_repo)} repositories")
        return commits_by_repo

    def calculate_activity_score(self, activity: Dict[str, Any], repo: Dict[str, Any], commits: List[Dict[str, Any]]) -> float:
        """
        Calculate relevance score between activity and repository.

        Args:
            activity: Activity dictionary
            repo: Repository dictionary
            commits: List of commit dictionaries for this repo

        Returns:
            Score (0.0 to 1.0) indicating relevance
        """
        score = 0.0
        max_score = 0.0

        # Score from repository description and WBSO relevance
        repo_text = f"{repo.get('repo_description', '')} {repo.get('wbso_relevance', '')}".lower()
        activity_keywords = activity.get("keywords", [])

        keyword_matches = sum(1 for keyword in activity_keywords if keyword.lower() in repo_text)
        if activity_keywords:
            max_score += 1.0
            score += min(keyword_matches / len(activity_keywords), 1.0)

        # Score from commit messages
        if commits:
            commit_text = " ".join(c.get("message", "") for c in commits).lower()
            commit_keyword_matches = sum(1 for keyword in activity_keywords if keyword.lower() in commit_text)
            if activity_keywords:
                max_score += 1.0
                score += min(commit_keyword_matches / (len(activity_keywords) * 2), 1.0)

        # Score from sub-activities
        sub_activities = activity.get("sub_activities", [])
        if sub_activities:
            sub_scores = []
            for sub_activity in sub_activities:
                sub_keywords = sub_activity.get("keywords", [])
                sub_keyword_matches = sum(1 for keyword in sub_keywords if keyword.lower() in repo_text)
                if sub_keywords:
                    sub_scores.append(min(sub_keyword_matches / len(sub_keywords), 1.0))
            if sub_scores:
                max_score += 0.5
                score += max(sub_scores) * 0.5

        # Normalize score
        if max_score > 0:
            return score / max_score
        return 0.0

    def generate_mappings(self, min_score: float = 0.1) -> None:
        """
        Auto-generate activity-repository mappings based on analysis.

        Args:
            min_score: Minimum score threshold for including a mapping
        """
        self.load_repositories()
        commits_by_repo = self.load_git_commits_by_repo()
        self.load_manual_overrides()

        self.mappings = {}

        # Process each repository
        for repo in self.repositories:
            repo_name = repo["repo_name"]
            commits = commits_by_repo.get(repo_name, [])

            # Check each activity
            for activity in self.activities_manager.activities:
                activity_id = activity["id"]
                score = self.calculate_activity_score(activity, repo, commits)

                if score >= min_score:
                    # Add main activity mapping
                    key = (activity_id, None, repo_name)
                    self.mappings[key] = {
                        "activity_id": activity_id,
                        "sub_activity_id": None,
                        "repo_name": repo_name,
                        "rationale_nl": self._generate_rationale(activity, repo, score),
                        "confidence": self._score_to_confidence(score),
                        "auto_generated": True,
                    }

                    # Check sub-activities
                    sub_activities = activity.get("sub_activities", [])
                    for sub_activity in sub_activities:
                        sub_activity_id = sub_activity["id"]
                        sub_keywords = sub_activity.get("keywords", [])
                        repo_text = f"{repo.get('repo_description', '')} {repo.get('wbso_relevance', '')}".lower()
                        commit_text = " ".join(c.get("message", "") for c in commits).lower()
                        combined_text = f"{repo_text} {commit_text}".lower()

                        sub_matches = sum(1 for keyword in sub_keywords if keyword.lower() in combined_text)
                        if sub_keywords and sub_matches > 0:
                            sub_score = min(sub_matches / len(sub_keywords), 1.0)
                            if sub_score >= min_score:
                                key = (activity_id, sub_activity_id, repo_name)
                                self.mappings[key] = {
                                    "activity_id": activity_id,
                                    "sub_activity_id": sub_activity_id,
                                    "repo_name": repo_name,
                                    "rationale_nl": self._generate_rationale(activity, repo, sub_score, sub_activity),
                                    "confidence": self._score_to_confidence(sub_score),
                                    "auto_generated": True,
                                }

        # Apply manual overrides
        for override in self.manual_overrides:
            activity_id = override.get("activity_id")
            sub_activity_id = override.get("sub_activity_id")
            repo_name = override.get("repo_name")

            if activity_id and repo_name:
                key = (activity_id, sub_activity_id, repo_name)
                self.mappings[key] = {
                    "activity_id": activity_id,
                    "sub_activity_id": sub_activity_id,
                    "repo_name": repo_name,
                    "rationale_nl": override.get("rationale_nl", ""),
                    "confidence": override.get("confidence", "medium"),
                    "auto_generated": False,
                }

        logger.info(f"Generated {len(self.mappings)} activity-repository mappings")

    def _generate_rationale(
        self,
        activity: Dict[str, Any],
        repo: Dict[str, Any],
        score: float,
        sub_activity: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate Dutch rationale for mapping."""
        wbso_relevance = repo.get("wbso_relevance", "")
        if wbso_relevance:
            return wbso_relevance

        activity_name = activity.get("name_nl", "")
        repo_desc = repo.get("repo_description", "")

        if sub_activity:
            sub_name = sub_activity.get("name_nl", "")
            return f"{activity_name} - {sub_name}: {repo_desc}"
        return f"{activity_name}: {repo_desc}"

    def _score_to_confidence(self, score: float) -> str:
        """Convert score to confidence level."""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"

    def map_repo_to_activities(self, repo_name: str) -> List[Dict[str, Any]]:
        """
        Get all activities (and sub-activities) for a repository.

        Args:
            repo_name: Repository name

        Returns:
            List of mapping dictionaries
        """
        return [
            mapping
            for key, mapping in self.mappings.items()
            if key[2] == repo_name  # repo_name is at index 2
        ]

    def map_activity_to_repos(self, activity_id: str, sub_activity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all repositories for an activity (and optionally sub-activity).

        Args:
            activity_id: Activity ID
            sub_activity_id: Optional sub-activity ID

        Returns:
            List of mapping dictionaries
        """
        return [
            mapping
            for key, mapping in self.mappings.items()
            if key[0] == activity_id and (sub_activity_id is None or key[1] == sub_activity_id)
        ]

    def save_mappings(self) -> None:
        """Save mappings to config file."""
        self.mappings_config.parent.mkdir(parents=True, exist_ok=True)

        # Convert mappings to list format
        mappings_list = list(self.mappings.values())

        data = {
            "generated_timestamp": datetime.now().isoformat(),
            "total_mappings": len(mappings_list),
            "mappings": mappings_list,
        }

        with open(self.mappings_config, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(mappings_list)} mappings to {self.mappings_config}")

    def load_mappings(self) -> None:
        """Load mappings from config file."""
        if not self.mappings_config.exists():
            logger.info("No mappings file found, generating new mappings...")
            self.generate_mappings()
            return

        try:
            with open(self.mappings_config, "r", encoding="utf-8") as f:
                data = json.load(f)
                mappings_list = data.get("mappings", [])

            self.mappings = {}
            for mapping in mappings_list:
                key = (
                    mapping.get("activity_id"),
                    mapping.get("sub_activity_id"),
                    mapping.get("repo_name"),
                )
                if key[0] and key[2]:  # activity_id and repo_name required
                    self.mappings[key] = mapping

            logger.info(f"Loaded {len(self.mappings)} mappings from {self.mappings_config}")
        except Exception as e:
            logger.warning(f"Error loading mappings: {e}, generating new mappings...")
            self.generate_mappings()
