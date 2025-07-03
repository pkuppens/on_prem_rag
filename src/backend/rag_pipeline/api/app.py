"""Main FastAPI application for the RAG pipeline.

This module creates and configures the FastAPI application,
combining all API routes and middleware.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..utils.logging import StructuredLogger
from . import documents, health, parameters, query, test, websocket

# Set root logger to DEBUG level
logging.getLogger().setLevel(logging.DEBUG)

# Create our structured logger
logger = StructuredLogger(__name__)

# Create FastAPI app
app = FastAPI(title="RAG Pipeline API", description="API for document processing and semantic search", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include all routers
app.include_router(health.router)
app.include_router(parameters.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(websocket.router)
app.include_router(test.router)


def start_server():
    """Entry point for starting the backend server."""
    import uvicorn

    logger.info("Starting backend server")
    # Use the fully qualified package path so the entrypoint works without
    # manipulating PYTHONPATH.
    uvicorn.run("backend.rag_pipeline.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
