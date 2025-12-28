#!/usr/bin/env python3
"""
WBSO Hours Totals Calculation and Gap Analysis

This script calculates total WBSO hours from the complete work log and identifies
the gap to the 510-hour target. It provides detailed analysis of hours by category,
time period, and project distribution.

TASK-037: WBSO Hours Totals Calculation and Gap Analysis
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Created: 2025-10-18
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WBSOTotalsCalculator:
    """Calculates WBSO hours totals and analyzes gap to target."""

    def __init__(self):
        """Initialize the calculator."""
        self.target_hours = 510.0
        self.wbso_project = "WBSO-AICM-2025-01: AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving"

    def load_work_log(self, work_log_file: Path) -> Dict[str, Any]:
        """Load complete work log."""
        logger.info(f"Loading work log from: {work_log_file}")

        with open(work_log_file, "r", encoding="utf-8") as f:
            work_log = json.load(f)

        work_sessions = work_log.get("work_sessions", [])
        logger.info(f"Loaded {len(work_sessions)} work sessions")

        return work_log

    def calculate_hour_totals(self, work_log: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive hour totals and analysis."""
        work_sessions = work_log.get("work_sessions", [])

        # Basic totals
        total_sessions = len(work_sessions)
        wbso_sessions = [s for s in work_sessions if s.get("is_wbso", False)]
        non_wbso_sessions = [s for s in work_sessions if not s.get("is_wbso", False)]

        total_hours = sum(s.get("work_hours", 0) for s in work_sessions)
        wbso_hours = sum(s.get("work_hours", 0) for s in wbso_sessions)
        non_wbso_hours = sum(s.get("work_hours", 0) for s in non_wbso_sessions)

        # Gap analysis
        gap_to_target = self.target_hours - wbso_hours
        target_percentage = (wbso_hours / self.target_hours * 100) if self.target_hours > 0 else 0

        # Real vs synthetic breakdown
        real_sessions = [s for s in wbso_sessions if not s.get("is_synthetic", False)]
        synthetic_sessions = [s for s in wbso_sessions if s.get("is_synthetic", False)]

        real_hours = sum(s.get("work_hours", 0) for s in real_sessions)
        synthetic_hours = sum(s.get("work_hours", 0) for s in synthetic_sessions)

        # WBSO category breakdown
        category_stats = defaultdict(lambda: {"count": 0, "hours": 0.0, "sessions": []})
        for session in wbso_sessions:
            category = session.get("wbso_category", "UNKNOWN")
            category_stats[category]["count"] += 1
            category_stats[category]["hours"] += session.get("work_hours", 0)
            category_stats[category]["sessions"].append(session)

        # Time period analysis
        monthly_stats = defaultdict(lambda: {"count": 0, "hours": 0.0, "sessions": []})
        weekly_stats = defaultdict(lambda: {"count": 0, "hours": 0.0, "sessions": []})

        for session in wbso_sessions:
            date_str = session.get("date", "")
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    month_key = date_obj.strftime("%Y-%m")
                    week_key = f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"

                    monthly_stats[month_key]["count"] += 1
                    monthly_stats[month_key]["hours"] += session.get("work_hours", 0)
                    monthly_stats[month_key]["sessions"].append(session)

                    weekly_stats[week_key]["count"] += 1
                    weekly_stats[week_key]["hours"] += session.get("work_hours", 0)
                    weekly_stats[week_key]["sessions"].append(session)
                except ValueError:
                    logger.warning(f"Invalid date format: {date_str}")

        # Repository analysis
        repo_stats = defaultdict(lambda: {"count": 0, "hours": 0.0, "sessions": []})
        for session in wbso_sessions:
            if session.get("assigned_commits"):
                repos = set(commit.get("repo_name", "Unknown") for commit in session["assigned_commits"])
                for repo in repos:
                    repo_stats[repo]["count"] += 1
                    repo_stats[repo]["hours"] += session.get("work_hours", 0) / len(repos)  # Distribute hours across repos
                    repo_stats[repo]["sessions"].append(session)
            else:
                repo_stats["No commits"]["count"] += 1
                repo_stats["No commits"]["hours"] += session.get("work_hours", 0)
                repo_stats["No commits"]["sessions"].append(session)

        # Session type analysis
        session_type_stats = defaultdict(lambda: {"count": 0, "hours": 0.0, "sessions": []})
        for session in wbso_sessions:
            session_type = session.get("session_type", "unknown")
            session_type_stats[session_type]["count"] += 1
            session_type_stats[session_type]["hours"] += session.get("work_hours", 0)
            session_type_stats[session_type]["sessions"].append(session)

        return {
            "basic_totals": {
                "total_sessions": total_sessions,
                "wbso_sessions": len(wbso_sessions),
                "non_wbso_sessions": len(non_wbso_sessions),
                "total_hours": total_hours,
                "wbso_hours": wbso_hours,
                "non_wbso_hours": non_wbso_hours,
                "wbso_percentage": (wbso_hours / total_hours * 100) if total_hours > 0 else 0,
            },
            "gap_analysis": {
                "target_hours": self.target_hours,
                "current_hours": wbso_hours,
                "gap_hours": gap_to_target,
                "target_percentage": target_percentage,
                "achievement_status": "ACHIEVED" if gap_to_target <= 0 else "IN_PROGRESS",
            },
            "source_breakdown": {
                "real_sessions": len(real_sessions),
                "synthetic_sessions": len(synthetic_sessions),
                "real_hours": real_hours,
                "synthetic_hours": synthetic_hours,
                "real_percentage": (real_hours / wbso_hours * 100) if wbso_hours > 0 else 0,
                "synthetic_percentage": (synthetic_hours / wbso_hours * 100) if wbso_hours > 0 else 0,
            },
            "category_breakdown": dict(category_stats),
            "monthly_breakdown": dict(monthly_stats),
            "weekly_breakdown": dict(weekly_stats),
            "repository_breakdown": dict(repo_stats),
            "session_type_breakdown": dict(session_type_stats),
        }

    def generate_friday_work_plan(self, gap_hours: float) -> Dict[str, Any]:
        """Generate Friday work plan to reach target."""
        # Calculate remaining weeks in 2025
        current_date = datetime.now()
        end_of_year = datetime(2025, 12, 31)
        remaining_weeks = max(0, (end_of_year - current_date).days // 7)

        # Friday availability scenarios
        scenarios = {
            "minimum": {"hours_per_friday": 4, "description": "4 hours per Friday"},
            "moderate": {"hours_per_friday": 6, "description": "6 hours per Friday"},
            "maximum": {"hours_per_friday": 8, "description": "8 hours per Friday"},
            "extended": {"hours_per_friday": 12, "description": "12 hours per Friday"},
        }

        friday_plans = {}

        for scenario_name, scenario in scenarios.items():
            hours_per_friday = scenario["hours_per_friday"]
            weeks_needed = gap_hours / hours_per_friday if hours_per_friday > 0 else float("inf")

            friday_plans[scenario_name] = {
                "hours_per_friday": hours_per_friday,
                "description": scenario["description"],
                "weeks_needed": weeks_needed,
                "weeks_available": remaining_weeks,
                "feasible": weeks_needed <= remaining_weeks,
                "completion_date": (current_date + timedelta(weeks=weeks_needed)).strftime("%Y-%m-%d")
                if weeks_needed != float("inf")
                else "Never",
                "total_friday_hours": hours_per_friday * remaining_weeks,
            }

        return {
            "gap_hours": gap_hours,
            "remaining_weeks_2025": remaining_weeks,
            "scenarios": friday_plans,
            "recommendation": self._get_friday_recommendation(friday_plans, gap_hours),
        }

    def _get_friday_recommendation(self, friday_plans: Dict[str, Any], gap_hours: float) -> str:
        """Get recommendation for Friday work plan."""
        if gap_hours <= 0:
            return "Target already achieved! No additional Friday work needed."

        feasible_scenarios = [name for name, plan in friday_plans.items() if plan["feasible"]]

        if not feasible_scenarios:
            return f"Target not achievable with remaining {friday_plans['minimum']['weeks_available']} weeks. Consider extending into 2026 or increasing weekly hours."

        # Recommend the most efficient feasible scenario
        if "minimum" in feasible_scenarios:
            return f"Recommended: {friday_plans['minimum']['description']} for {friday_plans['minimum']['weeks_needed']:.1f} weeks to reach target."
        elif "moderate" in feasible_scenarios:
            return f"Recommended: {friday_plans['moderate']['description']} for {friday_plans['moderate']['weeks_needed']:.1f} weeks to reach target."
        else:
            return f"Recommended: {friday_plans['maximum']['description']} for {friday_plans['maximum']['weeks_needed']:.1f} weeks to reach target."

    def save_analysis_report(self, analysis: Dict[str, Any], output_file: Path) -> None:
        """Save comprehensive analysis report."""
        logger.info(f"Saving analysis report to: {output_file}")

        # Add metadata
        analysis["metadata"] = {
            "generation_date": datetime.now().isoformat(),
            "wbso_project": self.wbso_project,
            "target_hours": self.target_hours,
            "analysis_version": "1.0",
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        # Log summary
        basic_totals = analysis["basic_totals"]
        gap_analysis = analysis["gap_analysis"]
        source_breakdown = analysis["source_breakdown"]

        logger.info("Analysis Summary:")
        logger.info(f"  - Total sessions: {basic_totals['total_sessions']}")
        logger.info(f"  - WBSO sessions: {basic_totals['wbso_sessions']}")
        logger.info(f"  - Total hours: {basic_totals['total_hours']:.2f}")
        logger.info(f"  - WBSO hours: {basic_totals['wbso_hours']:.2f}")
        logger.info(f"  - Target: {gap_analysis['target_hours']}")
        logger.info(f"  - Gap: {gap_analysis['gap_hours']:.2f}")
        logger.info(f"  - Achievement: {gap_analysis['achievement_status']}")
        logger.info(f"  - Real hours: {source_breakdown['real_hours']:.2f}")
        logger.info(f"  - Synthetic hours: {source_breakdown['synthetic_hours']:.2f}")


def main():
    """Main function to calculate WBSO totals and gap analysis."""
    # File paths
    work_log_file = Path("data/work_log_complete.json")
    output_file = Path("data/wbso_totals_analysis.json")

    # Validate input file exists
    if not work_log_file.exists():
        logger.error(f"Work log file not found: {work_log_file}")
        return

    # Create calculator
    calculator = WBSOTotalsCalculator()

    # Load work log
    work_log = calculator.load_work_log(work_log_file)

    # Calculate totals
    analysis = calculator.calculate_hour_totals(work_log)

    # Generate Friday work plan
    gap_hours = analysis["gap_analysis"]["gap_hours"]
    friday_plan = calculator.generate_friday_work_plan(gap_hours)
    analysis["friday_work_plan"] = friday_plan

    # Save analysis
    calculator.save_analysis_report(analysis, output_file)

    logger.info("WBSO totals calculation and gap analysis completed successfully")


if __name__ == "__main__":
    main()
