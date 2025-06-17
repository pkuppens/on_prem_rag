"""Parameter set API endpoints for the RAG pipeline.

This module provides endpoints for retrieving available parameter sets
and their configurations.
"""

from fastapi import APIRouter

from ..config.parameter_sets import (
    DEFAULT_PARAM_SET_NAME,
    available_param_sets,
)
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/parameters", tags=["parameters"])


@router.get("/sets")
async def get_parameter_sets() -> dict:
    """Return available RAG parameter sets and default selection.

    Returns:
        Dict containing:
            - default: Name of the default parameter set
            - sets: List of available parameter set names
    """
    logger.info("GET /api/parameters/sets")
    return {"default": DEFAULT_PARAM_SET_NAME, "sets": available_param_sets()}
