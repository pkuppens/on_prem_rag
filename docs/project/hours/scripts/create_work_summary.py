#!/usr/bin/env python3
"""
Create Work Summary Report

This script creates a comprehensive work summary from the work_log.json file,
including day count, commit count, and total work hours.

Usage:
    python create_work_summary.py [--work-log-file WORK_LOG_FILE] [--output-file OUTPUT_FILE]
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_work_summary(work_log_file: Path, output_file: Path) -> None:
    """Create work summary from work log data.

    Args:
        work_log_file: Path to work log JSON file
        output_file: Path to output summary file
    """
    logger.info(f"Creating work summary from: {work_log_file}")

    if not work_log_file.exists():
        logger.error(f"Work log file not found: {work_log_file}")
        return

    try:
        # Load work log data
        with open(work_log_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        work_log_records = data.get("work_log_records", [])
        metadata = data.get("metadata", {})

        logger.info(f"Processing {len(work_log_records)} work log records")

        # Calculate summary statistics
        total_days = metadata.get("total_days", 0)
        days_with_commits = metadata.get("days_with_commits", 0)
        total_commits = metadata.get("total_commits", 0)
        total_work_hours = metadata.get("total_work_hours", 0.0)

        # Calculate additional statistics
        avg_commits_per_day = total_commits / days_with_commits if days_with_commits > 0 else 0
        avg_work_hours_per_day = total_work_hours / days_with_commits if days_with_commits > 0 else 0
        work_efficiency = (days_with_commits / total_days) * 100 if total_days > 0 else 0

        # Analyze commits by repository
        repo_stats = {}
        for record in work_log_records:
            for commit in record.get("commits", []):
                repo_name = commit.get("repo_name", "unknown")
                if repo_name not in repo_stats:
                    repo_stats[repo_name] = {"commits": 0, "days": set()}
                repo_stats[repo_name]["commits"] += 1
                repo_stats[repo_name]["days"].add(record.get("date", ""))

        # Convert sets to counts
        for repo_name in repo_stats:
            repo_stats[repo_name]["days"] = len(repo_stats[repo_name]["days"])

        # Sort repositories by commit count
        sorted_repos = sorted(repo_stats.items(), key=lambda x: x[1]["commits"], reverse=True)

        # Create summary report
        summary = {
            "work_summary": {
                "period": {
                    "start_date": metadata.get("date_range", {}).get("start", "unknown"),
                    "end_date": metadata.get("date_range", {}).get("end", "unknown"),
                    "total_days": total_days,
                },
                "work_statistics": {
                    "days_with_commits": days_with_commits,
                    "total_commits": total_commits,
                    "total_work_hours": round(total_work_hours, 2),
                    "average_commits_per_work_day": round(avg_commits_per_day, 2),
                    "average_work_hours_per_work_day": round(avg_work_hours_per_day, 2),
                    "work_efficiency_percentage": round(work_efficiency, 1),
                },
                "repository_breakdown": {
                    repo_name: {"commits": stats["commits"], "work_days": stats["days"]} for repo_name, stats in sorted_repos
                },
                "daily_breakdown": [
                    {
                        "date": record.get("date", ""),
                        "commits": record.get("commit_count", 0),
                        "work_hours": record.get("work_hours", 0.0),
                        "repositories": list(set(commit.get("repo_name", "") for commit in record.get("commits", []))),
                    }
                    for record in work_log_records
                ],
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source_file": str(work_log_file),
                "matching_strategy": metadata.get("matching_strategy", "unknown"),
            },
        }

        # Write summary to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Print summary to console
        print("\n" + "=" * 60)
        print("WBSO WORK SUMMARY REPORT")
        print("=" * 60)
        print(f"Period: {summary['work_summary']['period']['start_date']} to {summary['work_summary']['period']['end_date']}")
        print(f"Total days in period: {total_days}")
        print(f"Days with commits: {days_with_commits}")
        print(f"Work efficiency: {work_efficiency:.1f}%")
        print()
        print("WORK STATISTICS:")
        print(f"  Total commits: {total_commits}")
        print(f"  Total work hours: {total_work_hours:.1f}")
        print(f"  Average commits per work day: {avg_commits_per_day:.1f}")
        print(f"  Average work hours per work day: {avg_work_hours_per_day:.1f}")
        print()
        print("TOP REPOSITORIES BY COMMITS:")
        for i, (repo_name, stats) in enumerate(sorted_repos[:10], 1):
            print(f"  {i:2d}. {repo_name}: {stats['commits']} commits, {stats['days']} work days")

        print(f"\nDetailed summary saved to: {output_file}")
        print("=" * 60)

        logger.info("Work summary created successfully")
        logger.info(f"Summary saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error creating work summary: {e}")


def main():
    """Main function to create work summary."""
    parser = argparse.ArgumentParser(description="Create comprehensive work summary from work log data")
    parser.add_argument(
        "--work-log-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "work_log.json",
        help="Work log JSON file (default: docs/project/hours/data/work_log.json)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "work_summary.json",
        help="Output summary JSON file (default: docs/project/hours/data/work_summary.json)",
    )

    args = parser.parse_args()

    # Create work summary
    create_work_summary(args.work_log_file, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
