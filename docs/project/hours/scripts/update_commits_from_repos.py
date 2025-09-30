#!/usr/bin/env python3
"""
Update Commit CSV Files from Repositories

This script reads the repositories.csv file and extracts the latest commits
from each repository, updating the corresponding CSV files.

Usage:
    python update_commits_from_repos.py [--repos-file REPOS_FILE] [--commits-dir COMMITS_DIR] [--repo-parent-dir REPO_PARENT_DIR]
"""

import argparse
import csv
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_git_command(repo_path: Path, command: List[str]) -> tuple[bool, str]:
    """Run a git command in the specified repository.

    Args:
        repo_path: Path to the git repository
        command: Git command as list of strings

    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out in {repo_path}")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Error running git command in {repo_path}: {e}")
        return False, str(e)


def extract_commits_from_repo(repo_path: Path, repo_name: str) -> List[Dict[str, str]]:
    """Extract commit data from a git repository.

    Args:
        repo_path: Path to the git repository
        repo_name: Name of the repository

    Returns:
        List of commit dictionaries
    """
    logger.info(f"Extracting commits from {repo_name}")

    # Check if it's a git repository
    if not (repo_path / ".git").exists():
        logger.warning(f"Not a git repository: {repo_path}")
        return []

    # Get all commits with the required format
    # Format: datetime|timestamp|message|author|hash
    git_command = ["log", "--pretty=format:%ad|%at|%s|%an|%H", "--date=format-local:%Y-%m-%d %H:%M:%S", "--reverse", "--all"]

    success, output = run_git_command(repo_path, git_command)
    if not success:
        logger.error(f"Failed to extract commits from {repo_name}")
        return []

    commits = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split("|", 4)  # Split into max 5 parts
        if len(parts) != 5:
            logger.warning(f"Invalid commit line format: {line}")
            continue

        commit = {"datetime": parts[0], "timestamp": parts[1], "message": parts[2], "author": parts[3], "hash": parts[4]}
        commits.append(commit)

    logger.info(f"Extracted {len(commits)} commits from {repo_name}")
    return commits


def write_commits_to_csv(commits: List[Dict[str, str]], output_file: Path) -> None:
    """Write commits to CSV file.

    Args:
        commits: List of commit dictionaries
        output_file: Output CSV file path
    """
    if not commits:
        logger.warning(f"No commits to write to {output_file}")
        return

    try:
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["datetime", "timestamp", "message", "author", "hash"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")
            writer.writeheader()
            writer.writerows(commits)

        logger.info(f"Wrote {len(commits)} commits to {output_file}")
    except Exception as e:
        logger.error(f"Error writing commits to {output_file}: {e}")


def update_commits_from_repositories(repos_file: Path, commits_dir: Path, repo_parent_dir: Path) -> None:
    """Update commit CSV files from repositories.

    Args:
        repos_file: Path to repositories.csv file
        commits_dir: Directory to store commit CSV files
        commits_dir: Parent directory containing repositories
    """
    logger.info(f"Reading repositories from: {repos_file}")
    logger.info(f"Output directory: {commits_dir}")
    logger.info(f"Repository parent directory: {repo_parent_dir}")

    if not repos_file.exists():
        logger.error(f"Repositories file not found: {repos_file}")
        return

    if not repo_parent_dir.exists():
        logger.error(f"Repository parent directory not found: {repo_parent_dir}")
        return

    # Create commits directory if it doesn't exist
    commits_dir.mkdir(parents=True, exist_ok=True)

    # Read repositories from CSV
    repositories = []
    try:
        with open(repos_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            repositories = list(reader)
    except Exception as e:
        logger.error(f"Error reading repositories file: {e}")
        return

    logger.info(f"Found {len(repositories)} repositories to process")

    processed_count = 0
    error_count = 0

    for repo in repositories:
        repo_name = repo.get("repo_name", "").strip()
        if not repo_name:
            logger.warning("Skipping repository with empty name")
            continue

        # Extract just the repository name (remove pkuppens/ prefix if present)
        if "/" in repo_name:
            repo_name = repo_name.split("/")[-1]

        logger.info(f"Processing repository: {repo_name}")

        # Check if repository directory exists
        repo_path = repo_parent_dir / repo_name
        if not repo_path.exists():
            logger.warning(f"Repository directory not found: {repo_path}")
            error_count += 1
            continue

        # Extract commits
        commits = extract_commits_from_repo(repo_path, repo_name)
        if not commits:
            logger.warning(f"No commits extracted from {repo_name}")
            error_count += 1
            continue

        # Write commits to CSV
        output_file = commits_dir / f"{repo_name}.csv"
        write_commits_to_csv(commits, output_file)
        processed_count += 1

    # Summary
    logger.info("=" * 50)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total repositories processed: {processed_count}")
    logger.info(f"Errors encountered: {error_count}")
    logger.info(f"Output files created in: {commits_dir}")


def main():
    """Main function to update commits from repositories."""
    parser = argparse.ArgumentParser(description="Update commit CSV files from repositories listed in repositories.csv")
    parser.add_argument(
        "--repos-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "repositories.csv",
        help="Path to repositories.csv file (default: docs/project/hours/data/repositories.csv)",
    )
    parser.add_argument(
        "--commits-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits",
        help="Directory to store commit CSV files (default: docs/project/hours/data/commits)",
    )
    parser.add_argument(
        "--repo-parent-dir",
        type=Path,
        default=Path("C:/Users/piete/Repos/pkuppens"),
        help="Parent directory containing repositories (default: C:/Users/piete/Repos/pkuppens)",
    )

    args = parser.parse_args()

    # Update commits from repositories
    update_commits_from_repositories(args.repos_file, args.commits_dir, args.repo_parent_dir)

    return 0


if __name__ == "__main__":
    exit(main())
