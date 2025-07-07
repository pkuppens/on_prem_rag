#!/usr/bin/env python3
"""
Test script to verify WebSocket connection with ping-pong functionality.

This script tests the WebSocket endpoint to ensure it properly handles
both string and JSON ping-pong messages.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest
import websockets

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from src.backend.rag_pipeline.utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection with ping-pong functionality."""
    uri = "ws://localhost:8000/ws/upload-progress"

    try:
        logger.info(f"Connecting to WebSocket at {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket connected successfully")

            # Test 1: String ping/pong
            logger.info("Testing string ping/pong...")
            await websocket.send("ping")
            response = await websocket.recv()
            if response == "pong":
                logger.info("✅ String ping/pong test passed")
            else:
                logger.error(f"❌ String ping/pong test failed. Expected 'pong', got '{response}'")

            # Test 2: JSON ping/pong
            logger.info("Testing JSON ping/pong...")
            ping_message = {"type": "ping", "timestamp": 1234567890}
            await websocket.send(json.dumps(ping_message))
            response = await websocket.recv()

            try:
                response_data = json.loads(response)
                if response_data.get("type") == "pong" and response_data.get("timestamp") == 1234567890:
                    logger.info("✅ JSON ping/pong test passed")
                else:
                    logger.error(f"❌ JSON ping/pong test failed. Unexpected response: {response_data}")
            except json.JSONDecodeError:
                logger.error(f"❌ JSON ping/pong test failed. Response is not valid JSON: {response}")

            # Test 3: Send multiple pings to test connection stability
            logger.info("Testing connection stability with multiple pings...")
            for i in range(5):
                ping_message = {"type": "ping", "timestamp": i}
                await websocket.send(json.dumps(ping_message))
                response = await websocket.recv()
                logger.info(f"Ping {i + 1}/5: Response received")
                await asyncio.sleep(1)  # Wait 1 second between pings

            logger.info("✅ Connection stability test passed")

    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        logger.info("Make sure the backend server is running on localhost:8000")
        return False

    logger.info("🎉 All WebSocket tests completed successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_websocket_connection())
    sys.exit(0 if success else 1)
