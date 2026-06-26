"""WebSocket connection manager for the Query Service.

Manages WebSocket connections for real-time progress reporting during
document upload and processing.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates.

    Subscribes clients to progress events, handles ping/pong for
    connection health, and cleans up on disconnection.
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def subscribe(self, websocket: WebSocket) -> None:
        """Subscribe a WebSocket connection to receive updates.

        Args:
            websocket: The WebSocket connection to subscribe.
        """
        self._connections.append(websocket)
        logger.info("WebSocket subscribed, total connections: %d", len(self._connections))

    async def unsubscribe(self, websocket: WebSocket) -> None:
        """Unsubscribe a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove.
        """
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("WebSocket unsubscribed, total connections: %d", len(self._connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all connected WebSocket clients.

        Args:
            event_type: The type of event (e.g. "progress", "pong").
            data: The event data payload.
        """
        payload = json.dumps({"type": event_type, **data})
        stale: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)

        for ws in stale:
            await self.unsubscribe(ws)

    async def handle_message(self, websocket: WebSocket, message: str) -> None:
        """Handle an incoming WebSocket message.

        Supports ping/pong for connection health checks.

        Args:
            websocket: The WebSocket connection that sent the message.
            message: The message content.
        """
        if message == "ping":
            await websocket.send_text("pong")
            return

        try:
            data = json.loads(message)
            if data.get("type") == "ping":
                response = {"type": "pong", "timestamp": data.get("timestamp")}
                await websocket.send_text(json.dumps(response))
        except json.JSONDecodeError:
            pass

    @property
    def connection_count(self) -> int:
        """Number of active WebSocket connections."""
        return len(self._connections)


# Module-level singleton
_ws_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Return the shared WebSocket manager instance."""
    return _ws_manager
