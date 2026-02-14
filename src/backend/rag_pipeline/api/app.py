"""Main FastAPI application for the RAG pipeline.

This module creates and configures the FastAPI application,
combining all API routes and middleware.
"""

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..utils.logging import StructuredLogger
from . import ask, chat, documents, documents_enhanced, health, metrics, parameters, query, stt, test, websocket

# Set root logger to DEBUG level
logging.getLogger().setLevel(logging.DEBUG)

# Create our structured logger
logger = StructuredLogger(__name__)

# Create FastAPI app
app = FastAPI(title="RAG Pipeline API", description="API for document processing and semantic search", version="1.0.0")

# RFC 7807 Problem Details exception handlers
from fastapi.exceptions import RequestValidationError

from .exception_handlers import http_exception_handler, validation_exception_handler

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Rate limiting (outermost)
from .middleware.rate_limit import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

# Correlation ID middleware
from .middleware.correlation_id import CorrelationIdMiddleware

app.add_middleware(CorrelationIdMiddleware)

# Add CORS middleware (origins from ALLOW_ORIGINS env, comma-separated)
_cors_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include all routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(parameters.router)
app.include_router(documents.router)
app.include_router(documents_enhanced.router)  # Enhanced documents API
app.include_router(query.router)
app.include_router(ask.router)
app.include_router(chat.router)
app.include_router(websocket.router)
app.include_router(test.router)
app.include_router(stt.router)  # Speech-to-text with LLM correction


def start_server():
    """Entry point for starting the backend server."""
    import uvicorn

    logger.info("Starting backend server")
    # Use the fully qualified package path so the entrypoint works without
    # manipulating PYTHONPATH.
    uvicorn.run("backend.rag_pipeline.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
