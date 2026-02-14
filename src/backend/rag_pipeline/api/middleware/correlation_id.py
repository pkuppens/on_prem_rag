"""Correlation ID middleware for request tracing.

Adds X-Correlation-ID header to requests and responses for distributed tracing.
"""

from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a correlation ID to each request and response.

    Reads X-Correlation-ID from request if present, otherwise generates a new UUID.
    Adds the same ID to the response for traceability.
    """

    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add correlation ID to response."""
        correlation_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())
        response = await call_next(request)
        response.headers[self.HEADER_NAME] = correlation_id
        return response
