"""Tests for the AuditLogMiddleware.

As a compliance officer, I want every API request logged with caller identity and
outcome so that access can be reconstructed from logs alone.
"""

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.rag_pipeline.api.middleware.audit_log import AuditLogMiddleware


@pytest.fixture()
def audit_app():
    """Minimal FastAPI app with AuditLogMiddleware for isolated testing."""
    app = FastAPI()
    app.add_middleware(AuditLogMiddleware)

    @app.get("/ping")
    def ping():
        return {"pong": True}

    return app


def test_audit_log_records_method_path_status(audit_app, caplog) -> None:
    """Audit middleware must log method, path, and status code for every request."""
    with caplog.at_level(logging.INFO, logger="audit"):
        client = TestClient(audit_app)
        client.get("/ping")

    assert any(
        "method=GET" in r.message and "path=/ping" in r.message and "status=200" in r.message
        for r in caplog.records
    ), f"Expected audit log entry not found in: {[r.message for r in caplog.records]}"


def test_audit_log_anonymous_without_token(audit_app, caplog) -> None:
    """Requests without Authorization header must be logged as anonymous."""
    with caplog.at_level(logging.INFO, logger="audit"):
        client = TestClient(audit_app)
        client.get("/ping")

    assert any("token=anonymous" in r.message for r in caplog.records)


def test_audit_log_truncates_bearer_token(audit_app, caplog) -> None:
    """Bearer token must appear truncated (8 chars + ellipsis) in the log — never the full credential."""
    token = "abcdefghijklmnopqrstuvwxyz"
    with caplog.at_level(logging.INFO, logger="audit"):
        client = TestClient(audit_app)
        client.get("/ping", headers={"Authorization": f"Bearer {token}"})

    log_messages = [r.message for r in caplog.records]
    assert any("token=abcdefgh\u2026" in m for m in log_messages), f"Truncated token hint not found: {log_messages}"
    assert not any(token in m for m in log_messages), "Full token must never appear in audit log"
