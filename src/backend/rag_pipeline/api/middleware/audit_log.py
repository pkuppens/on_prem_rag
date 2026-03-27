"""Audit log middleware for the RAG pipeline API.

Logs every HTTP request with method, path, status code, and the caller's
identity token (if present) so that every API access is traceable.

The token is NOT validated here — this middleware only records the raw
Bearer token prefix for correlation. Full identity resolution requires the
auth service. In a production deployment, replace token_hint with a verified
user_id extracted from a validated JWT.

Banking/compliance note: This middleware provides the basic access log that
answers "who queried what and when" from application logs alone.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log method, path, status_code, latency_ms, and caller token hint for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        # Extract the first 8 chars of the Bearer token as a correlation hint.
        # This is enough to correlate logs without exposing the full credential.
        auth_header = request.headers.get("Authorization", "")
        token_hint = "anonymous"
        if auth_header.lower().startswith("bearer "):
            raw = auth_header[7:].strip()
            token_hint = raw[:8] + "…" if len(raw) > 8 else raw

        response = await call_next(request)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "method=%s path=%s status=%d latency_ms=%d token=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            token_hint,
        )
        return response
