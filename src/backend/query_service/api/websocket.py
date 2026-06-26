"""WebSocket endpoint for progress reporting.

Same URL paths as the original rag_pipeline/api/websocket.py for backward compatibility.
Clients connect to /ws/upload-progress to receive progress events.
"""

import json

from fastapi import APIRouter, WebSocket

from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.rag_pipeline.utils.progress import progress_notifier

logger = StructuredLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/upload-progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        await progress_notifier.subscribe(websocket)

        while True:
            try:
                message = await websocket.receive_text()

                if message == "ping":
                    await websocket.send_text("pong")
                    logger.debug("Received string ping, sent string pong")
                else:
                    try:
                        json_data = json.loads(message)
                        if json_data.get("type") == "ping":
                            pong_response = {"type": "pong", "timestamp": json_data.get("timestamp")}
                            await websocket.send_text(json.dumps(pong_response))
                            logger.debug("Received JSON ping, sent JSON pong")
                        elif json_data.get("type") == "pong":
                            logger.debug("Received JSON pong response")
                        else:
                            logger.debug("Received unknown message type", message_type=json_data.get("type"))
                    except json.JSONDecodeError:
                        logger.debug("Received non-JSON message", message_content=message[:100])

            except Exception:
                break

    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        await progress_notifier.unsubscribe(websocket)
        logger.info("WebSocket connection closed")

        try:
            if hasattr(websocket, "client_state") and websocket.client_state.value != 3:
                await websocket.close()
        except Exception as e:
            logger.debug("WebSocket already closed or error during close", error=str(e))
