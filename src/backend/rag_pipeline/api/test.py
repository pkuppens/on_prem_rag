"""Test router for debugging progress reporting.

This module provides test endpoints to simulate document processing
and investigate progress bar behavior and UI responsiveness.
"""

import asyncio

from fastapi import APIRouter, BackgroundTasks

from ..utils.logging import StructuredLogger
from ..utils.progress import ProgressEvent, progress_notifier

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/test", tags=["test"])


async def simulate_progress_processing():
    """Simulate document processing with progress updates over 5 seconds.

    This function reports 10 progress steps over 5 seconds to test
    WebSocket progress reporting and UI responsiveness.
    """
    file_id = "progress_test.pdf"
    total_steps = 10
    step_duration = 0.5  # 5 seconds total / 10 steps

    logger.info(f"Starting progress simulation for {file_id}")

    for step in range(total_steps + 1):  # 0 to 10 inclusive
        progress = int((step / total_steps) * 100)
        message = f"Processing step {step}/{total_steps}"

        # Create and notify progress event
        event = ProgressEvent(file_id=file_id, progress=progress, message=message)

        await progress_notifier.notify(event)
        logger.debug(f"Progress update: {progress}% - {message}")

        # Wait before next step (except for the last step)
        if step < total_steps:
            await asyncio.sleep(step_duration)

    logger.info(f"Progress simulation completed for {file_id}")


@router.post("/dummy")
async def dummy_progress_test(background_tasks: BackgroundTasks):
    """Start a dummy progress test that reports 10 steps over 5 seconds.

    This endpoint simulates document processing to test progress bar
    behavior and identify potential UI blocking issues.

    Returns:
        dict: Confirmation that the test has started
    """
    logger.info("Dummy progress test requested")

    # Start the progress simulation in the background
    background_tasks.add_task(simulate_progress_processing)

    return {
        "message": "Dummy progress test started",
        "file_id": "progress_test.pdf",
        "duration": "5 seconds",
        "steps": 10,
        "status": "running",
    }
