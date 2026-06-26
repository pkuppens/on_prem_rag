"""Correlation ID middleware for request tracing.

Same implementation as the original rag_pipeline/api/middleware/correlation_id.py.
"""

from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a correlation ID to each request and response."""

    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())
        response = await call_next(request)
        response.headers[self.HEADER_NAME] = correlation_id
        return response
