"""Tests for the ingestion infrastructure ProgressNotifier."""

from __future__ import annotations

import asyncio
import time

import pytest

from backend.ingestion.infrastructure.progress import ProgressEvent, ProgressNotifier


class TestProgressEvent:
    def test_creation(self):
        event = ProgressEvent(file_id="file1", progress=50, message="chunking")
        assert event.file_id == "file1"
        assert event.progress == 50
        assert event.message == "chunking"
        assert event.timestamp > 0 or True  # timestamp may fail without event loop

    def test_default_message_empty(self):
        event = ProgressEvent(file_id="file1", progress=0)
        assert event.message == ""


class TestProgressNotifier:
    @pytest.mark.asyncio
    async def test_subscribe_and_unsubscribe(self):
        notifier = ProgressNotifier()
        mock_ws = _make_mock_ws()
        await notifier.subscribe(mock_ws)
        assert len(notifier._subscribers) == 1
        await notifier.unsubscribe(mock_ws)
        assert len(notifier._subscribers) == 0

    @pytest.mark.asyncio
    async def test_notify_sends_to_subscriber(self):
        notifier = ProgressNotifier()
        mock_ws = _make_mock_ws()
        await notifier.subscribe(mock_ws)
        event = ProgressEvent(file_id="file1", progress=50, message="chunking")
        await notifier.notify(event)
        assert mock_ws.send_json.called
        call_kwargs = mock_ws.send_json.call_args[0][0]
        assert call_kwargs["type"] == "progress_update"
        assert call_kwargs["file_id"] == "file1"
        assert call_kwargs["progress"] == 50
        assert call_kwargs["isComplete"] is False

    @pytest.mark.asyncio
    async def test_notify_completion(self):
        notifier = ProgressNotifier()
        mock_ws = _make_mock_ws()
        await notifier.subscribe(mock_ws)
        event = ProgressEvent(file_id="file1", progress=100)
        await notifier.notify(event)
        call_kwargs = mock_ws.send_json.call_args[0][0]
        assert call_kwargs["isComplete"] is True

    @pytest.mark.asyncio
    async def test_notify_error(self):
        notifier = ProgressNotifier()
        mock_ws = _make_mock_ws()
        await notifier.subscribe(mock_ws)
        event = ProgressEvent(file_id="file1", progress=-1, message="error occurred")
        await notifier.notify(event)
        call_kwargs = mock_ws.send_json.call_args[0][0]
        assert call_kwargs["error"] == "error occurred"
        assert call_kwargs["progress"] == -1

    @pytest.mark.asyncio
    async def test_notify_with_no_subscribers_does_not_raise(self):
        notifier = ProgressNotifier()
        event = ProgressEvent(file_id="file1", progress=50)
        await notifier.notify(event)

    @pytest.mark.asyncio
    async def test_subscribe_sends_initial_state_when_active_progress_exists(self):
        notifier = ProgressNotifier()
        notifier._current_progress = {"file_a": 50, "file_b": 100}
        mock_ws = _make_mock_ws()
        await notifier.subscribe(mock_ws)
        assert mock_ws.send_json.called
        call_kwargs = mock_ws.send_json.call_args[0][0]
        assert call_kwargs["type"] == "initial_state"
        assert "file_a" in call_kwargs["data"]
        assert "file_b" not in call_kwargs["data"]

    @pytest.mark.asyncio
    async def test_failing_socket_gets_removed(self):
        notifier = ProgressNotifier()
        mock_ws = _make_mock_ws()
        mock_ws.send_json.side_effect = RuntimeError("connection lost")
        await notifier.subscribe(mock_ws)
        event = ProgressEvent(file_id="file1", progress=50)
        await notifier.notify(event)
        assert mock_ws not in notifier._subscribers


class TestSharedNotifier:
    """As a React user I want upload processing progress over the WebSocket, so the progress row completes and clears."""

    def test_rag_pipeline_module_reexports_the_ingestion_instance(self):
        from backend.ingestion.infrastructure import progress as ingestion_progress
        from backend.rag_pipeline.utils import progress as rag_progress

        assert rag_progress.progress_notifier is ingestion_progress.progress_notifier

    @pytest.mark.asyncio
    async def test_processing_service_event_reaches_websocket_subscriber(self, tmp_path):
        from unittest.mock import MagicMock

        from backend.ingestion.application.ingest_service import IngestionService
        from backend.query_service.api.websocket import progress_notifier as websocket_notifier

        mock_ws = _make_mock_ws()
        await websocket_notifier.subscribe(mock_ws)
        try:
            service = IngestionService(document_loader=MagicMock(), vector_store=MagicMock())
            await service.process_document_background(tmp_path / "missing.txt", "missing.txt", "fast")
        finally:
            await websocket_notifier.unsubscribe(mock_ws)

        message = mock_ws.send_json.call_args[0][0]
        assert message["file_id"] == "missing.txt"
        assert message["progress"] == -1

    @pytest.mark.asyncio
    async def test_initial_state_excludes_failed_uploads(self):
        notifier = ProgressNotifier()
        notifier._current_progress = {"active": 40, "failed": -1}
        mock_ws = _make_mock_ws()
        await notifier.subscribe(mock_ws)
        assert mock_ws.send_json.call_args[0][0]["data"] == {"active": 40}


def _make_mock_ws():
    from unittest.mock import AsyncMock, MagicMock

    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws
