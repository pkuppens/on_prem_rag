"""Utilities for broadcasting progress updates.

These helpers implement a very small observer pattern so that processing
functions can emit ``ProgressEvent`` objects without knowing whether any
WebSocket clients are connected. The :class:`ProgressNotifier` keeps track
of subscribed ``WebSocket`` connections and forwards each event to them.
"""

import asyncio

from fastapi import WebSocket

from .logging import StructuredLogger

logger = StructuredLogger(__name__)


class ProgressEvent:
    """Represents a progress update event.

    Attributes:
        file_id: Identifier for the file being processed
        progress: Progress percentage (0-100, or -1 for error)
        message: Optional status message
        timestamp: When the event was created
    """

    def __init__(self, file_id: str, progress: int, message: str = ""):
        """Initialize a progress event.

        Args:
            file_id: Identifier for the file being processed
            progress: Progress percentage (0-100, or -1 for error)
            message: Optional status message
        """
        self.file_id = file_id
        self.progress = progress
        self.message = message
        self.timestamp = asyncio.get_event_loop().time()


class ProgressNotifier:
    """Observer/PubSub system for progress updates.

    This class maintains a list of WebSocket subscribers and notifies them
    of progress updates in real-time. It also tracks the current progress
    state for all active uploads.

    Attributes:
        _subscribers: Set of active WebSocket connections
        _current_progress: Current progress state for all uploads
    """

    def __init__(self):
        """Initialize the progress notifier."""
        self._subscribers: set[WebSocket] = set()
        self._current_progress: dict[str, int] = {}

    async def subscribe(self, websocket: WebSocket) -> None:
        """Add a WebSocket connection to receive progress updates.

        Args:
            websocket: The WebSocket connection to subscribe
        """
        self._subscribers.add(websocket)
        logger.info(f"WebSocket subscribed. Total subscribers: {len(self._subscribers)}")

        # Send current progress state to new subscriber
        if self._current_progress:
            active_progress = {k: v for k, v in self._current_progress.items() if v < 100}
            if active_progress:
                try:
                    await websocket.send_json({"type": "initial_state", "data": active_progress})
                except Exception as e:
                    logger.warning(f"Failed to send initial state to new subscriber: {e}")

    async def unsubscribe(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from receiving updates.

        Args:
            websocket: The WebSocket connection to unsubscribe
        """
        self._subscribers.discard(websocket)
        logger.info(f"WebSocket unsubscribed. Total subscribers: {len(self._subscribers)}")

    async def notify(self, event: ProgressEvent) -> None:
        """Notify all subscribers about a progress update.

        Args:
            event: The progress event to broadcast
        """
        # Update internal progress state
        self._current_progress[event.file_id] = event.progress

        # Remove completed uploads from tracking after a delay
        if event.progress >= 100:
            asyncio.create_task(self._cleanup_completed(event.file_id, delay=5.0))

        # Prepare message for WebSocket clients
        message = {
            "type": "progress_update",
            "file_id": event.file_id,
            "progress": event.progress,
            "message": event.message,
            "timestamp": event.timestamp,
            "isComplete": event.progress >= 100,
            "error": event.message if event.progress == -1 else None,
        }

        # Send to all connected WebSocket clients
        if self._subscribers:
            tasks = []
            for websocket in self._subscribers.copy():
                tasks.append(self._send_to_subscriber(websocket, message))

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_subscriber(self, websocket: WebSocket, message: dict) -> None:
        """Send message to a single WebSocket subscriber with error handling.

        Args:
            websocket: The WebSocket connection to send to
            message: The message to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket subscriber, removing: {e}")
            await self.unsubscribe(websocket)

    async def _cleanup_completed(self, file_id: str, delay: float) -> None:
        """Remove completed file from progress tracking after a delay.

        Args:
            file_id: The file ID to clean up
            delay: Delay in seconds before cleanup
        """
        await asyncio.sleep(delay)
        self._current_progress.pop(file_id, None)
        logger.debug(f"Cleaned up completed file: {file_id}")


# Global progress notifier instance
progress_notifier = ProgressNotifier()
