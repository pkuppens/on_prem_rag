"""WebSocket API endpoints for the RAG pipeline.

This module provides WebSocket endpoints for real-time progress updates
during document processing.
"""

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
    3. Handles ping/pong for connection health checks
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

                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text("pong")
                    logger.debug("Received ping, sent pong")
            except Exception:
                # Client disconnected or other error
                break

    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        # Cleanup when connection ends
        await progress_notifier.unsubscribe(websocket)
        logger.info("WebSocket connection closed")

        # Only close if not already closed
        try:
            if websocket.client_state.value != 3:  # 3 = CLOSED
                await websocket.close()
        except Exception as e:
            logger.debug("WebSocket already closed or error during close", error=str(e))
