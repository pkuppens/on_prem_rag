# src/backend/guardrails/actions/audit_action.py
"""Audit logging action for NeMo Guardrails.

Logs guardrail events for compliance and monitoring.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


async def audit_action(
    event_type: str = "guardrail_event",
    event_data: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Log a guardrail event for audit purposes.

    This action is called from Colang flows to log guardrail decisions.

    Args:
        event_type: Type of event (e.g., "input_blocked", "output_filtered")
        event_data: Additional event data
        context: NeMo Guardrails context

    Returns:
        Dict with event logging result
    """
    timestamp = datetime.now(UTC).isoformat()

    event = {
        "timestamp": timestamp,
        "event_type": event_type,
        "data": event_data or {},
    }

    # Extract relevant context
    if context:
        event["session_id"] = context.get("session_id")
        event["user_id"] = context.get("user_id")
        # Don't log full messages for privacy - just indicate presence
        event["had_user_message"] = bool(context.get("user_message"))
        event["had_bot_message"] = bool(context.get("bot_message"))

    # Log the event
    log_message = f"Guardrail audit: {event_type}"
    if event_data:
        log_message += f" - {event_data}"

    if event_type.endswith("_blocked") or event_type.endswith("_denied"):
        logger.warning(log_message)
    else:
        logger.info(log_message)

    # Try to store in memory system if available
    try:
        from backend.memory import get_memory_manager

        manager = get_memory_manager()
        manager.store_short_term(
            session_id=event.get("session_id", "audit"),
            key=f"guardrail_event_{timestamp}",
            value=event,
            agent_role="guardrails",
        )
    except Exception as e:
        # Memory storage is optional
        logger.debug(f"Could not store audit event in memory: {e}")

    return {
        "logged": True,
        "timestamp": timestamp,
        "event_type": event_type,
    }


async def log_blocked_request(
    reason: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Log a blocked request.

    Args:
        reason: Reason for blocking
        context: Request context

    Returns:
        Audit result
    """
    return await audit_action(
        event_type="request_blocked",
        event_data={"reason": reason},
        context=context,
    )


async def log_pii_detected(
    categories: list[str],
    location: str = "input",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Log PII detection event.

    Args:
        categories: Detected PII categories
        location: Where PII was detected (input/output)
        context: Request context

    Returns:
        Audit result
    """
    return await audit_action(
        event_type="pii_detected",
        event_data={
            "categories": categories,
            "location": location,
            "count": len(categories),
        },
        context=context,
    )
