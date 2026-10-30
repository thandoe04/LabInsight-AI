"""
Sample management API endpoints.
Validates state transitions and enforces date integrity across sample lifecycles.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.patient import Patient
from app.models.sample import (
    SAMPLE_STATUSES,
    VALID_STATUS_TRANSITIONS,
    Sample,
    SampleStatusHistory,
)
from app.security.dependencies import CurrentUser
from app.services.audit import record_audit_event

router = APIRouter()


class SampleCreate(BaseModel):
    patient_id: uuid.UUID
    sample_type: str = Field(..., min_length=2, max_length=64)
    collection_notes: str | None = None
    collected_at: datetime | None = None
    received_at: datetime | None = None


class SampleStatusUpdate(BaseModel):
    new_status: str
    rejection_reason: str | None = None
    notes: str | None = None


class SampleResponse(BaseModel):
    id: str
    sample_code: str
    patient_id: str
    sample_type: str
    collection_notes: str | None
    collected_at: datetime | None
    received_at: datetime | None
    status: str
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SampleListResponse(BaseModel):
    items: list[SampleResponse]
    total: int
    page: int
    page_size: int


class SampleHistoryResponse(BaseModel):
    id: str
    previous_status: str | None
    new_status: str
    changed_at: datetime
    notes: str | None
    changed_by_name: str | None


@router.get("", response_model=SampleListResponse)
async def list_samples(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    sample_type: str | None = None,
    search: str | None = None,
) -> Any:
    """List samples with pagination and filtering."""
    query = select(Sample)

    if status:
        query = query.where(Sample.status == status)
    if sample_type:
        query = query.where(Sample.sample_type == sample_type)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(
            or_(
                Sample.sample_code.ilike(search_filter),
                Sample.sample_type.ilike(search_filter),
            )
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Sample.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    samples = result.scalars().all()

    return SampleListResponse(
        items=[
            SampleResponse(
                id=str(s.id),
                sample_code=s.sample_code,
                patient_id=str(s.patient_id),
                sample_type=s.sample_type,
                collection_notes=s.collection_notes,
                collected_at=s.collected_at,
                received_at=s.received_at,
                status=s.status,
                rejection_reason=s.rejection_reason,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in samples
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=SampleResponse, status_code=status.HTTP_201_CREATED)
async def register_sample(
    request: Request,
    body: SampleCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new biological sample."""
    # Verify patient exists
    p_res = await db.execute(select(Patient).where(Patient.id == body.patient_id, Patient.is_active.is_(True)))
    patient = p_res.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found or inactive.")

    # Validate dates: collected_at cannot be later than received_at
    if body.collected_at and body.received_at and body.collected_at > body.received_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Collection timestamp cannot be later than receipt timestamp.",
        )

    # Generate unique sample code (e.g. SMP-2026-A83F12)
    year = datetime.now(timezone.utc).year
    sample_code = f"SMP-{year}-{secrets.token_hex(3).upper()}"

    initial_status = "received" if body.received_at else ("collected" if body.collected_at else "registered")

    new_sample = Sample(
        sample_code=sample_code,
        patient_id=body.patient_id,
        sample_type=body.sample_type,
        collection_notes=body.collection_notes,
        collected_at=body.collected_at,
        received_at=body.received_at,
        status=initial_status,
        registered_by_id=current_user.id,
    )
    db.add(new_sample)
    await db.flush()

    # Record initial status transition in history
    history_entry = SampleStatusHistory(
        sample_id=new_sample.id,
        previous_status=None,
        new_status=initial_status,
        changed_by_id=current_user.id,
        notes="Initial sample registration",
    )
    db.add(history_entry)
    await db.flush()

    await record_audit_event(
        db,
        action="sample.register",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="sample",
        entity_id=new_sample.id,
        request=request,
    )
    await db.commit()

    return SampleResponse(
        id=str(new_sample.id),
        sample_code=new_sample.sample_code,
        patient_id=str(new_sample.patient_id),
        sample_type=new_sample.sample_type,
        collection_notes=new_sample.collection_notes,
        collected_at=new_sample.collected_at,
        received_at=new_sample.received_at,
        status=new_sample.status,
        rejection_reason=new_sample.rejection_reason,
        created_at=new_sample.created_at,
        updated_at=new_sample.updated_at,
    )


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(
    sample_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve an individual sample by ID."""
    result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found.")

    return SampleResponse(
        id=str(sample.id),
        sample_code=sample.sample_code,
        patient_id=str(sample.patient_id),
        sample_type=sample.sample_type,
        collection_notes=sample.collection_notes,
        collected_at=sample.collected_at,
        received_at=sample.received_at,
        status=sample.status,
        rejection_reason=sample.rejection_reason,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.patch("/{sample_id}/status", response_model=SampleResponse)
async def update_sample_status(
    sample_id: uuid.UUID,
    body: SampleStatusUpdate,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Transition sample status through the validated lifecycle."""
    result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found.")

    if body.new_status not in SAMPLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{body.new_status}'. Allowed: {', '.join(sorted(SAMPLE_STATUSES))}",
        )

    # Validate transition
    allowed_transitions = VALID_STATUS_TRANSITIONS.get(sample.status, frozenset())
    if body.new_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from '{sample.status}' to '{body.new_status}'. Allowed: {', '.join(sorted(allowed_transitions)) or 'None (terminal)'}",
        )

    if body.new_status == "rejected" and not body.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A rejection reason must be specified when rejecting a sample.",
        )

    previous_status = sample.status
    sample.status = body.new_status
    if body.rejection_reason:
        sample.rejection_reason = body.rejection_reason

    # Add history
    hist = SampleStatusHistory(
        sample_id=sample.id,
        previous_status=previous_status,
        new_status=body.new_status,
        changed_by_id=current_user.id,
        notes=body.notes or (f"Reason: {body.rejection_reason}" if body.rejection_reason else None),
    )
    db.add(hist)
    await db.flush()

    await record_audit_event(
        db,
        action="sample.status_transition",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="sample",
        entity_id=sample.id,
        metadata={"from": previous_status, "to": body.new_status},
        request=request,
    )
    await db.commit()

    return SampleResponse(
        id=str(sample.id),
        sample_code=sample.sample_code,
        patient_id=str(sample.patient_id),
        sample_type=sample.sample_type,
        collection_notes=sample.collection_notes,
        collected_at=sample.collected_at,
        received_at=sample.received_at,
        status=sample.status,
        rejection_reason=sample.rejection_reason,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.get("/{sample_id}/history", response_model=list[SampleHistoryResponse])
async def get_sample_history(
    sample_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve full immutable audit history of status changes for a sample."""
    result = await db.execute(
        select(SampleStatusHistory)
        .where(SampleStatusHistory.sample_id == sample_id)
        .options(selectinload(SampleStatusHistory.changed_by))
        .order_by(SampleStatusHistory.changed_at.asc())
    )
    history = result.scalars().all()

    return [
        SampleHistoryResponse(
            id=str(h.id),
            previous_status=h.previous_status,
            new_status=h.new_status,
            changed_at=h.changed_at,
            notes=h.notes,
            changed_by_name=h.changed_by.full_name if h.changed_by else None,
        )
        for h in history
    ]
