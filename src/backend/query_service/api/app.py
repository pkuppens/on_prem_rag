"""Main FastAPI application for the Query Service.

Creates and configures the FastAPI application with all routes and middleware.
Same endpoints as the original rag_pipeline/api/app.py for backward compatibility.
"""

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.rag_pipeline.config.llm_config import check_data_sovereignty
from backend.rag_pipeline.utils.logging import StructuredLogger

from . import ask, chat, documents, health, metrics, parameters, query, stt, websocket
from .exception_handlers import http_exception_handler, validation_exception_handler

# Fail fast: refuse to start if a cloud LLM backend is used in strict mode.
check_data_sovereignty()

logging.getLogger().setLevel(logging.DEBUG)
logger = StructuredLogger(__name__)

app = FastAPI(title="RAG Pipeline API - Query Service", description="API for document processing and semantic search", version="1.0.0")

# RFC 7807 Problem Details exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Rate limiting (outermost)
from .middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

# Correlation ID middleware
from .middleware.correlation_id import CorrelationIdMiddleware
app.add_middleware(CorrelationIdMiddleware)

# Audit log middleware (innermost so it sees final status codes)
from .middleware.audit_log import AuditLogMiddleware
app.add_middleware(AuditLogMiddleware)

# CORS middleware
_cors_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(parameters.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(ask.router)
app.include_router(chat.router)
app.include_router(stt.router)
app.include_router(websocket.router)
