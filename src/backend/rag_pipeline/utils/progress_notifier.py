"""Progress notification system for document processing.

This module provides a pub/sub system for real-time progress updates during
document processing, using WebSockets for communication.
"""

import asyncio
import logging
from enum import Enum

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ProgressEvent:
    """Represents a progress update event."""

    def __init__(self, file_id: str, progress: int, message: str = ""):
        self.file_id = file_id
        self.progress = progress
        self.message = message
        self.timestamp = asyncio.get_event_loop().time()


class ProgressNotifier:
    """
    Observer/PubSub system for progress updates.

    This class maintains a list of WebSocket subscribers and notifies them
    of progress updates in real-time.
    """

    def __init__(self):
        # Set of active WebSocket connections that want progress updates
        self._subscribers: set[WebSocket] = set()
        # Current progress state for all uploads
        self._current_progress: dict[str, int] = {}

    async def subscribe(self, websocket: WebSocket) -> None:
        """Add a WebSocket connection to receive progress updates."""
        self._subscribers.add(websocket)
        logger.info(f"WebSocket subscribed. Total subscribers: {len(self._subscribers)}")

        # Send current progress state to new subscriber immediately
        if self._current_progress:
            active_progress = {k: v for k, v in self._current_progress.items() if v < 100}
            if active_progress:
                try:
                    await websocket.send_json({"type": "initial_state", "data": active_progress})
                except Exception as e:
                    logger.warning(f"Failed to send initial state to new subscriber: {e}")

    async def unsubscribe(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from receiving updates."""
        self._subscribers.discard(websocket)
        logger.info(f"WebSocket unsubscribed. Total subscribers: {len(self._subscribers)}")

    async def notify(self, event: ProgressEvent) -> None:
        """Notify all subscribers about a progress update."""
        # Update our internal progress state
        self._current_progress[event.file_id] = event.progress

        # Remove completed uploads from tracking after a delay
        if event.progress >= 100:
            # Keep completed files for 5 seconds so frontend can show completion
            asyncio.create_task(self._cleanup_completed(event.file_id, delay=5.0))

        # Prepare message to send to all WebSocket clients
        message = {
            "type": "progress_update",
            "file_id": event.file_id,
            "progress": event.progress,
            "message": event.message,
            "timestamp": event.timestamp,
        }

        # Send to all connected WebSocket clients
        if self._subscribers:
            # Create list of tasks to send message to all subscribers
            tasks = []
            for websocket in self._subscribers.copy():  # Copy to avoid modification during iteration
                tasks.append(self._send_to_subscriber(websocket, message))

            # Execute all sends concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_subscriber(self, websocket: WebSocket, message: dict) -> None:
        """Send message to a single WebSocket subscriber with error handling."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            # If sending fails (client disconnected, etc.), remove them from subscribers
            logger.warning(f"Failed to send to WebSocket subscriber, removing: {e}")
            await self.unsubscribe(websocket)

    async def _cleanup_completed(self, file_id: str, delay: float) -> None:
        """Remove completed file from progress tracking after a delay."""
        await asyncio.sleep(delay)
        self._current_progress.pop(file_id, None)
        logger.debug(f"Cleaned up completed file: {file_id}")


# Global progress notifier instance
progress_notifier = ProgressNotifier()
