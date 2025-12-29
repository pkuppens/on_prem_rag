# src/backend/guardrails/middleware.py
"""FastAPI middleware for guardrails integration.

Provides automatic request/response filtering for the RAG API.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.guardrails.config_loader import get_guardrails_config
from backend.guardrails.guardrails_manager import get_guardrails_manager

logger = logging.getLogger(__name__)


class GuardrailsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for guardrails validation.

    Validates incoming requests and outgoing responses against guardrails.
    """

    # Paths that bypass guardrails
    BYPASS_PATHS = [
        "/health",
        "/healthz",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    ]

    # Paths that require guardrails
    PROTECTED_PATHS = [
        "/api/v1/query",
        "/api/v1/analyze",
        "/api/v1/chat",
        "/api/v1/documents",
    ]

    def __init__(self, app: ASGIApp, protected_paths: list[str] | None = None):
        super().__init__(app)
        self.config = get_guardrails_config()
        self.protected_paths = protected_paths or self.PROTECTED_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through guardrails.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint

        Returns:
            Response after guardrails processing
        """
        start_time = time.time()
        path = request.url.path

        # Check if path should bypass guardrails
        if self._should_bypass(path):
            return await call_next(request)

        # Check if guardrails are enabled
        if not self.config.enabled:
            return await call_next(request)

        # Check if path requires protection
        if not self._requires_protection(path):
            return await call_next(request)

        # Get guardrails manager
        manager = get_guardrails_manager()

        # Validate input for POST/PUT requests with body
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    input_text = body.decode("utf-8")
                    context = self._build_context(request)

                    input_result = manager.validate_input(input_text, context)

                    if not input_result.is_allowed:
                        processing_time = (time.time() - start_time) * 1000
                        return self._blocked_response(
                            input_result.blocking_reason or "Request blocked by guardrails",
                            processing_time,
                        )

            except Exception as e:
                logger.error(f"Guardrails input validation error: {e}")
                # Don't block on errors - let request through
                pass

        # Process the request
        response = await call_next(request)

        # Note: Output validation for streaming responses is complex
        # For now, we rely on the agent-level guardrails for output validation

        # Add guardrails timing header
        processing_time = (time.time() - start_time) * 1000
        response.headers["X-Guardrails-Time-Ms"] = str(round(processing_time, 2))

        return response

    def _should_bypass(self, path: str) -> bool:
        """Check if path should bypass guardrails."""
        return any(path.startswith(bp) for bp in self.BYPASS_PATHS)

    def _requires_protection(self, path: str) -> bool:
        """Check if path requires guardrails protection."""
        return any(path.startswith(pp) for pp in self.protected_paths)

    def _build_context(self, request: Request) -> dict:
        """Build context from request."""
        return {
            "source": request.client.host if request.client else "unknown",
            "method": request.method,
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", ""),
        }

    def _blocked_response(self, reason: str, processing_time: float) -> Response:
        """Create a blocked response."""
        import json

        body = json.dumps(
            {
                "error": "Request blocked by guardrails",
                "reason": reason,
                "processing_time_ms": round(processing_time, 2),
            }
        )

        return Response(
            content=body,
            status_code=403,
            media_type="application/json",
            headers={"X-Guardrails-Blocked": "true"},
        )


def add_guardrails_middleware(
    app: FastAPI,
    protected_paths: list[str] | None = None,
) -> None:
    """Add guardrails middleware to FastAPI app.

    Args:
        app: The FastAPI application
        protected_paths: List of paths to protect (uses defaults if not provided)
    """
    app.add_middleware(GuardrailsMiddleware, protected_paths=protected_paths)
    logger.info("Guardrails middleware added to FastAPI app")


class GuardrailsDepends:
    """Dependency injection for guardrails in FastAPI routes.

    Use this as a dependency to add guardrails validation to specific routes.

    Example:
        @app.post("/api/query")
        async def query(
            request: QueryRequest,
            guardrails: GuardrailsDepends = Depends(),
        ):
            validated = guardrails.validate_input(request.text)
            if not validated.is_allowed:
                raise HTTPException(403, validated.blocking_reason)
            ...
    """

    def __init__(self):
        self.manager = get_guardrails_manager()
        self.config = get_guardrails_config()

    def validate_input(
        self,
        text: str,
        context: dict | None = None,
    ):
        """Validate input text."""
        return self.manager.validate_input(text, context)

    def validate_output(
        self,
        text: str,
        context: dict | None = None,
    ):
        """Validate output text."""
        return self.manager.validate_output(text, context)

    @property
    def enabled(self) -> bool:
        """Check if guardrails are enabled."""
        return self.config.enabled
