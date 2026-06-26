"""Compatibility shim — delegates to the Query Service API.

Re-exports AuditLogMiddleware from backend.query_service.api.middleware.audit_log.
"""

from backend.query_service.api.middleware.audit_log import AuditLogMiddleware  # noqa: F401

__all__ = ["AuditLogMiddleware"]
