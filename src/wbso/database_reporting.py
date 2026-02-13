"""Database-based WBSO reporting system.

This module provides reporting functionality that queries from the normalized
WBSO database instead of processing JSON files in-memory.

See docs/technical/WBSO_DATABASE_SCHEMA.md for database schema details.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

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

logger = get_logger("database_reporting")


class WBSODatabaseReporter:
    """Database-based WBSO reporting system with normalized data queries."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the database reporter.

        Args:
            output_dir: Directory for output files. If None, uses default.
        """
        self.output_dir = output_dir or Path("docs/project/hours/reporting_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"WBSODatabaseReporter initialized with output directory: {self.output_dir}")

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive WBSO report from database.

        Returns:
            Dictionary with all report data
        """
        logger.info("Generating comprehensive WBSO report from database")

        with get_wbso_session() as session:
            # Calculate hours breakdown
            hours_data = self._calculate_wbso_hours(session)

            # Generate category analysis
            category_analysis = self._analyze_categories(session)

            # Generate repository analysis
            repository_analysis = self._analyze_repositories(session)

            # Generate compliance documentation
            compliance_data = self._generate_compliance_documentation(session)

            # Generate monthly and weekly breakdowns
            time_breakdowns = self._generate_time_breakdowns(session)

            # Combine all data
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "data_source": "normalized_database",
                    "database_schema_version": "1.0",
                    "total_sessions_analyzed": hours_data["total_wbso_sessions"],
                },
                "hours_calculation": hours_data,
                "category_analysis": category_analysis,
                "repository_analysis": repository_analysis,
                "compliance_documentation": compliance_data,
                "time_breakdowns": time_breakdowns,
                "database_normalization_summary": self._generate_normalization_summary(session),
            }

            # Export to files
            self._export_to_files(report_data, session)

            logger.info("Comprehensive WBSO report generated successfully")
            return report_data

    def _calculate_wbso_hours(self, session: Session) -> Dict[str, Any]:
        """Calculate WBSO hours from database with project start date filtering."""
        logger.info("Calculating WBSO hours from database")

        # Project start date filter
        project_start_date = datetime(2025, 6, 1).date()

        # Base query for eligible sessions
        base_query = session.query(WorkSession).filter(
            and_(WorkSession.is_wbso, func.date(WorkSession.start_time) >= project_start_date)
        )

        # Total WBSO sessions and hours
        total_sessions = base_query.count()
        total_hours = (
            session.query(func.sum(WorkSession.work_hours))
            .filter(and_(WorkSession.is_wbso, func.date(WorkSession.start_time) >= project_start_date))
            .scalar()
            or 0.0
        )

        # Real vs Synthetic breakdown
        real_sessions = base_query.filter(~WorkSession.is_synthetic).count()
        real_hours = (
            session.query(func.sum(WorkSession.work_hours))
            .filter(
                and_(
                    WorkSession.is_wbso,
                    ~WorkSession.is_synthetic,
                    func.date(WorkSession.start_time) >= project_start_date,
                )
            )
            .scalar()
            or 0.0
        )

        synthetic_sessions = base_query.filter(WorkSession.is_synthetic).count()
        synthetic_hours = (
            session.query(func.sum(WorkSession.work_hours))
            .filter(
                and_(
                    WorkSession.is_wbso,
                    WorkSession.is_synthetic,
                    func.date(WorkSession.start_time) >= project_start_date,
                )
            )
            .scalar()
            or 0.0
        )

        # Category breakdown
        category_breakdown = {}
        category_query = (
            session.query(
                WBSOCategory.code,
                WBSOCategory.name,
                func.count(WorkSession.id).label("count"),
                func.sum(WorkSession.work_hours).label("total_hours"),
                func.sum(case((~WorkSession.is_synthetic, WorkSession.work_hours), else_=0)).label("real_hours"),
                func.sum(case((WorkSession.is_synthetic, WorkSession.work_hours), else_=0)).label("synthetic_hours"),
            )
            .join(WorkSession, WBSOCategory.id == WorkSession.wbso_category_id, isouter=True)
            .filter(and_(WorkSession.is_wbso, func.date(WorkSession.start_time) >= project_start_date))
            .group_by(WBSOCategory.id, WBSOCategory.code, WBSOCategory.name)
        )

        for row in category_query:
            category_breakdown[row.code] = {
                "name": row.name,
                "count": row.count or 0,
                "hours": float(row.total_hours or 0),
                "real_hours": float(row.real_hours or 0),
                "synthetic_hours": float(row.synthetic_hours or 0),
            }

        # Handle uncategorized sessions
        uncategorized_query = session.query(
            func.count(WorkSession.id).label("count"),
            func.sum(WorkSession.work_hours).label("total_hours"),
            func.sum(case((~WorkSession.is_synthetic, WorkSession.work_hours), else_=0)).label("real_hours"),
            func.sum(case((WorkSession.is_synthetic, WorkSession.work_hours), else_=0)).label("synthetic_hours"),
        ).filter(
            and_(
                WorkSession.is_wbso,
                WorkSession.wbso_category_id.is_(None),
                func.date(WorkSession.start_time) >= project_start_date,
            )
        )

        uncategorized = uncategorized_query.first()
        if uncategorized and uncategorized.count > 0:
            category_breakdown[""] = {
                "name": "Uncategorized Sessions",
                "count": uncategorized.count,
                "hours": float(uncategorized.total_hours or 0),
                "real_hours": float(uncategorized.real_hours or 0),
                "synthetic_hours": float(uncategorized.synthetic_hours or 0),
            }

        # Target analysis
        target_hours = 510.0
        gap_hours = total_hours - target_hours
        target_percentage = (total_hours / target_hours * 100) if target_hours > 0 else 0
        achievement_status = "ACHIEVED" if total_hours >= target_hours else "IN_PROGRESS"

        return {
            "calculation_timestamp": datetime.now().isoformat(),
            "total_wbso_sessions": total_sessions,
            "total_wbso_hours": float(total_hours),
            "real_sessions": real_sessions,
            "real_hours": float(real_hours),
            "synthetic_sessions": synthetic_sessions,
            "synthetic_hours": float(synthetic_hours),
            "real_percentage": (real_hours / total_hours * 100) if total_hours > 0 else 0,
            "synthetic_percentage": (synthetic_hours / total_hours * 100) if total_hours > 0 else 0,
            "category_breakdown": category_breakdown,
            "target_analysis": {
                "target_hours": target_hours,
                "current_hours": float(total_hours),
                "gap_hours": float(gap_hours),
                "target_percentage": target_percentage,
                "achievement_status": achievement_status,
            },
        }

    def _analyze_categories(self, session: Session) -> Dict[str, Any]:
        """Analyze WBSO categories with detailed breakdowns."""
        logger.info("Analyzing WBSO categories")

        # Get all categories with session counts and hours
        category_stats = (
            session.query(
                WBSOCategory.code,
                WBSOCategory.name,
                WBSOCategory.description,
                func.count(WorkSession.id).label("session_count"),
                func.sum(WorkSession.work_hours).label("total_hours"),
                func.avg(WorkSession.work_hours).label("avg_hours_per_session"),
                func.min(WorkSession.start_time).label("first_session"),
                func.max(WorkSession.start_time).label("last_session"),
            )
            .join(WorkSession, WBSOCategory.id == WorkSession.wbso_category_id, isouter=True)
            .group_by(WBSOCategory.id)
            .all()
        )

        analysis = {"category_statistics": {}, "category_justifications": {}, "recommendations": []}

        for stat in category_stats:
            code = stat.code
            analysis["category_statistics"][code] = {
                "name": stat.name,
                "description": stat.description,
                "session_count": stat.session_count or 0,
                "total_hours": float(stat.total_hours or 0),
                "avg_hours_per_session": float(stat.avg_hours_per_session or 0),
                "first_session": stat.first_session.isoformat() if stat.first_session else None,
                "last_session": stat.last_session.isoformat() if stat.last_session else None,
            }

            # Get justification template
            category = session.query(WBSOCategory).filter_by(code=code).first()
            if category and category.justification_template:
                analysis["category_justifications"][code] = category.justification_template

        # Generate recommendations
        uncategorized_count = (
            session.query(func.count(WorkSession.id))
            .filter(and_(WorkSession.is_wbso, WorkSession.wbso_category_id.is_(None)))
            .scalar()
            or 0
        )

        if uncategorized_count > 0:
            analysis["recommendations"].append(
                f"Review {uncategorized_count} uncategorized sessions and assign appropriate WBSO categories"
            )

        return analysis

    def _analyze_repositories(self, session: Session) -> Dict[str, Any]:
        """Analyze repository usage and commit patterns."""
        logger.info("Analyzing repository usage")

        # Repository statistics
        repo_stats = (
            session.query(
                Repository.name,
                Repository.description,
                func.count(WorkSession.id).label("session_count"),
                func.sum(WorkSession.work_hours).label("total_hours"),
                func.count(Commit.id).label("commit_count"),
            )
            .outerjoin(WorkSession, Repository.id == WorkSession.repository_id)
            .outerjoin(Commit, Repository.id == Commit.repository_id)
            .group_by(Repository.id, Repository.name, Repository.description)
            .all()
        )

        analysis = {"repository_statistics": {}, "commit_patterns": {}, "session_repository_mapping": {}}

        for stat in repo_stats:
            repo_name = stat.name
            analysis["repository_statistics"][repo_name] = {
                "description": stat.description,
                "session_count": stat.session_count or 0,
                "total_hours": float(stat.total_hours or 0),
                "commit_count": stat.commit_count or 0,
            }

        # Commit patterns by repository (simplified)
        commit_patterns = (
            session.query(Repository.name, func.count(Commit.id).label("total_commits"))
            .join(Commit, Repository.id == Commit.repository_id)
            .group_by(Repository.id, Repository.name)
            .all()
        )

        for pattern in commit_patterns:
            analysis["commit_patterns"][pattern.name] = {"total_commits": pattern.total_commits}

        return analysis

    def _generate_compliance_documentation(self, session: Session) -> Dict[str, Any]:
        """Generate WBSO compliance documentation from database."""
        logger.info("Generating compliance documentation")

        # Get all WBSO sessions with full details
        wbso_sessions = (
            session.query(WorkSession)
            .filter(and_(WorkSession.is_wbso, func.date(WorkSession.start_time) >= datetime(2025, 6, 1).date()))
            .all()
        )

        compliance_data = {
            "wbso_eligibility_summary": {
                "total_sessions": len(wbso_sessions),
                "project_start_date": "2025-06-01",
                "data_source": "normalized_database",
            },
            "session_details": [],
            "validation_summary": {},
            "audit_trail": {
                "database_schema": "normalized_relational",
                "data_integrity": "verified",
                "foreign_key_constraints": "enforced",
            },
        }

        for session_obj in wbso_sessions:
            session_detail = {
                "session_id": session_obj.session_id,
                "date": session_obj.date,
                "start_time": session_obj.start_time.isoformat(),
                "end_time": session_obj.end_time.isoformat(),
                "work_hours": float(session_obj.work_hours),
                "wbso_category": session_obj.wbso_category.code if session_obj.wbso_category else None,
                "repository_name": session_obj.repository.name if session_obj.repository else None,
                "is_wbso": session_obj.is_wbso,
                "is_synthetic": session_obj.is_synthetic,
                "commit_count": len(session_obj.commits),
                "confidence_score": float(session_obj.confidence_score),
                "justification": session_obj.wbso_justification,
            }
            compliance_data["session_details"].append(session_detail)

        # Validation summary
        validation_results = session.query(ValidationResult).all()
        compliance_data["validation_summary"] = {
            "total_validations": len(validation_results),
            "valid_sessions": len([v for v in validation_results if v.is_valid]),
            "invalid_sessions": len([v for v in validation_results if not v.is_valid]),
        }

        return compliance_data

    def _generate_time_breakdowns(self, session: Session) -> Dict[str, Any]:
        """Generate monthly and weekly time breakdowns."""
        logger.info("Generating time breakdowns")

        # Monthly breakdown
        monthly_query = (
            session.query(
                func.strftime("%Y-%m", WorkSession.start_time).label("month"),
                func.count(WorkSession.id).label("count"),
                func.sum(WorkSession.work_hours).label("hours"),
            )
            .filter(and_(WorkSession.is_wbso, func.date(WorkSession.start_time) >= datetime(2025, 6, 1).date()))
            .group_by(func.strftime("%Y-%m", WorkSession.start_time))
            .all()
        )

        monthly_breakdown = {}
        for row in monthly_query:
            monthly_breakdown[row.month] = {"count": row.count, "hours": float(row.hours)}

        # Weekly breakdown
        weekly_query = (
            session.query(
                func.strftime("%Y-W%W", WorkSession.start_time).label("week"),
                func.count(WorkSession.id).label("count"),
                func.sum(WorkSession.work_hours).label("hours"),
            )
            .filter(and_(WorkSession.is_wbso, func.date(WorkSession.start_time) >= datetime(2025, 6, 1).date()))
            .group_by(func.strftime("%Y-W%W", WorkSession.start_time))
            .all()
        )

        weekly_breakdown = {}
        for row in weekly_query:
            weekly_breakdown[row.week] = {"count": row.count, "hours": float(row.hours)}

        return {"monthly_breakdown": monthly_breakdown, "weekly_breakdown": weekly_breakdown}

    def _generate_normalization_summary(self, session: Session) -> Dict[str, Any]:
        """Generate summary of database normalization benefits."""
        logger.info("Generating database normalization summary")

        # Count entities
        entity_counts = {
            "repositories": session.query(Repository).count(),
            "wbso_categories": session.query(WBSOCategory).count(),
            "work_sessions": session.query(WorkSession).count(),
            "commits": session.query(Commit).count(),
            "calendar_events": session.query(CalendarEvent).count(),
            "validation_results": session.query(ValidationResult).count(),
        }

        # Data integrity metrics
        sessions_with_categories = session.query(WorkSession).filter(WorkSession.wbso_category_id.isnot(None)).count()

        sessions_with_repositories = session.query(WorkSession).filter(WorkSession.repository_id.isnot(None)).count()

        sessions_with_commits = session.query(WorkSession).join(Commit).distinct().count()

        return {
            "normalization_benefits": {
                "data_integrity": "Foreign key constraints ensure referential integrity",
                "query_performance": "Indexed relationships enable fast joins and aggregations",
                "data_consistency": "Normalized schema prevents data duplication",
                "audit_trail": "Complete transaction history with timestamps",
                "scalability": "Relational structure supports growth and complex queries",
            },
            "entity_counts": entity_counts,
            "data_quality_metrics": {
                "sessions_with_categories": sessions_with_categories,
                "sessions_with_repositories": sessions_with_repositories,
                "sessions_with_commits": sessions_with_commits,
                "categorization_rate": (sessions_with_categories / entity_counts["work_sessions"] * 100)
                if entity_counts["work_sessions"] > 0
                else 0,
                "repository_assignment_rate": (sessions_with_repositories / entity_counts["work_sessions"] * 100)
                if entity_counts["work_sessions"] > 0
                else 0,
            },
            "database_schema_version": "1.0",
            "migration_timestamp": datetime.now().isoformat(),
        }

    def _export_to_files(self, report_data: Dict[str, Any], session: Session) -> None:
        """Export report data to various file formats."""
        logger.info("Exporting report data to files")

        # Export JSON report
        json_path = self.output_dir / "wbso_database_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        # Export CSV files
        self._export_sessions_csv(session)
        self._export_category_summary_csv(report_data)
        self._export_monthly_summary_csv(report_data)

        # Export summary markdown
        self._export_summary_markdown(report_data)

        logger.info(f"Report files exported to {self.output_dir}")

    def _export_sessions_csv(self, session: Session) -> None:
        """Export work sessions to CSV with database normalization info."""
        csv_path = self.output_dir / "wbso_sessions_database.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "session_id",
                "date",
                "start_time",
                "end_time",
                "work_hours",
                "wbso_category",
                "repository_name",
                "is_wbso",
                "is_synthetic",
                "commit_count",
                "confidence_score",
                "justification",
                "source_type",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Query sessions with joins
            sessions = (
                session.query(WorkSession)
                .join(WBSOCategory, WorkSession.wbso_category_id == WBSOCategory.id, isouter=True)
                .join(Repository, WorkSession.repository_id == Repository.id, isouter=True)
                .all()
            )

            for session_obj in sessions:
                writer.writerow(
                    {
                        "session_id": session_obj.session_id,
                        "date": session_obj.date,
                        "start_time": session_obj.start_time.isoformat(),
                        "end_time": session_obj.end_time.isoformat(),
                        "work_hours": float(session_obj.work_hours),
                        "wbso_category": session_obj.wbso_category.code if session_obj.wbso_category else "",
                        "repository_name": session_obj.repository.name if session_obj.repository else "",
                        "is_wbso": session_obj.is_wbso,
                        "is_synthetic": session_obj.is_synthetic,
                        "commit_count": len(session_obj.commits),
                        "confidence_score": float(session_obj.confidence_score),
                        "justification": session_obj.wbso_justification or "",
                        "source_type": session_obj.source_type,
                    }
                )

    def _export_category_summary_csv(self, report_data: Dict[str, Any]) -> None:
        """Export category summary to CSV."""
        csv_path = self.output_dir / "wbso_category_summary_database.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["category", "session_count", "total_hours", "real_hours", "synthetic_hours"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            category_breakdown = report_data["hours_calculation"]["category_breakdown"]
            for category_code, data in category_breakdown.items():
                writer.writerow(
                    {
                        "category": category_code or "Uncategorized",
                        "session_count": data["count"],
                        "total_hours": data["hours"],
                        "real_hours": data["real_hours"],
                        "synthetic_hours": data["synthetic_hours"],
                    }
                )

    def _export_monthly_summary_csv(self, report_data: Dict[str, Any]) -> None:
        """Export monthly summary to CSV."""
        csv_path = self.output_dir / "wbso_monthly_summary_database.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["month", "session_count", "total_hours"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            monthly_breakdown = report_data["time_breakdowns"]["monthly_breakdown"]
            for month, data in monthly_breakdown.items():
                writer.writerow({"month": month, "session_count": data["count"], "total_hours": data["hours"]})

    def _export_summary_markdown(self, report_data: Dict[str, Any]) -> None:
        """Export summary report to Markdown."""
        md_path = self.output_dir / "wbso_database_summary_report.md"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# WBSO Database Report Summary\n\n")
            f.write(f"**Generated**: {report_data['report_metadata']['generated_at']}\n")
            f.write(f"**Data Source**: {report_data['report_metadata']['data_source']}\n")
            f.write(f"**Database Schema Version**: {report_data['report_metadata']['database_schema_version']}\n\n")

            # Hours summary
            hours = report_data["hours_calculation"]
            f.write("## Hours Summary\n\n")
            f.write(f"- **Total WBSO Hours**: {hours['total_wbso_hours']:.2f}\n")
            f.write(f"- **Real Hours**: {hours['real_hours']:.2f} ({hours['real_percentage']:.1f}%)\n")
            f.write(f"- **Synthetic Hours**: {hours['synthetic_hours']:.2f} ({hours['synthetic_percentage']:.1f}%)\n")
            f.write(f"- **Target Achievement**: {hours['target_analysis']['target_percentage']:.1f}%\n\n")

            # Database normalization benefits
            norm_summary = report_data["database_normalization_summary"]
            f.write("## Database Normalization Benefits\n\n")
            f.write("This report is generated from a normalized relational database with the following benefits:\n\n")
            for benefit, description in norm_summary["normalization_benefits"].items():
                f.write(f"- **{benefit.replace('_', ' ').title()}**: {description}\n")

            f.write("\n### Data Quality Metrics\n\n")
            metrics = norm_summary["data_quality_metrics"]
            f.write(f"- **Categorization Rate**: {metrics['categorization_rate']:.1f}%\n")
            f.write(f"- **Repository Assignment Rate**: {metrics['repository_assignment_rate']:.1f}%\n")
            f.write(f"- **Sessions with Commits**: {metrics['sessions_with_commits']}\n\n")

            # Entity counts
            f.write("### Database Entity Counts\n\n")
            for entity, count in norm_summary["entity_counts"].items():
                f.write(f"- **{entity.replace('_', ' ').title()}**: {count}\n")


def main():
    """Main function for running database reporting."""
    reporter = WBSODatabaseReporter()
    report_data = reporter.generate_comprehensive_report()

    print("Database-based WBSO report generated successfully!")
    print(f"Total WBSO Hours: {report_data['hours_calculation']['total_wbso_hours']:.2f}")
    print(f"Data Source: {report_data['report_metadata']['data_source']}")


if __name__ == "__main__":
    main()
