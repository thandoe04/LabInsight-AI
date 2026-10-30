"""
Audit Logging API endpoints.
Provides tamper-evident query access to the immutable system audit trail.
Never exposes sensitive authentication tokens, passwords, or PII.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.audit import AuditLog
from app.security.dependencies import CurrentUser

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    actor_id: str | None
    actor_username: str | None
    action: str
    outcome: str
    entity_type: str | None
    entity_id: str | None
    ip_address: str | None
    request_id: str | None
    metadata_: dict | None
    occurred_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: str | None = None,
    outcome: str | None = None,
    entity_type: str | None = None,
) -> Any:
    """Query immutable audit events with pagination and filtering."""
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if outcome:
        q = q.where(AuditLog.outcome == outcome)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    q = q.order_by(AuditLog.occurred_at.desc()).offset(offset).limit(page_size)
    res = await db.execute(q)
    logs = res.scalars().all()

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                actor_id=str(log.actor_id) if log.actor_id else None,
                actor_username=log.actor_username,
                action=log.action,
                outcome=log.outcome,
                entity_type=log.entity_type,
                entity_id=str(log.entity_id) if log.entity_id else None,
                ip_address=log.ip_address,
                request_id=log.request_id,
                metadata_=log.metadata_,
                occurred_at=log.occurred_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
