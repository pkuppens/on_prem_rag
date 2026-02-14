"""Rate limiting middleware for the RAG API.

Simple in-memory rate limiter: configurable requests per minute per client IP.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Paths excluded from rate limiting
BYPASS_PATHS = {
    "/health",
    "/healthz",
    "/ready",
    "/api/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

# Default: 60 requests per minute per IP
DEFAULT_RPM = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that limits requests per minute per client IP."""

    def __init__(
        self,
        app,
        requests_per_minute: int = DEFAULT_RPM,
        bypass_paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.bypass = bypass_paths if bypass_paths is not None else BYPASS_PATHS
        # IP -> list of timestamps (last N requests)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _should_bypass(self, path: str) -> bool:
        """Check if path should bypass rate limiting."""
        return any(path == p or path.startswith(p + "/") for p in self.bypass)

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = time.time()
        window_start = now - 60  # 1 minute window
        # Prune old timestamps
        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > window_start]
        return len(self._requests[client_ip]) >= self.rpm

    def _record_request(self, client_ip: str) -> None:
        """Record a request for the client."""
        self._requests[client_ip].append(time.time())

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and enforce rate limit."""
        path = request.url.path
        if self._should_bypass(path):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "type": "about:blank",
                    "title": "Too Many Requests",
                    "status": 429,
                    "detail": f"Rate limit exceeded. Maximum {self.rpm} requests per minute.",
                    "instance": path,
                },
                media_type="application/problem+json",
                headers={"Retry-After": "60"},
            )

        self._record_request(client_ip)
        return await call_next(request)
