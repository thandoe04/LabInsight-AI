"""
Audit logging service.

All sensitive operations generate audit events.
Never logs passwords, tokens, or sensitive PII.
Audit records are append-only.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)


async def record_audit_event(
    db: AsyncSession,
    action: str,
    outcome: str,
    *,
    actor_id: uuid.UUID | None = None,
    actor_username: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Create an append-only audit log entry.

    Parameters
    ----------
    action      : str  — e.g. 'login', 'patient.create', 'result.verify'
    outcome     : str  — 'success', 'failure', 'error'
    metadata    : dict — additional context (must NOT contain secrets/PII)
    """
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None

    if request is not None:
        forwarded_for = request.headers.get("X-Forwarded-For")
        ip_address = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else getattr(request.client, "host", None)
        )
        user_agent = request.headers.get("User-Agent", "")[:512]
        request_id = request.headers.get("X-Request-ID")

    entry = AuditLog(
        actor_id=actor_id,
        actor_username=actor_username,
        action=action,
        outcome=outcome,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        metadata_=metadata,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "audit_event",
        action=action,
        outcome=outcome,
        actor=actor_username,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
    )
    return entry
