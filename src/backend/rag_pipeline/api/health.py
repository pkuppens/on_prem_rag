"""Health check API endpoints for the RAG pipeline.

This module provides endpoints for checking the health and status
of the API service.
"""

from fastapi import APIRouter

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check() -> dict:
    """Check if the API service is healthy.

    Returns:
        Dict with status information
    """
    logger.info("Health check requested")
    return {"status": "ok"}
