"""WebSocket endpoint for progress reporting.

The backend publishes :class:`~backend.rag_pipeline.utils.progress.ProgressEvent`
objects via ``progress_notifier``.  Clients connect to
``/ws/upload-progress`` to receive those events.  The connection stays alive
with a simple ``ping``/``pong`` exchange.
"""

import json

from fastapi import APIRouter, WebSocket

from ..utils.logging import StructuredLogger
from ..utils.progress import progress_notifier

logger = StructuredLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/upload-progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates.

    This endpoint:
    1. Accepts WebSocket connections
    2. Subscribes the connection to progress updates
    3. Handles ping/pong for connection health checks (supports both string and JSON)
    4. Cleans up on disconnection

    Args:
        websocket: The WebSocket connection
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        # Subscribe this WebSocket to receive progress updates
        await progress_notifier.subscribe(websocket)

        # Keep connection alive and handle ping/pong
        while True:
            try:
                # Wait for any message from client (like ping)
                message = await websocket.receive_text()

                # Handle ping/pong - support both string and JSON formats
                if message == "ping":
                    # Legacy string ping/pong
                    await websocket.send_text("pong")
                    logger.debug("Received string ping, sent string pong")
                else:
                    # Try to parse as JSON for structured ping/pong
                    try:
                        json_data = json.loads(message)
                        if json_data.get("type") == "ping":
                            # Respond to JSON ping with JSON pong
                            pong_response = {"type": "pong", "timestamp": json_data.get("timestamp")}
                            await websocket.send_text(json.dumps(pong_response))
                            logger.debug("Received JSON ping, sent JSON pong")
                        elif json_data.get("type") == "pong":
                            # Just log pong responses
                            logger.debug("Received JSON pong response")
                        else:
                            # Unknown message type, log it
                            logger.debug("Received unknown message type", message_type=json_data.get("type"))
                    except json.JSONDecodeError:
                        # Not JSON, ignore unknown string messages
                        logger.debug("Received non-JSON message", message_content=message[:100])

            except Exception:
                # Client disconnected or other error
                break

    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        # Cleanup when connection ends
        await progress_notifier.unsubscribe(websocket)
        logger.info("WebSocket connection closed")

        # Only close if not already closed - check client state more carefully
        try:
            # Check if the connection is still open before trying to close it
            if hasattr(websocket, "client_state") and websocket.client_state.value != 3:  # 3 = CLOSED
                await websocket.close()
        except Exception as e:
            # Ignore errors when trying to close an already closed connection
            logger.debug("WebSocket already closed or error during close", error=str(e))
