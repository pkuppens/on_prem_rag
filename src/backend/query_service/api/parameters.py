"""Parameter set API endpoints for the Query Service.

Same URL paths as the original rag_pipeline/api/parameters.py for backward compatibility.
"""

from fastapi import APIRouter

from backend.rag_pipeline.config.parameter_sets import (
    DEFAULT_PARAM_SET_NAME,
    available_param_sets,
)
from backend.rag_pipeline.utils.logging import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter(tags=["parameters"])


@router.get("/api/v1/parameter-sets")
async def get_parameter_sets() -> dict:
    """Return available RAG parameter sets and default selection."""
    logger.info("GET /api/v1/parameter-sets")
    return {"default": DEFAULT_PARAM_SET_NAME, "sets": available_param_sets()}
