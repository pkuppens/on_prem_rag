"""Audit log middleware for the Query Service API.

Same implementation as the original rag_pipeline/api/middleware/audit_log.py.
Logs every HTTP request for traceability.
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
