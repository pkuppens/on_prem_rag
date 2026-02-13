#!/usr/bin/env python3
"""
Test script to simulate progress updates for file processing.

This script simulates a 10-second file processing operation with 1% progress increments
to test the progress reporting system and WebSocket functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from src.backend.rag_pipeline.utils.logging import StructuredLogger
from src.backend.rag_pipeline.utils.progress import ProgressEvent, progress_notifier

logger = StructuredLogger(__name__)


async def simulate_file_processing(filename: str = "test.pdf", duration_seconds: int = 10):
    """
    Simulate file processing with progress updates.

    Args:
        filename: Name of the file being processed
        duration_seconds: Total duration of the simulation in seconds
    """
    logger.info(f"Starting progress simulation for {filename}", filename=filename, duration=duration_seconds)

    # Calculate delay between progress updates
    # We want to go from 0% to 100% in duration_seconds
    # With 1% increments, we need 100 updates
    total_updates = 100
    delay_between_updates = duration_seconds / total_updates

    logger.info("Progress simulation parameters", total_updates=total_updates, delay_seconds=delay_between_updates)

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

        # Log the progress update
        logger.debug("Progress update sent", filename=filename, progress=progress, status_message=message)

        # Wait before next update
        await asyncio.sleep(delay_between_updates)

    # Final completion
    await progress_notifier.notify(ProgressEvent(filename, 100, "Processing completed successfully"))
    logger.info(f"Progress simulation completed for {filename}", filename=filename)


async def simulate_error_processing(filename: str = "error_test.pdf"):
    """
    Simulate a file processing error.

    Args:
        filename: Name of the file that failed
    """
    logger.info(f"Starting error simulation for {filename}", filename=filename)

    # Start processing
    await progress_notifier.notify(ProgressEvent(filename, 0, "Starting file processing"))
    await asyncio.sleep(1)

    # Some progress
    await progress_notifier.notify(ProgressEvent(filename, 25, "Processing pages"))
    await asyncio.sleep(1)

    # Error occurs
    await progress_notifier.notify(ProgressEvent(filename, -1, "Error: File format not supported"))
    logger.info(f"Error simulation completed for {filename}", filename=filename)


async def main():
    """Main function to run the progress simulation."""
    logger.info("Starting progress simulation test")

    try:
        # Simulate successful processing
        await simulate_file_processing("test.pdf", 10)

        # Wait a bit before error simulation
        await asyncio.sleep(2)

        # Simulate error processing
        await simulate_error_processing("error_test.pdf")

        logger.info("Progress simulation test completed successfully")

    except Exception as e:
        logger.error("Error during progress simulation", error=str(e))
        raise


if __name__ == "__main__":
    # Run the simulation
    asyncio.run(main())
