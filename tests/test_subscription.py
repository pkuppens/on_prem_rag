"""Tests for subscription utilities."""

from datetime import datetime, timedelta

from backend.monetization.subscription import (
    is_request_time_reasonable,
    is_subscription_active,
)


def test_subscription_active_true() -> None:
    """Subscription should be active when expiry is in the future."""
    expires_at = datetime.utcnow() + timedelta(days=1)
    assert is_subscription_active(expires_at)


def test_subscription_active_false() -> None:
    """Subscription should be inactive after expiration."""
    expires_at = datetime.utcnow() - timedelta(seconds=1)
    assert not is_subscription_active(expires_at)


def test_request_time_reasonable() -> None:
    """Client timestamp within tolerance should pass."""
    server_time = datetime.utcnow()
    client_time = server_time - timedelta(minutes=2)
    assert is_request_time_reasonable(client_time, server_time)


def test_request_time_unreasonable() -> None:
    """Client timestamp outside tolerance should fail."""
    server_time = datetime.utcnow()
    client_time = server_time - timedelta(minutes=10)
    assert not is_request_time_reasonable(client_time, server_time, tolerance=timedelta(minutes=5))
