"""RFC 7807 Problem Details exception handlers for the RAG API.

Converts HTTPException and validation errors to application/problem+json format.
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTPException to RFC 7807 Problem Details format."""
    content = {
        "type": "about:blank",
        "title": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url.path),
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        media_type=PROBLEM_JSON,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Convert RequestValidationError to RFC 7807 Problem Details format."""
    errors = exc.errors()
    detail = errors[0].get("msg", "Validation error") if errors else "Validation error"
    content = {
        "type": "about:blank",
        "title": "Validation Error",
        "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": detail,
        "instance": str(request.url.path),
        "errors": errors,
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
        media_type=PROBLEM_JSON,
    )
