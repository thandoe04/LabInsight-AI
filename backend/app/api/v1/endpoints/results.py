"""
Laboratory test results management API endpoints.
Enforces immutable revision history, verification controls, and reference interval flagging.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.laboratory import LaboratoryTest, ReferenceRange
from app.models.result import ResultRevision, ResultVerification, TestResult
from app.models.sample import Sample
from app.security.dependencies import CurrentUser
from app.services.audit import record_audit_event

router = APIRouter()


class ResultCreate(BaseModel):
    sample_id: uuid.UUID
    test_id: uuid.UUID
    numeric_value: float | None = None
    qualitative_value: str | None = None
    text_value: str | None = None
    measurement_unit: str | None = None
    measured_at: datetime | None = None


class ResultRevise(BaseModel):
    new_numeric_value: float | None = None
    new_qualitative_value: str | None = None
    reason: str = Field(..., min_length=5, description="Mandatory audit explanation for revising result.")


class ResultVerify(BaseModel):
    notes: str | None = None


class RevisionResponse(BaseModel):
    revision_number: int
    previous_numeric_value: float | None
    previous_qualitative_value: str | None
    new_numeric_value: float | None
    new_qualitative_value: str | None
    reason: str
    revised_at: datetime
    revised_by_name: str | None


class ResultResponse(BaseModel):
    id: str
    sample_id: str
    sample_code: str | None
    test_id: str
    test_code: str | None
    test_name: str | None
    numeric_value: float | None
    qualitative_value: str | None
    text_value: str | None
    measurement_unit: str | None
    is_above_upper_limit: bool | None
    is_below_lower_limit: bool | None
    measured_at: datetime
    status: str
    verified_at: datetime | None
    verified_by_name: str | None
    revisions_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResultListResponse(BaseModel):
    items: list[ResultResponse]
    total: int
    page: int
    page_size: int


async def _evaluate_reference_interval(
    db: AsyncSession,
    test_id: uuid.UUID,
    numeric_val: float | None,
) -> tuple[bool | None, bool | None, uuid.UUID | None]:
    """Compare a numeric value against active reference intervals. Return (is_above, is_below, ref_range_id)."""
    if numeric_val is None:
        return None, None, None

    res = await db.execute(
        select(ReferenceRange)
        .where(ReferenceRange.test_id == test_id, ReferenceRange.is_active.is_(True))
        .order_by(ReferenceRange.created_at.desc())
    )
    ranges = res.scalars().all()
    if not ranges:
        return None, None, None

    # Use first matching active general range
    rr = ranges[0]
    is_above = None
    is_below = None

    if rr.upper_limit is not None and numeric_val > float(rr.upper_limit):
        is_above = True
    elif rr.upper_limit is not None:
        is_above = False

    if rr.lower_limit is not None and numeric_val < float(rr.lower_limit):
        is_below = True
    elif rr.lower_limit is not None:
        is_below = False

    return is_above, is_below, rr.id


@router.get("", response_model=ResultListResponse)
async def list_results(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sample_id: uuid.UUID | None = None,
    test_id: uuid.UUID | None = None,
    status: str | None = None,
) -> Any:
    """Query test results with test and verification metadata."""
    query = (
        select(TestResult)
        .options(
            selectinload(TestResult.sample),
            selectinload(TestResult.test),
            selectinload(TestResult.verification).selectinload(ResultVerification.verified_by),
            selectinload(TestResult.revisions),
        )
    )

    if sample_id:
        query = query.where(TestResult.sample_id == sample_id)
    if test_id:
        query = query.where(TestResult.test_id == test_id)
    if status:
        query = query.where(TestResult.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(TestResult.measured_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    results = result.scalars().all()

    items: list[ResultResponse] = []
    for r in results:
        items.append(
            ResultResponse(
                id=str(r.id),
                sample_id=str(r.sample_id),
                sample_code=r.sample.sample_code if r.sample else None,
                test_id=str(r.test_id),
                test_code=r.test.test_code if r.test else None,
                test_name=r.test.name if r.test else None,
                numeric_value=float(r.numeric_value) if r.numeric_value is not None else None,
                qualitative_value=r.qualitative_value,
                text_value=r.text_value,
                measurement_unit=r.measurement_unit or (r.test.measurement_unit if r.test else None),
                is_above_upper_limit=r.is_above_upper_limit,
                is_below_lower_limit=r.is_below_lower_limit,
                measured_at=r.measured_at,
                status=r.status,
                verified_at=r.verification.verified_at if r.verification else None,
                verified_by_name=r.verification.verified_by.full_name if (r.verification and r.verification.verified_by) else None,
                revisions_count=len(r.revisions),
                created_at=r.created_at,
            )
        )

    return ResultListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ResultResponse, status_code=status.HTTP_201_CREATED)
async def record_result(
    request: Request,
    body: ResultCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record a laboratory test result for a sample."""
    # Verify sample & test
    s_res = await db.execute(select(Sample).where(Sample.id == body.sample_id))
    sample = s_res.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found.")

    t_res = await db.execute(select(LaboratoryTest).where(LaboratoryTest.id == body.test_id))
    test = t_res.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Laboratory test not found.")

    measured_at = body.measured_at or datetime.now(timezone.utc)
    is_above, is_below, ref_id = await _evaluate_reference_interval(db, test.id, body.numeric_value)

    res = TestResult(
        sample_id=body.sample_id,
        test_id=body.test_id,
        numeric_value=body.numeric_value,
        qualitative_value=body.qualitative_value,
        text_value=body.text_value,
        measurement_unit=body.measurement_unit or test.measurement_unit,
        is_above_upper_limit=is_above,
        is_below_lower_limit=is_below,
        reference_range_id=ref_id,
        measured_at=measured_at,
        status="pending",
        recorded_by_id=current_user.id,
    )
    db.add(res)
    await db.flush()

    await record_audit_event(
        db,
        action="result.record",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="test_result",
        entity_id=res.id,
        request=request,
    )
    await db.commit()

    return ResultResponse(
        id=str(res.id),
        sample_id=str(res.sample_id),
        sample_code=sample.sample_code,
        test_id=str(res.test_id),
        test_code=test.test_code,
        test_name=test.name,
        numeric_value=body.numeric_value,
        qualitative_value=body.qualitative_value,
        text_value=body.text_value,
        measurement_unit=res.measurement_unit,
        is_above_upper_limit=is_above,
        is_below_lower_limit=is_below,
        measured_at=res.measured_at,
        status=res.status,
        verified_at=None,
        verified_by_name=None,
        revisions_count=0,
        created_at=res.created_at,
    )


