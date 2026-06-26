"""Compatibility shim — delegates to the Query Service API.

Re-exports CorrelationIdMiddleware from backend.query_service.api.middleware.correlation_id.
"""

from backend.query_service.api.middleware.correlation_id import CorrelationIdMiddleware  # noqa: F401

__all__ = ["CorrelationIdMiddleware"]
