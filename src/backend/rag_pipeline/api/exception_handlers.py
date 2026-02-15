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


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    """Make validation errors JSON-serializable by replacing non-serializable ctx values."""
    sanitized = []
    for err in errors:
        err_copy = err.copy()
        if "ctx" in err_copy and err_copy["ctx"]:
            ctx = {}
            for k, v in err_copy["ctx"].items():
                ctx[k] = str(v) if v is not None and not isinstance(v, (str, int, float, bool)) else v
            err_copy["ctx"] = ctx
        sanitized.append(err_copy)
    return sanitized


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Convert RequestValidationError to RFC 7807 Problem Details format."""
    errors = exc.errors()
    sanitized_errors = _sanitize_validation_errors(errors)
    detail = errors[0].get("msg", "Validation error") if errors else "Validation error"
    content = {
        "type": "about:blank",
        "title": "Validation Error",
        "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": detail,
        "instance": str(request.url.path),
        "errors": sanitized_errors,
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
        media_type=PROBLEM_JSON,
    )
