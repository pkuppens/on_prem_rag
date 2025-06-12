"""Subscription helpers.

See docs/technical/MONETIZATION.md for usage details.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def is_subscription_active(expires_at: datetime, *, now: datetime | None = None) -> bool:
    """Return ``True`` if the subscription has not expired."""
    current = now or datetime.utcnow()
    return current <= expires_at


def is_request_time_reasonable(
    client_time: datetime, server_time: datetime, *, tolerance: timedelta = timedelta(minutes=5)
) -> bool:
    """Return ``True`` if the client timestamp is within ``tolerance`` of server time."""
    return abs(server_time - client_time) <= tolerance
