"""Tests for the Query Service adapter layer.

Covers adapters for access_control, audit, privacy_guard, retrieval, and llm.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.query_service.adapters.access_control import AccessControlAdapter
from backend.query_service.adapters.audit import AuditTrailAdapter
from backend.query_service.adapters.llm import LLMCompletionAdapter
from backend.query_service.adapters.privacy_guard import PrivacyGuardAdapter
from backend.query_service.adapters.retrieval import RetrievalAdapter


# ---------------------------------------------------------------------------
# AccessControlAdapter
# ---------------------------------------------------------------------------

class TestAccessControlAdapter:
    def test_check_permission_granted_for_gp(self):
        adapter = AccessControlAdapter()
        assert adapter.check_permission("dr_smith", "QUERY_LOCAL_LLM") is True

    def test_check_permission_denied_for_admin(self):
        adapter = AccessControlAdapter()
        assert adapter.check_permission("admin_user", "QUERY_LOCAL_LLM") is False

    def test_check_permission_unknown_permission(self):
        adapter = AccessControlAdapter()
        assert adapter.check_permission("admin_user", "UNKNOWN_PERM") is False

    def test_infer_role_patient(self):
        adapter = AccessControlAdapter()
        assert adapter._infer_role("patient_john").value == "patient"

    def test_infer_role_admin(self):
        adapter = AccessControlAdapter()
        assert adapter._infer_role("admin_bob").value == "admin"

    def test_infer_role_auditor(self):
        adapter = AccessControlAdapter()
        assert adapter._infer_role("auditor_amy").value == "auditor"

    def test_infer_role_default_gp(self):
        adapter = AccessControlAdapter()
        assert adapter._infer_role("dr_smith").value == "gp"

    def test_apply_scope_patient_adds_filter(self):
        adapter = AccessControlAdapter()
        params = adapter.apply_scope("patient_alice", "patient", {"top_k": 5})
        assert params["patient_id"] == "patient_alice"

    def test_apply_scope_gp_no_patient_filter(self):
        adapter = AccessControlAdapter()
        params = adapter.apply_scope("dr_smith", "gp", {"top_k": 5})
        assert "patient_id" not in params


# ---------------------------------------------------------------------------
# AuditTrailAdapter
# ---------------------------------------------------------------------------

class TestAuditTrailAdapter:
    def test_log_query_received_noop_without_service(self):
        adapter = AuditTrailAdapter()
        # Should not raise
        adapter.log_query_received("q1", "hello", "u1", "s1")

    def test_log_query_received_noop_without_service(self):
        adapter = AuditTrailAdapter()
        adapter.log_query_received("q1", "hello", "u1", "s1")

    def test_log_error_noop_without_service(self):
        adapter = AuditTrailAdapter()
        adapter.log_error("q1", "something failed", "retrieval")

    def test_log_retrieval_noop(self):
        adapter = AuditTrailAdapter()
        adapter.log_retrieval("q1", 3, "hybrid")

    def test_log_answer_noop(self):
        adapter = AuditTrailAdapter()
        adapter.log_answer("q1", "what?", "answer", "high")


# ---------------------------------------------------------------------------
# PrivacyGuardAdapter
# ---------------------------------------------------------------------------

class TestPrivacyGuardAdapter:
    def test_sanitize_clean_text(self):
        adapter = PrivacyGuardAdapter()
        sanitized, meta = adapter.sanitize("What is diabetes?")
        assert sanitized == "What is diabetes?"
        assert meta["pii_detected"] == 0

    def test_is_cloud_safe_clean(self):
        adapter = PrivacyGuardAdapter()
        safe, meta = adapter.is_cloud_safe("What is diabetes?")
        assert safe is True
        assert meta["pii_found"] == 0


# ---------------------------------------------------------------------------
# RetrievalAdapter
# ---------------------------------------------------------------------------

class TestRetrievalAdapter:
    def test_init_sets_config(self):
        adapter = RetrievalAdapter(strategy="dense", model_name="test-model", persist_dir="/tmp/test")
        assert adapter._config["strategy"] == "dense"
        assert adapter._config["model_name"] == "test-model"

    @patch("backend.query_service.adapters.retrieval.create_retrieval_service")
    def test_get_service_creates_service(self, mock_create):
        mock_create.return_value = "mock_service"
        adapter = RetrievalAdapter(persist_dir="/tmp/test")
        service = adapter._get_service(strategy="dense")
        assert service == "mock_service"
        mock_create.assert_called_once()
        assert mock_create.call_args[1]["strategy"] == "dense"

    @patch("backend.query_service.adapters.retrieval.create_retrieval_service")
    def test_get_service_with_strategy_override(self, mock_create):
        mock_create.return_value = "mock_service"
        adapter = RetrievalAdapter(persist_dir="/tmp/test")
        service = adapter._get_service(strategy="hybrid")
        assert service == "mock_service"
        assert mock_create.call_args[1]["strategy"] == "hybrid"

    @patch("backend.query_service.adapters.retrieval.create_retrieval_service")
    def test_retrieve_delegates(self, mock_create):
        mock_service = MagicMock()
        mock_service.retrieve.return_value = [{"text": "result"}]
        mock_create.return_value = mock_service

        adapter = RetrievalAdapter(persist_dir="/tmp/test")
        results = adapter.retrieve("test query", top_k=3)
        assert len(results) == 1
        mock_service.retrieve.assert_called_with(query="test query", top_k=3, similarity_threshold=0.0)


# ---------------------------------------------------------------------------
# LLMCompletionAdapter
# ---------------------------------------------------------------------------

class TestLLMCompletionAdapter:
    def test_generate_delegates(self):
        mock_service = MagicMock()
        mock_service.generate.return_value = "hello"
        adapter = LLMCompletionAdapter(completion_service=mock_service)
        result = adapter.generate("prompt")
        assert result == "hello"

    def test_generate_stream_delegates(self):
        mock_service = MagicMock()
        mock_service.generate_stream.return_value = iter(["hello", " world"])
        adapter = LLMCompletionAdapter(completion_service=mock_service)
        result = list(adapter.generate_stream("prompt"))
        assert result == ["hello", " world"]

    @pytest.mark.asyncio
    async def test_health_check_delegates(self):
        mock_service = AsyncMock()
        mock_service.health_check = AsyncMock(return_value=True)
        adapter = LLMCompletionAdapter(completion_service=mock_service)
        result = await adapter.health_check()
        assert result is True

    def test_provider_property(self):
        mock_service = MagicMock()
        mock_service.provider = "test_provider"
        adapter = LLMCompletionAdapter(completion_service=mock_service)
        assert adapter.provider == "test_provider"

    def test_init_with_provider(self):
        mock_provider = MagicMock()
        adapter = LLMCompletionAdapter(provider=mock_provider)
        assert adapter._service is not None

    @patch("backend.llm_gateway.infrastructure.provider_factory.get_llm_provider_from_env")
    def test_init_no_args(self, mock_get):
        mock_provider = MagicMock()
        mock_get.return_value = mock_provider
        adapter = LLMCompletionAdapter()
        assert adapter._service is not None
        mock_get.assert_called_once()