@router.post("/{result_id}/verify", response_model=ResultResponse)
async def verify_result(
    result_id: uuid.UUID,
    body: ResultVerify,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify a laboratory result. Once verified, it cannot be silently modified."""
    q = (
        select(TestResult)
        .where(TestResult.id == result_id)
        .options(
            selectinload(TestResult.sample),
            selectinload(TestResult.test),
            selectinload(TestResult.revisions),
            selectinload(TestResult.verification),
        )
    )
    result = (await db.execute(q)).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found.")

    if result.status == "verified":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Result is already verified.")

    verification = ResultVerification(
        result_id=result.id,
        verified_by_id=current_user.id,
        notes=body.notes,
    )
    db.add(verification)

    result.status = "verified"
    await db.flush()

    await record_audit_event(
        db,
        action="result.verify",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="test_result",
        entity_id=result.id,
        request=request,
    )
    await db.commit()

    return ResultResponse(
        id=str(result.id),
        sample_id=str(result.sample_id),
        sample_code=result.sample.sample_code if result.sample else None,
        test_id=str(result.test_id),
        test_code=result.test.test_code if result.test else None,
        test_name=result.test.name if result.test else None,
        numeric_value=float(result.numeric_value) if result.numeric_value is not None else None,
        qualitative_value=result.qualitative_value,
        text_value=result.text_value,
        measurement_unit=result.measurement_unit,
        is_above_upper_limit=result.is_above_upper_limit,
        is_below_lower_limit=result.is_below_lower_limit,
        measured_at=result.measured_at,
        status=result.status,
        verified_at=verification.verified_at,
        verified_by_name=current_user.full_name,
        revisions_count=len(result.revisions),
        created_at=result.created_at,
    )


@router.patch("/{result_id}/revise", response_model=ResultResponse)
async def revise_result(
    result_id: uuid.UUID,
    body: ResultRevise,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Apply a controlled revision to a result.
    NEVER silently overwrites previous values: creates an immutable ResultRevision record.
    """
    q = (
        select(TestResult)
        .where(TestResult.id == result_id)
        .options(
            selectinload(TestResult.sample),
            selectinload(TestResult.test),
            selectinload(TestResult.revisions),
            selectinload(TestResult.verification).selectinload(ResultVerification.verified_by),
        )
    )
    res = (await db.execute(q)).scalar_one_or_none()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found.")

    rev_number = len(res.revisions) + 1
    rev = ResultRevision(
        result_id=res.id,
        revision_number=rev_number,
        previous_numeric_value=res.numeric_value,
        previous_qualitative_value=res.qualitative_value,
        new_numeric_value=body.new_numeric_value,
        new_qualitative_value=body.new_qualitative_value,
        reason=body.reason,
        revised_by_id=current_user.id,
    )
    db.add(rev)

    # Re-evaluate reference range
    is_above, is_below, ref_id = await _evaluate_reference_interval(db, res.test_id, body.new_numeric_value)
    res.numeric_value = body.new_numeric_value
    res.qualitative_value = body.new_qualitative_value
    res.is_above_upper_limit = is_above
    res.is_below_lower_limit = is_below
    if ref_id:
        res.reference_range_id = ref_id
    res.status = "corrected"
    await db.flush()

    await record_audit_event(
        db,
        action="result.revise",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="test_result",
        entity_id=res.id,
        metadata={"revision_number": rev_number, "reason": body.reason},
        request=request,
    )
    await db.commit()

    return ResultResponse(
        id=str(res.id),
        sample_id=str(res.sample_id),
        sample_code=res.sample.sample_code if res.sample else None,
        test_id=str(res.test_id),
        test_code=res.test.test_code if res.test else None,
        test_name=res.test.name if res.test else None,
        numeric_value=float(res.numeric_value) if res.numeric_value is not None else None,
        qualitative_value=res.qualitative_value,
        text_value=res.text_value,
        measurement_unit=res.measurement_unit,
        is_above_upper_limit=res.is_above_upper_limit,
        is_below_lower_limit=res.is_below_lower_limit,
        measured_at=res.measured_at,
        status=res.status,
        verified_at=res.verification.verified_at if res.verification else None,
        verified_by_name=res.verification.verified_by.full_name if (res.verification and res.verification.verified_by) else None,
        revisions_count=rev_number,
        created_at=res.created_at,
    )


@router.get("/{result_id}/history", response_model=list[RevisionResponse])
async def get_result_history(
    result_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve complete audit history of all revisions made to a test result."""
    result = await db.execute(
        select(ResultRevision)
        .where(ResultRevision.result_id == result_id)
        .options(selectinload(ResultRevision.revised_by))
        .order_by(ResultRevision.revision_number.asc())
    )
    revisions = result.scalars().all()

    return [
        RevisionResponse(
            revision_number=r.revision_number,
            previous_numeric_value=float(r.previous_numeric_value) if r.previous_numeric_value is not None else None,
            previous_qualitative_value=r.previous_qualitative_value,
            new_numeric_value=float(r.new_numeric_value) if r.new_numeric_value is not None else None,
            new_qualitative_value=r.new_qualitative_value,
            reason=r.reason,
            revised_at=r.revised_at,
            revised_by_name=r.revised_by.full_name if r.revised_by else None,
        )
        for r in revisions
    ]
