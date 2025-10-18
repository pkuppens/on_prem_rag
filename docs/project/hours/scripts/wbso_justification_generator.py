#!/usr/bin/env python3
"""
WBSO Justification Generator for Calendar Events

This script generates proper WBSO justifications for calendar events based on
work session data. It creates detailed R&D activity descriptions that comply
with WBSO requirements for tax deduction purposes.

TASK-035: WBSO Justification Generator for Calendar Events
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)

Author: AI Assistant
Date: 2025-01-15
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WBSOJustificationGenerator:
    """Generates WBSO-compliant justifications for calendar events."""

    def __init__(self):
        """Initialize the justification generator."""
        # WBSO project reference
        self.wbso_project = "WBSO-AICM-2025-01: AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving"

        # Detailed WBSO activity templates
        self.wbso_activity_templates = {
            "AI_FRAMEWORK": {
                "title": "AI Framework Development",
                "description": "Development and implementation of AI agent framework components including natural language processing, intent recognition, and agent communication protocols.",
                "technical_details": [
                    "Natural language processing implementation",
                    "Intent recognition algorithm development",
                    "Agent communication protocol design",
                    "AI framework architecture optimization",
                    "Machine learning model integration",
                ],
                "rd_justification": "Systematic investigation into AI agent frameworks and natural language processing techniques to create novel communication protocols for data-safe environments.",
            },
            "ACCESS_CONTROL": {
                "title": "Access Control System Development",
                "description": "Research and development of role-based access control systems, authentication mechanisms, and authorization protocols for secure AI agent communication.",
                "technical_details": [
                    "Role-based access control implementation",
                    "Authentication mechanism development",
                    "Authorization protocol design",
                    "Security token management",
                    "Permission system optimization",
                ],
                "rd_justification": "Development of novel access control mechanisms for AI agent environments, addressing technical uncertainty in secure multi-agent communication.",
            },
            "PRIVACY_CLOUD": {
                "title": "Privacy-Preserving Cloud Integration",
                "description": "Research and development of privacy-preserving techniques for cloud integration, including data anonymization, pseudonymization, and AVG compliance mechanisms.",
                "technical_details": [
                    "Data anonymization algorithm development",
                    "Pseudonymization technique implementation",
                    "AVG compliance mechanism design",
                    "Cloud data screening system",
                    "Privacy-preserving data processing",
                ],
                "rd_justification": "Systematic investigation into privacy-preserving cloud integration techniques, addressing technical challenges in data protection and regulatory compliance.",
            },
            "AUDIT_LOGGING": {
                "title": "Audit Logging System Development",
                "description": "Development of comprehensive audit logging systems for AI agent activities, ensuring traceability while maintaining privacy compliance.",
                "technical_details": [
                    "Audit log structure design",
                    "Privacy-friendly logging implementation",
                    "Traceability system development",
                    "Log analysis and monitoring",
                    "Compliance reporting automation",
                ],
                "rd_justification": "Innovation in audit logging approaches for AI systems, balancing comprehensive tracking with privacy protection requirements.",
            },
            "DATA_INTEGRITY": {
                "title": "Data Integrity Protection Systems",
                "description": "Research and development of data integrity protection mechanisms, corruption prevention systems, and data validation frameworks.",
                "technical_details": [
                    "Data integrity validation algorithms",
                    "Corruption detection systems",
                    "Data backup and recovery mechanisms",
                    "Integrity monitoring implementation",
                    "Risk operation blocking systems",
                ],
                "rd_justification": "Development of novel data integrity protection mechanisms for AI agent environments, addressing technical uncertainty in data corruption prevention.",
            },
            "GENERAL_RD": {
                "title": "General Research and Development",
                "description": "General research and development activities supporting the AI agent communication system, including system architecture, testing, and optimization.",
                "technical_details": [
                    "System architecture research",
                    "Performance optimization",
                    "Testing and validation",
                    "Documentation and analysis",
                    "Technical investigation",
                ],
                "rd_justification": "Systematic investigation and development activities supporting the overall AI agent communication system architecture and implementation.",
            },
        }

        # Repository-specific context
        self.repository_context = {
            "on_prem_rag": "On-premises RAG system for secure document processing and semantic search",
            "healthcare-aigent": "Healthcare AI agent system for medical data processing",
            "ai-agents-masterclass": "AI agents educational and research platform",
            "context_engineering": "Context engineering framework for AI systems",
            "gemini_agent": "Gemini AI agent integration and development",
            "my_chat_gpt": "ChatGPT integration and customization platform",
            "gmail_summarize_draft": "Gmail AI summarization and drafting system",
            "motivatie-brieven-ai": "AI-powered motivation letter generation system",
            "chrome_extensions": "Chrome extension development for AI integration",
            "langflow_org": "Langflow organization and workflow management",
            "genai-hackathon": "Generative AI hackathon projects and research",
            "datacation-chatbot-workspace": "Data science chatbot workspace development",
            "job_hunt": "AI-assisted job hunting and application system",
            "ChatRTX": "ChatRTX integration and optimization",
            "WBSO-AICM-2025-01": "WBSO project documentation and compliance",
        }

    def generate_calendar_event_title(self, session: Dict[str, Any]) -> str:
        """Generate a concise calendar event title."""
        category = session.get("wbso_category", "GENERAL_RD")
        template = self.wbso_activity_templates.get(category, self.wbso_activity_templates["GENERAL_RD"])

        # Get repository context if available
        repo_context = ""
        if session.get("assigned_commits"):
            repos = set(commit.get("repo_name", "") for commit in session["assigned_commits"])
            if repos:
                repo_context = f" - {', '.join(repos)}"

        return f"WBSO: {template['title']}{repo_context}"

    def generate_calendar_event_description(self, session: Dict[str, Any]) -> str:
        """Generate detailed calendar event description with WBSO justification."""
        category = session.get("wbso_category", "GENERAL_RD")
        template = self.wbso_activity_templates.get(category, self.wbso_activity_templates["GENERAL_RD"])

        # Get commit details for context
        commit_details = []
        if session.get("assigned_commits"):
            for commit in session["assigned_commits"][:3]:  # Limit to first 3 commits
                repo_name = commit.get("repo_name", "Unknown")
                message = commit.get("message", "No message")[:100]  # Truncate long messages
                commit_details.append(f"• {repo_name}: {message}")

        # Get repository context
        repo_context = ""
        if session.get("assigned_commits"):
            repos = set(commit.get("repo_name", "") for commit in session["assigned_commits"])
            repo_descriptions = []
            for repo in repos:
                if repo in self.repository_context:
                    repo_descriptions.append(f"{repo}: {self.repository_context[repo]}")
            if repo_descriptions:
                repo_context = "\n\nRepository Context:\n" + "\n".join(repo_descriptions)

        # Build description
        description = f"""WBSO Project: {self.wbso_project}

