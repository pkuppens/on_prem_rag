"""Locust load test for the RAG backend.

Covers POST /api/ask, POST /api/query, and GET /api/health.

Prerequisites:
    pip install locust          # or: uv add --dev locust

Quick run (headless, 5 users, 30 s):
    locust -f scripts/load/locustfile.py \\
        --host=http://localhost:9180 \\
        --users 5 --spawn-rate 1 --run-time 30s --headless

Interactive UI (opens browser at http://localhost:8089):
    locust -f scripts/load/locustfile.py --host=http://localhost:9180

Override host via env:
    BACKEND_URL=http://my-server:9180 locust -f scripts/load/locustfile.py ...

SLOs (Service-Level Objectives)
--------------------------------
- POST /api/ask   : p95 < 15 000 ms, error rate < 5 %  (LLM inference included)
- POST /api/query : p95 <  2 000 ms, error rate < 1 %  (retrieval-only)
- GET  /api/health: p95 <    500 ms, error rate < 1 %
"""

import os
import random

from locust import HttpUser, between, task

# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------
_ASK_QUESTIONS = [
    "What is the main topic of the documents?",
    "Summarise the key findings.",
    "What recommendations are made?",
    "Are there any risks mentioned?",
    "What conclusions can be drawn?",
]

_QUERY_TEXTS = [
    "treatment guidelines",
    "diagnostic criteria",
    "patient safety",
    "evidence-based recommendations",
    "clinical outcomes",
]

_BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:9180")


# ---------------------------------------------------------------------------
# Locust user definition
# ---------------------------------------------------------------------------
class RAGUser(HttpUser):
    """Simulates a user interacting with the RAG backend.

    Task weight ratio (approximate):
        health : query : ask = 3 : 2 : 1
    This reflects realistic usage where health checks are frequent and
    LLM-backed asks are relatively rare.
    """

    host = _BACKEND_URL
    wait_time = between(1, 3)  # seconds between tasks

    @task(3)
    def health_check(self) -> None:
        """GET /api/health — lightweight liveness probe."""
        self.client.get("/api/health", name="GET /api/health")

    @task(2)
    def query_documents(self) -> None:
        """POST /api/query — retrieval-only, no LLM inference."""
        self.client.post(
            "/api/query",
            json={"query": random.choice(_QUERY_TEXTS), "top_k": 5},
            name="POST /api/query",
        )

    @task(1)
    def ask_question(self) -> None:
        """POST /api/ask — full RAG pipeline with LLM answer generation."""
        self.client.post(
            "/api/ask",
            json={
                "question": random.choice(_ASK_QUESTIONS),
                "top_k": 5,
                "similarity_threshold": 0.7,
            },
            name="POST /api/ask",
        )
