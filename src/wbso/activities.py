#!/usr/bin/env python3
"""
WBSO Activities List Generator

Generates and manages a list of WBSO-acceptable activities in Dutch with time estimates.
This is a one-off generation that can be stored and reused unless explicitly regenerated.

Supports nested sub-activities for detailed tracking while maintaining grouping for reporting.

Author: AI Assistant
Created: 2025-11-28
Updated: 2025-11-30
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

        Activities include nested sub-activities for detailed tracking aligned with
        WBSO project phases.

        Returns:
            List of activity dictionaries with id, name_nl, keywords, estimated_hours, sub_activities
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
                "sub_activities": [
                    {
                        "id": "llm_integration",
                        "name_nl": "LLM Integratie en Model Selectie",
                        "name_en": "LLM Integration and Model Selection",
                        "keywords": ["llm", "model", "gpt", "openai", "anthropic", "claude", "local", "cloud"],
                        "description_nl": "Integratie van Large Language Models met configureerbare keuze tussen lokale en cloud-gebaseerde modellen.",
                        "estimated_hours": 85.0,
                    },
                    {
                        "id": "agent_orchestration",
                        "name_nl": "AI Agent Orkestratie",
                        "name_en": "AI Agent Orchestration",
                        "keywords": ["agent", "orchestration", "coordination", "workflow", "langflow", "autogen"],
                        "description_nl": "Ontwikkeling van agent orkestratie systemen voor gecoördineerde AI-agent workflows.",
                        "estimated_hours": 75.0,
                    },
                    {
                        "id": "prompt_engineering",
                        "name_nl": "Prompt Engineering en Jailbreak Detectie",
                        "name_en": "Prompt Engineering and Jailbreak Detection",
                        "keywords": ["prompt", "engineering", "jailbreak", "detection", "safety", "instruction"],
                        "description_nl": "Ontwikkeling van prompt engineering technieken en jailbreak detectie mechanismen.",
                        "estimated_hours": 60.0,
                    },
                ],
            },
            {
                "id": "nlp_implementation",
                "name_nl": "Natural Language Processing Implementatie",
                "name_en": "NLP Implementation",
                "keywords": ["nlp", "natural language", "text processing", "tokenization", "parsing", "semantic", "chunking"],
                "estimated_hours": 65.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Implementatie van natural language processing functionaliteit voor tekstanalyse en -verwerking.",
                "sub_activities": [
                    {
                        "id": "intent_recognition",
                        "name_nl": "Intentieherkenning en Semantische Interpretatie",
                        "name_en": "Intent Recognition and Semantic Interpretation",
                        "keywords": ["intent", "intention", "semantic", "interpretation", "understanding", "nlp"],
                        "description_nl": "Ontwikkeling van intentieherkenning en semantische interpretatie van natuurlijke taalvragen.",
                        "estimated_hours": 45.0,
                    },
                    {
                        "id": "text_processing",
                        "name_nl": "Tekstverwerking en Tokenisatie",
                        "name_en": "Text Processing and Tokenization",
                        "keywords": ["text", "processing", "tokenization", "parsing", "chunking", "preprocessing"],
                        "description_nl": "Implementatie van tekstverwerking, tokenisatie en preprocessing functionaliteit.",
                        "estimated_hours": 35.0,
                    },
                ],
            },
            {
                "id": "vector_store_development",
                "name_nl": "Vector Store Ontwikkeling",
                "name_en": "Vector Store Development",
                "keywords": ["vector", "embedding", "chroma", "pinecone", "weaviate", "qdrant", "similarity", "search"],
                "estimated_hours": 55.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Ontwikkeling en optimalisatie van vector database systemen voor semantische zoekfunctionaliteit.",
                "sub_activities": [
                    {
                        "id": "vector_database",
                        "name_nl": "Vector Database Implementatie",
                        "name_en": "Vector Database Implementation",
                        "keywords": ["vector", "embedding", "chroma", "database", "similarity"],
                        "description_nl": "Implementatie en optimalisatie van vector database systemen.",
                        "estimated_hours": 55.0,
                    },
                ],
            },
            {
                "id": "rag_pipeline_development",
                "name_nl": "RAG Pipeline Ontwikkeling",
                "name_en": "RAG Pipeline Development",
                "keywords": ["rag", "retrieval", "augmented", "generation", "pipeline", "document", "context"],
                "estimated_hours": 70.0,
                "category": "AI_FRAMEWORK",
                "description_nl": "Ontwikkeling van Retrieval-Augmented Generation pipelines voor context-aware AI responses.",
                "sub_activities": [
                    {
                        "id": "document_retrieval",
                        "name_nl": "Document Retrieval en Context Aggregatie",
                        "name_en": "Document Retrieval and Context Aggregation",
                        "keywords": ["retrieval", "document", "context", "aggregation", "search", "query"],
                        "description_nl": "Ontwikkeling van document retrieval systemen en context aggregatie voor AI responses.",
                        "estimated_hours": 50.0,
                    },
                    {
                        "id": "semantic_search",
                        "name_nl": "Semantische Zoekfunctionaliteit",
                        "name_en": "Semantic Search Functionality",
                        "keywords": ["semantic", "search", "query", "natural language", "nlp", "vector"],
                        "description_nl": "Implementatie van semantische zoekfunctionaliteit voor natuurlijke taal queries.",
                        "estimated_hours": 40.0,
                    },
                ],
            },
            {
                "id": "authentication_system",
                "name_nl": "Authenticatie Systeem Ontwikkeling",
                "name_en": "Authentication System Development",
                "keywords": ["auth", "authentication", "login", "oauth", "jwt", "token", "session", "credential"],
                "estimated_hours": 45.0,
                "category": "ACCESS_CONTROL",
                "description_nl": "Ontwikkeling van authenticatie- en autorisatiesystemen voor veilige toegangscontrole.",
                "sub_activities": [
                    {
                        "id": "user_authentication",
                        "name_nl": "Gebruikersauthenticatie en Sessiebeheer",
                        "name_en": "User Authentication and Session Management",
                        "keywords": ["auth", "authentication", "login", "session", "credential", "jwt", "token"],
                        "description_nl": "Implementatie van gebruikersauthenticatie en sessiebeheer systemen.",
                        "estimated_hours": 45.0,
                    },
                ],
            },
            {
                "id": "authorization_framework",
                "name_nl": "Autorisatie Framework Ontwikkeling",
                "name_en": "Authorization Framework Development",
                "keywords": ["authorization", "permission", "role", "rbac", "access control", "policy"],
                "estimated_hours": 40.0,
                "category": "ACCESS_CONTROL",
                "description_nl": "Ontwikkeling van autorisatieframeworks voor gedetailleerde toegangscontrole.",
                "sub_activities": [
                    {
                        "id": "role_based_access",
                        "name_nl": "Rolgebaseerde Toegangscontrole",
                        "name_en": "Role-Based Access Control",
                        "keywords": ["role", "rbac", "permission", "access control", "policy", "authorization"],
                        "description_nl": "Ontwikkeling van rolgebaseerde toegangscontrole systemen voor bevoegdheidsbeheer.",
                        "estimated_hours": 30.0,
                    },
                    {
                        "id": "context_based_access",
                        "name_nl": "Context-gebaseerde Toegangscontrole",
                        "name_en": "Context-Based Access Control",
                        "keywords": ["context", "access control", "intent", "authorization", "policy"],
                        "description_nl": "Ontwikkeling van context-gebaseerde toegangscontrole voor natuurlijke taal queries.",
                        "estimated_hours": 35.0,
                    },
                ],
            },
            {
                "id": "security_mechanisms",
                "name_nl": "Beveiligingsmechanismen Ontwikkeling",
                "name_en": "Security Mechanisms Development",
                "keywords": ["security", "encryption", "ssl", "tls", "cipher", "hash", "salt", "secure"],
                "estimated_hours": 50.0,
                "category": "ACCESS_CONTROL",
                "description_nl": "Ontwikkeling van beveiligingsmechanismen voor data-veilige omgevingen.",
                "sub_activities": [
                    {
                        "id": "encryption_security",
                        "name_nl": "Encryptie en Beveiligingsmechanismen",
                        "name_en": "Encryption and Security Mechanisms",
                        "keywords": ["encryption", "security", "ssl", "tls", "cipher", "hash"],
                        "description_nl": "Implementatie van encryptie en beveiligingsmechanismen.",
                        "estimated_hours": 50.0,
                    },
                ],
            },
            {
                "id": "privacy_preserving_cloud",
                "name_nl": "Privacy-bewuste Cloud Integratie",
                "name_en": "Privacy-preserving Cloud Integration",
                "keywords": ["cloud", "privacy", "aws", "azure", "gcp", "s3", "storage", "integration"],
                "estimated_hours": 60.0,
                "category": "PRIVACY_CLOUD",
                "description_nl": "Ontwikkeling van privacy-bewuste cloud integratieoplossingen en data protection mechanismen.",
                "sub_activities": [
                    {
                        "id": "data_anonymization",
                        "name_nl": "Data Anonimisering en Pseudonimisering",
                        "name_en": "Data Anonymization and Pseudonymization",
                        "keywords": ["anonymization", "pseudonymization", "privacy", "pii", "sensitive", "data protection"],
                        "description_nl": "Ontwikkeling van data anonimisering en pseudonimisering technieken voor veilige cloud verwerking.",
                        "estimated_hours": 45.0,
                    },
                    {
                        "id": "cloud_decision_rules",
                        "name_nl": "Cloud-waardigheid Beslisregels",
                        "name_en": "Cloud-Worthiness Decision Rules",
                        "keywords": ["cloud", "decision", "rules", "screening", "privacy", "gdpr"],
                        "description_nl": "Ontwikkeling van beslisregels voor bepaling of data veilig naar cloud gestuurd kan worden.",
                        "estimated_hours": 40.0,
                    },
                ],
            },
            {
                "id": "data_protection",
                "name_nl": "Data Bescherming Ontwikkeling",
                "name_en": "Data Protection Development",
                "keywords": ["data protection", "gdpr", "privacy", "anonymization", "pii", "sensitive"],
                "estimated_hours": 55.0,
                "category": "PRIVACY_CLOUD",
                "description_nl": "Ontwikkeling van data protection mechanismen voor privacy-bewuste applicaties.",
                "sub_activities": [
                    {
                        "id": "gdpr_compliance",
                        "name_nl": "AVG Compliance en Toestemmingsverificatie",
                        "name_en": "GDPR Compliance and Consent Verification",
                        "keywords": ["gdpr", "compliance", "consent", "verification", "privacy", "legal"],
                        "description_nl": "Implementatie van AVG compliance mechanismen en toestemmingsverificatie.",
                        "estimated_hours": 55.0,
                    },
                ],
            },
            {
                "id": "audit_logging_system",
                "name_nl": "Audit Logging Systeem Ontwikkeling",
                "name_en": "Audit Logging System Development",
                "keywords": ["audit", "logging", "log", "tracking", "monitoring", "compliance", "trail"],
                "estimated_hours": 50.0,
                "category": "AUDIT_LOGGING",
                "description_nl": "Implementatie van uitgebreide audit logging systemen voor compliance tracking.",
                "sub_activities": [
                    {
                        "id": "privacy_friendly_audit",
                        "name_nl": "Privacyvriendelijke Audit Log Structuur",
                        "name_en": "Privacy-Friendly Audit Log Structure",
                        "keywords": ["audit", "logging", "privacy", "structure", "reference", "compliance"],
                        "description_nl": "Ontwikkeling van privacyvriendelijke audit log structuren met veilige referenties zonder privacylekken.",
                        "estimated_hours": 50.0,
                    },
                ],
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
                "sub_activities": [
                    {
                        "id": "query_classification",
                        "name_nl": "Query Classificatie (Lezen/Bewerken)",
                        "name_en": "Query Classification (Read/Write)",
                        "keywords": ["query", "classification", "read", "write", "modify", "delete", "risk"],
                        "description_nl": "Ontwikkeling van classificatiemodule voor natuurlijke taal queries als alleen-lezen of bewerkend.",
                        "estimated_hours": 35.0,
                    },
                    {
                        "id": "corruption_prevention",
                        "name_nl": "Datacorruptie Preventie",
                        "name_en": "Data Corruption Prevention",
                        "keywords": ["corruption", "prevention", "integrity", "validation", "block", "risk"],
                        "description_nl": "Implementatie van mechanismen tegen datacorruptie en onbedoelde wijzigingen.",
                        "estimated_hours": 30.0,
                    },
                ],
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
                "sub_activities": [
                    {
                        "id": "backend_api",
                        "name_nl": "Backend API Ontwikkeling (FastAPI)",
                        "name_en": "Backend API Development (FastAPI)",
                        "keywords": ["api", "fastapi", "backend", "rest", "endpoint", "service"],
                        "description_nl": "Ontwikkeling van backend APIs voor systeemintegratie.",
                        "estimated_hours": 35.0,
                    },
                    {
                        "id": "frontend_integration",
                        "name_nl": "Frontend Integratie (React)",
                        "name_en": "Frontend Integration (React)",
                        "keywords": ["frontend", "react", "integration", "ui", "interface"],
                        "description_nl": "Integratie van frontend interfaces met backend APIs.",
                        "estimated_hours": 25.0,
                    },
                ],
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
                "sub_activities": [
                    {
                        "id": "system_architecture",
                        "name_nl": "Systeemarchitectuur Ontwerp",
                        "name_en": "System Architecture Design",
                        "keywords": ["architecture", "design", "structure", "pattern", "microservice"],
                        "description_nl": "Ontwerp van systeemarchitectuur voor schaalbare en onderhoudbare systemen.",
                        "estimated_hours": 50.0,
                    },
                ],
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

        # Ensure all activities have sub_activities field (backward compatibility)
        for activity in activities:
            if "sub_activities" not in activity:
                activity["sub_activities"] = []

        # Calculate total hours
        total_hours = sum(act["estimated_hours"] for act in activities)
        total_sub_activities = sum(len(act.get("sub_activities", [])) for act in activities)
        logger.info(
            f"Generated {len(activities)} WBSO activities with {total_sub_activities} sub-activities "
            f"and total {total_hours:.2f} estimated hours"
        )

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
        # Ensure backward compatibility: add empty sub_activities if missing
        for activity in self.activities:
            if "sub_activities" not in activity:
                activity["sub_activities"] = []

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

    def get_sub_activity_by_id(self, activity_id: str, sub_activity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sub-activity by activity ID and sub-activity ID.

        Args:
            activity_id: Parent activity ID
            sub_activity_id: Sub-activity ID

        Returns:
            Sub-activity dictionary or None if not found
        """
        activity = self.activity_map.get(activity_id)
        if not activity:
            return None

        sub_activities = activity.get("sub_activities", [])
        return next((sub for sub in sub_activities if sub.get("id") == sub_activity_id), None)

    def get_all_sub_activities(self) -> List[Dict[str, Any]]:
        """
        Get all sub-activities from all activities.

        Returns:
            List of all sub-activities with parent activity ID included
        """
        all_sub_activities = []
        for activity in self.activities:
            activity_id = activity.get("id")
            sub_activities = activity.get("sub_activities", [])
            for sub_activity in sub_activities:
                sub_activity_with_parent = sub_activity.copy()
                sub_activity_with_parent["parent_activity_id"] = activity_id
                sub_activity_with_parent["parent_activity_name_nl"] = activity.get("name_nl", "")
                all_sub_activities.append(sub_activity_with_parent)
        return all_sub_activities