Activity: {template["title"]}
Duration: {session.get("work_hours", 0):.1f} hours
Date: {session.get("date", "Unknown")}
Session Type: {session.get("session_type", "Unknown")}

Description:
{template["description"]}

Technical Activities:
{chr(10).join(template["technical_details"])}

R&D Justification:
{template["rd_justification"]}

Commit Activities:
{chr(10).join(commit_details) if commit_details else "No specific commits recorded"}{repo_context}

WBSO Compliance:
This activity qualifies for WBSO tax deduction as it involves systematic investigation, technical uncertainty, and innovation in AI agent communication systems. The work contributes to the development of novel approaches for secure, privacy-compliant AI agent environments.

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

        return description

    def generate_calendar_events(self, work_log_file: Path) -> List[Dict[str, Any]]:
        """Generate calendar events for all WBSO-eligible work sessions."""
        logger.info(f"Loading work log from: {work_log_file}")

        with open(work_log_file, "r", encoding="utf-8") as f:
            work_log = json.load(f)

        work_sessions = work_log.get("work_sessions", [])
        wbso_sessions = [s for s in work_sessions if s.get("is_wbso", False)]

        logger.info(f"Found {len(wbso_sessions)} WBSO-eligible sessions out of {len(work_sessions)} total sessions")

        calendar_events = []

        for session in wbso_sessions:
            # Generate calendar event
            event = {
                "summary": self.generate_calendar_event_title(session),
                "description": self.generate_calendar_event_description(session),
                "start": {"dateTime": f"{session['start_time']}:00", "timeZone": "Europe/Amsterdam"},
                "end": {"dateTime": f"{session['end_time']}:00", "timeZone": "Europe/Amsterdam"},
                "colorId": "1",  # Blue color for WBSO activities
                "visibility": "private",
                "reminders": {"useDefault": False, "overrides": []},
                "extendedProperties": {
                    "private": {
                        "wbso_project": self.wbso_project,
                        "wbso_category": session.get("wbso_category", "GENERAL_RD"),
                        "session_id": session.get("session_id", ""),
                        "work_hours": str(session.get("work_hours", 0)),
                        "is_synthetic": str(session.get("is_synthetic", False)),
                        "commit_count": str(session.get("commit_count", 0)),
                    }
                },
            }

            calendar_events.append(event)

        logger.info(f"Generated {len(calendar_events)} calendar events")
        return calendar_events

    def save_calendar_events(self, events: List[Dict[str, Any]], output_file: Path) -> None:
        """Save calendar events to JSON file."""
        logger.info(f"Saving {len(events)} calendar events to: {output_file}")

        # Calculate summary statistics
        total_hours = 0
        category_stats = {}
        synthetic_count = 0
        real_count = 0

        for event in events:
            # Extract hours from extended properties
            hours = float(event["extendedProperties"]["private"].get("work_hours", 0))
            total_hours += hours

            # Count by category
            category = event["extendedProperties"]["private"].get("wbso_category", "UNKNOWN")
            if category not in category_stats:
                category_stats[category] = {"count": 0, "hours": 0.0}
            category_stats[category]["count"] += 1
            category_stats[category]["hours"] += hours

            # Count synthetic vs real
            is_synthetic = event["extendedProperties"]["private"].get("is_synthetic", "False") == "True"
            if is_synthetic:
                synthetic_count += 1
            else:
                real_count += 1

        # Create output structure
        output_data = {
            "calendar_events": events,
            "summary": {
                "total_events": len(events),
                "real_events": real_count,
                "synthetic_events": synthetic_count,
                "total_hours": total_hours,
                "category_breakdown": category_stats,
                "generation_date": datetime.now().isoformat(),
                "wbso_project": self.wbso_project,
            },
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved calendar events:")
        logger.info(f"  - Total events: {len(events)}")
        logger.info(f"  - Real events: {real_count}")
        logger.info(f"  - Synthetic events: {synthetic_count}")
        logger.info(f"  - Total hours: {total_hours:.2f}")
        logger.info(f"  - Category breakdown: {category_stats}")


def main():
    """Main function to generate WBSO calendar events."""
    # File paths
    work_log_file = Path("data/work_log_complete.json")
    output_file = Path("data/wbso_calendar_events.json")

    # Validate input file exists
    if not work_log_file.exists():
        logger.error(f"Work log file not found: {work_log_file}")
        return

    # Create generator
    generator = WBSOJustificationGenerator()

    # Generate calendar events
    calendar_events = generator.generate_calendar_events(work_log_file)

    if not calendar_events:
        logger.warning("No calendar events generated")
        return

    # Save results
    generator.save_calendar_events(calendar_events, output_file)

    logger.info("WBSO calendar events generation completed successfully")


if __name__ == "__main__":
    main()
