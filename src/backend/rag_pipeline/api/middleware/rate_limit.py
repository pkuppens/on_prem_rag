"""Compatibility shim — delegates to the Query Service API.

Re-exports RateLimitMiddleware from backend.query_service.api.middleware.rate_limit.
"""

from backend.query_service.api.middleware.rate_limit import RateLimitMiddleware  # noqa: F401

__all__ = ["RateLimitMiddleware"]
