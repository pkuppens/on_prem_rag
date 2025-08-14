#!/usr/bin/env python3
"""
WBSO Hours Registration - Git Commit Processing Script

This script processes git commit history to generate WBSO-compliant hours registration
for Dutch R&D tax deduction purposes.

Usage:
    python process_commits.py

Output files:
    - commit_analysis.txt: Detailed daily analysis
    - weekly_summary.txt: Weekly hours summary
    - wbso_activities.txt: WBSO activity categorization
"""

import datetime
import os
from collections import defaultdict
from pathlib import Path


def timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to datetime object."""
    return datetime.datetime.fromtimestamp(int(timestamp))


def process_commit_history(filename):
    """Process the git commit history file and group by date."""
    commits_by_date = defaultdict(list)

    if not os.path.exists(filename):
        print(f"Error: {filename} not found. Please run git log command first.")
        return commits_by_date

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse the line: date timestamp message
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                date_str, timestamp, message = parts
                try:
                    dt = timestamp_to_datetime(timestamp)
                    commits_by_date[date_str].append({"datetime": dt, "time": dt.strftime("%H:%M:%S"), "message": message})
                except ValueError:
                    print(f"Warning: Invalid timestamp in line: {line}")
                    continue

    return commits_by_date


def analyze_work_patterns(commits_by_date):
    """Analyze work patterns and suggest time ranges with realistic breaks."""
    work_sessions = []

    for date, commits in sorted(commits_by_date.items()):
        if not commits:
            continue

        # Sort commits by time
        commits.sort(key=lambda x: x["datetime"])

        # Group commits into sessions (gaps > 2 hours create new session)
        sessions = []
        current_session = [commits[0]]

        for i in range(1, len(commits)):
            time_diff = commits[i]["datetime"] - commits[i - 1]["datetime"]
            if time_diff.total_seconds() > 7200:  # 2 hours
                sessions.append(current_session)
                current_session = [commits[i]]
            else:
                current_session.append(commits[i])

        if current_session:
            sessions.append(current_session)

        # Create time ranges for each session with realistic breaks
        for session_idx, session in enumerate(sessions):
            start_time = session[0]["datetime"]
            end_time = session[-1]["datetime"]

            # Add buffer time (30 minutes before first commit, 30 minutes after last)
            start_time = start_time - datetime.timedelta(minutes=30)
            end_time = end_time + datetime.timedelta(minutes=30)

            # Ensure reasonable work hours and fix time wrapping issues
            if start_time.hour < 6:
                start_time = start_time.replace(hour=8, minute=0)
            if end_time.hour > 22:
                end_time = end_time.replace(hour=18, minute=0)

            # Handle time wrapping (end time before start time)
            if end_time < start_time:
                end_time = start_time.replace(hour=18, minute=0)

            duration_hours = (end_time - start_time).total_seconds() / 3600

            # Only include sessions with reasonable duration
            if 0.5 <= duration_hours <= 12:
                work_sessions.append(
                    {
                        "date": date,
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "duration_hours": duration_hours,
                        "commits": session,
                        "messages": [c["message"] for c in session],
                        "session_idx": session_idx,
                    }
                )

    return work_sessions


def create_wbso_task_description(messages):
    """Create WBSO-justified task descriptions based on commit messages."""
    # Keywords that indicate R&D activities
    rd_keywords = {
        "research": ["exploration", "investigation", "analysis", "research", "study", "explore"],
        "development": ["implement", "develop", "create", "build", "design", "architecture", "add", "feat"],
        "innovation": ["novel", "new", "improve", "enhance", "optimize", "refactor", "refactor"],
        "technical": ["algorithm", "model", "embedding", "chunking", "vector", "semantic", "api", "ui"],
        "testing": ["test", "validation", "verification", "quality", "debug", "fix"],
    }

    # Analyze messages for R&D content
    rd_activities = []
    for msg in messages:
        msg_lower = msg.lower()

        # Check for research activities
        if any(keyword in msg_lower for keyword in rd_keywords["research"]):
            rd_activities.append("Research and investigation of technical solutions")

        # Check for development activities
        if any(keyword in msg_lower for keyword in rd_keywords["development"]):
            rd_activities.append("Development and implementation of new features")

        # Check for innovation activities
        if any(keyword in msg_lower for keyword in rd_keywords["innovation"]):
            rd_activities.append("Innovation and optimization of system components")

        # Check for technical activities
        if any(keyword in msg_lower for keyword in rd_keywords["technical"]):
            rd_activities.append("Technical implementation and system architecture")

        # Check for testing activities
        if any(keyword in msg_lower for keyword in rd_keywords["testing"]):
            rd_activities.append("Quality assurance and testing of developed features")

    # Remove duplicates and create final description
    unique_activities = list(set(rd_activities))
    if unique_activities:
        return " - ".join(unique_activities)
    else:
        return "Research and development of on-premises RAG system components"


def add_realistic_breaks(work_sessions):
    """Add realistic lunch and dinner breaks to work sessions."""
    sessions_with_breaks = []

    for session in work_sessions:
        sessions_with_breaks.append(session)

        # Add lunch break if session ends after 12:00 and before 14:00
        end_hour = int(session["end_time"].split(":")[0])
        if 12 <= end_hour < 14:
            # Add lunch break entry
            lunch_duration = 30  # 30 minutes
            sessions_with_breaks.append(
                {
                    "date": session["date"],
                    "start_time": session["end_time"],
                    "end_time": (
                        datetime.datetime.strptime(session["end_time"], "%H:%M") + datetime.timedelta(minutes=lunch_duration)
                    ).strftime("%H:%M"),
                    "duration_hours": lunch_duration / 60,
                    "commits": [],
                    "messages": ["Lunch break"],
                    "session_idx": session["session_idx"],
                    "is_break": True,
                }
            )

        # Add dinner break if session ends after 18:00
        if end_hour >= 18:
            # Add dinner break entry
            dinner_duration = 90  # 1.5 hours
            sessions_with_breaks.append(
                {
                    "date": session["date"],
                    "start_time": session["end_time"],
                    "end_time": (
                        datetime.datetime.strptime(session["end_time"], "%H:%M") + datetime.timedelta(minutes=dinner_duration)
                    ).strftime("%H:%M"),
                    "duration_hours": dinner_duration / 60,
                    "commits": [],
                    "messages": ["Dinner break"],
                    "session_idx": session["session_idx"],
                    "is_break": True,
                }
            )

    return sessions_with_breaks


def main():
    """Main function to process commits and generate analysis."""
    script_dir = Path(__file__).parent
    git_history_file = script_dir / "git_commit_history.txt"

    print("Processing git commit history for WBSO hours registration...")

    # Process commits
    commits_by_date = process_commit_history(git_history_file)
    work_sessions = analyze_work_patterns(commits_by_date)
    sessions_with_breaks = add_realistic_breaks(work_sessions)

    # Write detailed analysis
    analysis_file = script_dir / "commit_analysis.txt"
    with open(analysis_file, "w", encoding="utf-8") as f:
        f.write("Git Commit Analysis for WBSO Hours Registration\n")
        f.write("=" * 50 + "\n\n")

        for session in sessions_with_breaks:
            f.write(f"Date: {session['date']}\n")
            f.write(f"Time: {session['start_time']} - {session['end_time']}\n")
            f.write(f"Duration: {session['duration_hours']:.1f} hours\n")

            if session.get("is_break"):
                f.write("Activity: Break\n")
            else:
                f.write("WBSO Activity: " + create_wbso_task_description(session["messages"]) + "\n")
                f.write("Commits:\n")
                for msg in session["messages"]:
                    f.write(f"  - {msg}\n")
            f.write("\n")

    # Write summary by week
    weekly_summary = defaultdict(list)
    for session in sessions_with_breaks:
        if not session.get("is_break"):  # Don't count breaks in total hours
            date_obj = datetime.datetime.strptime(session["date"], "%Y-%m-%d")
            week_num = date_obj.isocalendar()[1]
            weekly_summary[week_num].append(session)

    summary_file = script_dir / "weekly_summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("Weekly Summary for WBSO Hours Registration\n")
        f.write("=" * 40 + "\n\n")

        for week_num in sorted(weekly_summary.keys()):
            sessions = weekly_summary[week_num]
            total_hours = sum(s["duration_hours"] for s in sessions)

            f.write(f"Week {week_num}:\n")
            f.write(f"Total Hours: {total_hours:.1f}\n")
            f.write("Sessions:\n")

            for session in sessions:
                f.write(f"  {session['date']}: {session['start_time']}-{session['end_time']} ({session['duration_hours']:.1f}h)\n")
            f.write("\n")

    # Write WBSO activities summary
    wbso_file = script_dir / "wbso_activities.txt"
    with open(wbso_file, "w", encoding="utf-8") as f:
        f.write("WBSO Activity Categorization Summary\n")
        f.write("=" * 40 + "\n\n")

        activity_counts = defaultdict(int)
        for session in work_sessions:
            activity = create_wbso_task_description(session["messages"])
            activity_counts[activity] += 1

        f.write("Activity Categories and Frequency:\n")
        for activity, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {activity}: {count} sessions\n")

    print(f"Analysis complete. Files created:")
    print(f"  - {analysis_file}")
    print(f"  - {summary_file}")
    print(f"  - {wbso_file}")


if __name__ == "__main__":
    main()
