#!/usr/bin/env python3
"""
WebSocket client test script to listen for progress updates.

This script connects to the backend WebSocket and displays progress updates
in real-time. Run this while the backend is running to see progress events.
"""

import asyncio
import json
import sys
from pathlib import Path

import websockets

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from src.backend.rag_pipeline.utils.logging import StructuredLogger
from src.backend.rag_pipeline.utils.progress import ProgressEvent, progress_notifier

logger = StructuredLogger(__name__)


async def websocket_client():
    """Connect to the WebSocket and listen for progress updates."""
    uri = "ws://localhost:8000/ws/upload-progress"

    try:
        logger.info(f"Connecting to WebSocket at {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket connected successfully")

            # Send a ping to keep connection alive
            await websocket.send("ping")

            # Listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Handle different message types
                    if data.get("type") == "progress_update":
                        logger.info(f"Progress Update: {data['file_id']} - {data['progress']}% - {data['message']}")
                        if data.get("isComplete"):
                            logger.info(f"✅ File {data['file_id']} completed successfully!")
                        if data.get("error"):
                            logger.error(f"❌ File {data['file_id']} failed: {data['error']}")

                    elif data.get("type") == "initial_state":
                        logger.info(f"Initial state received: {data['data']}")

                    elif data == "pong":
                        logger.debug("Received pong from server")

                    else:
                        logger.info(f"Unknown message type: {data}")

                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    break

    except Exception as e:
        logger.error(f"Failed to connect to WebSocket: {e}")
        logger.info("Make sure the backend server is running on localhost:8000")


async def simulate_progress_with_websocket():
    """Simulate progress while also running the WebSocket client."""
    logger.info("Starting combined progress simulation and WebSocket test")

    # Start WebSocket client in background
    websocket_task = asyncio.create_task(websocket_client())

    # Wait a moment for WebSocket to connect
    await asyncio.sleep(1)

    try:
        # Simulate file processing
        await simulate_file_processing("test.pdf", 10)

        # Wait for WebSocket to finish
        await asyncio.sleep(2)

    finally:
        # Cancel WebSocket task
        websocket_task.cancel()
        try:
            await websocket_task
        except asyncio.CancelledError:
            pass


async def simulate_file_processing(filename: str = "test.pdf", duration_seconds: int = 10):
    """Simulate file processing with progress updates."""
    logger.info(f"Starting progress simulation for {filename}", filename=filename, duration=duration_seconds)

    # Calculate delay between progress updates
    total_updates = 100
    delay_between_updates = duration_seconds / total_updates

    # Start with 0% progress
    await progress_notifier.notify(ProgressEvent(filename, 0, "Starting file processing"))
    await asyncio.sleep(delay_between_updates)

    # Simulate progress from 1% to 99%
    for progress in range(1, 100):
        # Create different messages based on progress ranges
        if progress < 20:
            message = f"Loading document ({progress}%)"
        elif progress < 50:
            message = f"Processing pages ({progress}%)"
        elif progress < 80:
            message = f"Generating embeddings ({progress}%)"
        elif progress < 95:
            message = f"Storing in database ({progress}%)"
        else:
            message = f"Finalizing ({progress}%)"

        # Send progress update
        await progress_notifier.notify(ProgressEvent(filename, progress, message))

        # Wait before next update
        await asyncio.sleep(delay_between_updates)

    # Final completion
    await progress_notifier.notify(ProgressEvent(filename, 100, "Processing completed successfully"))
    logger.info(f"Progress simulation completed for {filename}", filename=filename)


async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test progress reporting system")
    parser.add_argument("--mode", choices=["websocket", "simulation", "combined"], default="websocket", help="Test mode")
    parser.add_argument("--duration", type=int, default=10, help="Duration of simulation in seconds")

    args = parser.parse_args()

    if args.mode == "websocket":
        await websocket_client()
    elif args.mode == "simulation":
        await simulate_file_processing("test.pdf", args.duration)
    elif args.mode == "combined":
        await simulate_progress_with_websocket()


if __name__ == "__main__":
    asyncio.run(main())
