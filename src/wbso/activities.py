#!/usr/bin/env python3
"""
WBSO Activities List Generator

Generates and manages a list of WBSO-acceptable activities in Dutch with time estimates.
This is a one-off generation that can be stored and reused unless explicitly regenerated.

Author: AI Assistant
Created: 2025-11-28
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .logging_config import get_logger

logger = get_logger("activities")

# Default storage path
ACTIVITIES_FILE = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "config" / "wbso_activities.json"


class WBSOActivities:
    """Manages WBSO acceptable activities list with Dutch descriptions and time estimates."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize activities manager."""
        self.storage_path = storage_path or ACTIVITIES_FILE
        self.activities: List[Dict[str, Any]] = []
        self.activity_map: Dict[str, Dict[str, Any]] = {}  # activity_id -> activity

    def generate_activities_list(self) -> List[Dict[str, Any]]:
        """
        Generate comprehensive list of WBSO acceptable activities in Dutch.

        Activities are based on WBSO project scope: AI Agent Communicatie in een
        data-veilige en privacy-bewuste omgeving.

        Returns:
            List of activity dictionaries with id, name_nl, keywords, estimated_hours
        """
        activities = [
            {
                "id": "ai_framework_development",
                "name_nl": "AI Framework Ontwikkeling",
                "name_en": "AI Framework Development",
                "keywords": [
                    "ai",
                    "framework",
                    "agent",
                    "llm",
                    "gpt",
                    "openai",
                    "anthropic",
                    "model",
                    "prompt",
                    "embedding",
                    "vector",
                ],
                "estimated_hours": 85.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Ontwikkeling en implementatie van AI agent frameworks, natural language processing capabilities, en intelligente communicatiesystemen voor data-veilige omgevingen.",
            },
            {
                "id": "nlp_implementation",
                "name_nl": "Natural Language Processing Implementatie",
                "name_en": "NLP Implementation",
                "keywords": ["nlp", "natural language", "text processing", "tokenization", "parsing", "semantic", "chunking"],
                "estimated_hours": 65.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Implementatie van natural language processing functionaliteit voor tekstanalyse en -verwerking.",
            },
            {
                "id": "vector_store_development",
                "name_nl": "Vector Store Ontwikkeling",
                "name_en": "Vector Store Development",
                "keywords": ["vector", "embedding", "chroma", "pinecone", "weaviate", "qdrant", "similarity", "search"],
                "estimated_hours": 55.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Ontwikkeling en optimalisatie van vector database systemen voor semantische zoekfunctionaliteit.",
            },
            {
                "id": "rag_pipeline_development",
                "name_nl": "RAG Pipeline Ontwikkeling",
                "name_en": "RAG Pipeline Development",
                "keywords": ["rag", "retrieval", "augmented", "generation", "pipeline", "document", "context"],
                "estimated_hours": 70.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Ontwikkeling van Retrieval-Augmented Generation pipelines voor context-aware AI responses.",
            },
            {
                "id": "authentication_system",
                "name_nl": "Authenticatie Systeem Ontwikkeling",
                "name_en": "Authentication System Development",
                "keywords": ["auth", "authentication", "login", "oauth", "jwt", "token", "session", "credential"],
                "estimated_hours": 45.0,
                "category": "ACCESS_CONTROL",
                "description_nl": "Ontwikkeling van authenticatie- en autorisatiesystemen voor veilige toegangscontrole.",
            },
            {
                "id": "authorization_framework",
                "name_nl": "Autorisatie Framework Ontwikkeling",
                "name_en": "Authorization Framework Development",
                "keywords": ["authorization", "permission", "role", "rbac", "access control", "policy"],
                "estimated_hours": 40.0,
                "category": "ACCESS_CONTROL",
                "description_nl": "Ontwikkeling van autorisatieframeworks voor gedetailleerde toegangscontrole.",
            },
            {
                "id": "security_mechanisms",
                "name_nl": "Beveiligingsmechanismen Ontwikkeling",
                "name_en": "Security Mechanisms Development",
                "keywords": ["security", "encryption", "ssl", "tls", "cipher", "hash", "salt", "secure"],
                "estimated_hours": 50.0,
                "category": "ACCESS_CONTROL",
                "description_nl": "Ontwikkeling van beveiligingsmechanismen voor data-veilige omgevingen.",
            },
            {
                "id": "privacy_preserving_cloud",
                "name_nl": "Privacy-bewuste Cloud Integratie",
                "name_en": "Privacy-preserving Cloud Integration",
                "keywords": ["cloud", "privacy", "aws", "azure", "gcp", "s3", "storage", "integration"],
                "estimated_hours": 60.0,
                "category": "PRIVACY_CLOUD",
                "description_nl": "Ontwikkeling van privacy-bewuste cloud integratieoplossingen en data protection mechanismen.",
            },
            {
                "id": "data_protection",
                "name_nl": "Data Bescherming Ontwikkeling",
                "name_en": "Data Protection Development",
                "keywords": ["data protection", "gdpr", "privacy", "anonymization", "pii", "sensitive"],
                "estimated_hours": 55.0,
                "category": "PRIVACY_CLOUD",
                "description_nl": "Ontwikkeling van data protection mechanismen voor privacy-bewuste applicaties.",
            },
            {
                "id": "audit_logging_system",
                "name_nl": "Audit Logging Systeem Ontwikkeling",
                "name_en": "Audit Logging System Development",
                "keywords": ["audit", "logging", "log", "tracking", "monitoring", "compliance", "trail"],
                "estimated_hours": 50.0,
                "category": "AUDIT_LOGGING",
                "description_nl": "Implementatie van uitgebreide audit logging systemen voor compliance tracking.",
            },
            {
                "id": "monitoring_solutions",
                "name_nl": "Monitoring Oplossingen Ontwikkeling",
                "name_en": "Monitoring Solutions Development",
                "keywords": ["monitoring", "metrics", "observability", "dashboard", "alert", "health"],
                "estimated_hours": 45.0,
                "category": "AUDIT_LOGGING",
                "description_nl": "Ontwikkeling van privacy-vriendelijke monitoring oplossingen.",
            },
            {
                "id": "data_integrity_protection",
                "name_nl": "Data Integriteit Bescherming",
                "name_en": "Data Integrity Protection",
                "keywords": ["integrity", "validation", "checksum", "corruption", "verification", "consistency"],
                "estimated_hours": 50.0,
                "category": "DATA_INTEGRITY",
                "description_nl": "Onderzoek en ontwikkeling van data integriteit beschermingssystemen en corruptie preventie.",
            },
            {
                "id": "validation_frameworks",
                "name_nl": "Validatie Frameworks Ontwikkeling",
                "name_en": "Validation Frameworks Development",
                "keywords": ["validation", "validate", "schema", "constraint", "rule", "check"],
                "estimated_hours": 40.0,
                "category": "DATA_INTEGRITY",
                "description_nl": "Ontwikkeling van validatie frameworks voor data kwaliteitscontrole.",
            },
            {
                "id": "api_development",
                "name_nl": "API Ontwikkeling en Integratie",
                "name_en": "API Development and Integration",
                "keywords": ["api", "rest", "graphql", "endpoint", "service", "integration", "client"],
                "estimated_hours": 50.0,
                "category": "GENERAL_RD",
                "description_nl": "Ontwikkeling van APIs voor integratie met externe systemen en services.",
            },
            {
                "id": "database_development",
                "name_nl": "Database Ontwikkeling en Optimalisatie",
                "name_en": "Database Development and Optimization",
                "keywords": ["database", "db", "sql", "query", "index", "optimization", "schema"],
                "estimated_hours": 45.0,
                "category": "GENERAL_RD",
                "description_nl": "Database ontwikkeling en optimalisatie voor performante data opslag.",
            },
            {
                "id": "testing_framework",
                "name_nl": "Test Framework Ontwikkeling",
                "name_en": "Testing Framework Development",
                "keywords": ["test", "testing", "pytest", "unit", "integration", "fixture", "mock"],
                "estimated_hours": 40.0,
                "category": "GENERAL_RD",
                "description_nl": "Ontwikkeling van test frameworks en test infrastructuur.",
            },
            {
                "id": "documentation_development",
                "name_nl": "Technische Documentatie Ontwikkeling",
                "name_en": "Technical Documentation Development",
                "keywords": ["documentation", "doc", "readme", "guide", "manual", "specification"],
                "estimated_hours": 35.0,
                "category": "GENERAL_RD",
                "description_nl": "Ontwikkeling van technische documentatie en specificaties.",
            },
            {
                "id": "architecture_design",
                "name_nl": "Architectuur Ontwerp en Planning",
                "name_en": "Architecture Design and Planning",
                "keywords": ["architecture", "design", "planning", "structure", "pattern", "diagram"],
                "estimated_hours": 50.0,
                "category": "GENERAL_RD",
                "description_nl": "Architectuur ontwerp en planning voor schaalbare systemen.",
            },
            {
                "id": "performance_optimization",
                "name_nl": "Performance Optimalisatie",
                "name_en": "Performance Optimization",
                "keywords": ["performance", "optimization", "optimize", "speed", "efficiency", "cache"],
                "estimated_hours": 45.0,
                "category": "GENERAL_RD",
                "description_nl": "Performance optimalisatie en efficiency verbetering van systemen.",
            },
            {
                "id": "deployment_automation",
                "name_nl": "Deployment Automatisering",
                "name_en": "Deployment Automation",
                "keywords": ["deployment", "deploy", "ci", "cd", "pipeline", "docker", "kubernetes"],
                "estimated_hours": 40.0,
                "category": "GENERAL_RD",
                "description_nl": "Automatisering van deployment processen en CI/CD pipelines.",
            },
            {
                "id": "research_analysis",
                "name_nl": "Onderzoek en Analyse",
                "name_en": "Research and Analysis",
                "keywords": ["research", "analysis", "study", "investigation", "evaluation", "comparison"],
                "estimated_hours": 50.0,
                "category": "GENERAL_RD",
                "description_nl": "Onderzoek en analyse van technische oplossingen en best practices.",
            },
        ]

        # Calculate total hours
        total_hours = sum(act["estimated_hours"] for act in activities)
        logger.info(f"Generated {len(activities)} WBSO activities with total {total_hours:.2f} estimated hours")

        return activities

    def load_activities(self, force_regenerate: bool = False) -> None:
        """
        Load activities from storage or generate if not exists.

        Args:
            force_regenerate: If True, regenerate activities even if file exists
        """
        if force_regenerate or not self.storage_path.exists():
            logger.info("Generating WBSO activities list...")
            self.activities = self.generate_activities_list()
            self._build_activity_map()
            self._save_activities()
        else:
            logger.info(f"Loading WBSO activities from {self.storage_path}")
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.activities = data.get("activities", [])
                    self._build_activity_map()
                logger.info(f"Loaded {len(self.activities)} activities")
            except Exception as e:
                logger.warning(f"Failed to load activities: {e}, regenerating...")
                self.activities = self.generate_activities_list()
                self._build_activity_map()
                self._save_activities()

    def _build_activity_map(self) -> None:
        """Build activity map for quick lookup."""
        self.activity_map = {act["id"]: act for act in self.activities}

    def _save_activities(self) -> None:
        """Save activities to storage file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "generated_timestamp": datetime.now().isoformat(),
            "total_activities": len(self.activities),
            "total_estimated_hours": sum(act["estimated_hours"] for act in self.activities),
            "activities": self.activities,
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.activities)} activities to {self.storage_path}")

    def find_activity_by_commits(
        self, commit_messages: List[str], previous_activity_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find most relevant activity based on commit messages.

        Args:
            commit_messages: List of commit message strings
            previous_activity_id: Previous activity ID to use as fallback

        Returns:
            Activity dictionary or None if no match found
        """
        if not commit_messages:
            # Fallback to previous activity
            if previous_activity_id and previous_activity_id in self.activity_map:
                return self.activity_map[previous_activity_id]
            return None

        # Combine all commit messages into searchable text
        search_text = " ".join(commit_messages).lower()

        # Score each activity based on keyword matches
        activity_scores = []
        for activity in self.activities:
            score = 0
            keywords = activity.get("keywords", [])

            # Count keyword matches
            for keyword in keywords:
                if keyword.lower() in search_text:
                    score += 1

            if score > 0:
                activity_scores.append((score, activity))

        # Return highest scoring activity
        if activity_scores:
            activity_scores.sort(key=lambda x: x[0], reverse=True)
            return activity_scores[0][1]

        # Fallback to previous activity
        if previous_activity_id and previous_activity_id in self.activity_map:
            return self.activity_map[previous_activity_id]

        # Final fallback: return first general R&D activity
        general_rd = next((act for act in self.activities if act["category"] == "GENERAL_RD"), None)
        return general_rd

    def get_activity_name_nl(self, activity_id: str) -> str:
        """Get Dutch activity name by ID."""
        if activity_id in self.activity_map:
            return self.activity_map[activity_id]["name_nl"]
        return "Algemeen R&D Werk"

    def get_total_estimated_hours(self) -> float:
        """Get total estimated hours across all activities."""
        return sum(act["estimated_hours"] for act in self.activities)
