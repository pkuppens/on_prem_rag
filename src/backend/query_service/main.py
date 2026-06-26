# src/backend/query_service/main.py
"""
Main entry point for the Query Service.

Runs the FastAPI application for the Query Service bounded context.
"""

from backend.query_service.api.app import app
from backend.rag_pipeline.utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


def start_server():
    """Entry point for starting the Query Service server."""
    import uvicorn

    logger.info("Starting Query Service server")
    uvicorn.run("backend.query_service.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
