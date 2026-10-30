"""
Laboratory test catalogue and reference interval management endpoints.
Reference intervals require documented clinical provenance and authorised user assignment.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.laboratory import LaboratoryTest, ReferenceRange, TestCategory
from app.security.dependencies import CurrentUser
from app.services.audit import record_audit_event

router = APIRouter()


# ─── Categories ──────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: str | None = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List laboratory test categories."""
    result = await db.execute(select(TestCategory).where(TestCategory.is_active.is_(True)).order_by(TestCategory.name))
    categories = result.scalars().all()
    return [
        CategoryResponse(
            id=str(c.id),
            name=c.name,
            description=c.description,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in categories
    ]


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    body: CategoryCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new laboratory test category."""
    existing = await db.execute(select(TestCategory).where(TestCategory.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists.")

    cat = TestCategory(name=body.name, description=body.description)
    db.add(cat)
    await db.flush()

    await record_audit_event(
        db,
        action="category.create",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="test_category",
        entity_id=cat.id,
        request=request,
    )
    await db.commit()

    return CategoryResponse(
        id=str(cat.id),
        name=cat.name,
        description=cat.description,
        is_active=cat.is_active,
        created_at=cat.created_at,
    )


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestCreate(BaseModel):
    test_code: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=2, max_length=256)
    category_id: uuid.UUID
    measurement_unit: str | None = None
    result_type: str = Field("numeric", pattern="^(numeric|qualitative|text)$")
    allowed_values: str | None = None
    description: str | None = None


class TestUpdate(BaseModel):
    name: str | None = None
    measurement_unit: str | None = None
    allowed_values: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ReferenceRangeResponse(BaseModel):
    id: str
    applicable_sex: str | None
    min_age_years: float | None
    max_age_years: float | None
    lower_limit: float | None
    upper_limit: float | None
    unit: str | None
    qualitative_normal_values: str | None
    source: str
    notes: str | None
    is_active: bool


class TestResponse(BaseModel):
    id: str
    test_code: str
    name: str
    category_id: str
    category_name: str | None
    measurement_unit: str | None
    result_type: str
    allowed_values: str | None
    description: str | None
    is_active: bool
    reference_ranges: list[ReferenceRangeResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/tests", response_model=list[TestResponse])
async def list_tests(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    include_inactive: bool = False,
) -> Any:
    """List and search laboratory tests with their active reference ranges."""
    query = select(LaboratoryTest).options(
        selectinload(LaboratoryTest.category),
        selectinload(LaboratoryTest.reference_ranges),
    )

    if not include_inactive:
        query = query.where(LaboratoryTest.is_active.is_(True))
    if category_id:
        query = query.where(LaboratoryTest.category_id == category_id)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(
            or_(
                LaboratoryTest.test_code.ilike(search_filter),
                LaboratoryTest.name.ilike(search_filter),
            )
        )

    query = query.order_by(LaboratoryTest.test_code.asc())
    result = await db.execute(query)
    tests = result.scalars().all()

    return [
        TestResponse(
            id=str(t.id),
            test_code=t.test_code,
            name=t.name,
            category_id=str(t.category_id),
            category_name=t.category.name if t.category else None,
            measurement_unit=t.measurement_unit,
            result_type=t.result_type,
            allowed_values=t.allowed_values,
            description=t.description,
            is_active=t.is_active,
            reference_ranges=[
                ReferenceRangeResponse(
                    id=str(r.id),
                    applicable_sex=r.applicable_sex,
                    min_age_years=float(r.min_age_years) if r.min_age_years is not None else None,
                    max_age_years=float(r.max_age_years) if r.max_age_years is not None else None,
                    lower_limit=float(r.lower_limit) if r.lower_limit is not None else None,
                    upper_limit=float(r.upper_limit) if r.upper_limit is not None else None,
                    unit=r.unit,
                    qualitative_normal_values=r.qualitative_normal_values,
                    source=r.source,
                    notes=r.notes,
                    is_active=r.is_active,
                )
                for r in t.reference_ranges
                if r.is_active
            ],
            created_at=t.created_at,
        )
        for t in tests
    ]


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    request: Request,
    body: TestCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new laboratory test definition."""
    existing = await db.execute(select(LaboratoryTest).where(LaboratoryTest.test_code == body.test_code.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A test with this code already exists.")

    test = LaboratoryTest(
        test_code=body.test_code.upper(),
        name=body.name,
        category_id=body.category_id,
        measurement_unit=body.measurement_unit,
        result_type=body.result_type,
        allowed_values=body.allowed_values,
        description=body.description,
        created_by_id=current_user.id,
    )
    db.add(test)
    await db.flush()

    await record_audit_event(
        db,
        action="test.create",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="laboratory_test",
        entity_id=test.id,
        request=request,
    )
    await db.commit()

    return TestResponse(
        id=str(test.id),
        test_code=test.test_code,
        name=test.name,
        category_id=str(test.category_id),
        category_name=None,
        measurement_unit=test.measurement_unit,
        result_type=test.result_type,
        allowed_values=test.allowed_values,
        description=test.description,
        is_active=test.is_active,
        reference_ranges=[],
        created_at=test.created_at,
    )


# ─── Reference Ranges ────────────────────────────────────────────────────────

class ReferenceRangeCreate(BaseModel):
    test_id: uuid.UUID
    applicable_sex: str | None = Field(None, pattern="^(male|female|intersex|all)$")
    min_age_years: float | None = None
    max_age_years: float | None = None
    lower_limit: float | None = None
    upper_limit: float | None = None
    unit: str | None = None
    qualitative_normal_values: str | None = None
    source: str = Field(..., min_length=3, description="Clinical guidelines, manufacturer specification, or accredited literature.")
    notes: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None


@router.post("/reference-ranges", response_model=ReferenceRangeResponse, status_code=status.HTTP_201_CREATED)
async def create_reference_range(
    request: Request,
    body: ReferenceRangeCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Define a validated reference interval for a laboratory test.
    Requires mandatory clinical source attribution.
    """
    t_res = await db.execute(select(LaboratoryTest).where(LaboratoryTest.id == body.test_id))
    test = t_res.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Laboratory test not found.")

    if body.lower_limit is not None and body.upper_limit is not None:
        if body.lower_limit > body.upper_limit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Lower limit cannot exceed upper limit.",
            )

    rr = ReferenceRange(
        test_id=body.test_id,
        applicable_sex=body.applicable_sex,
        min_age_years=body.min_age_years,
        max_age_years=body.max_age_years,
        lower_limit=body.lower_limit,
        upper_limit=body.upper_limit,
        unit=body.unit or test.measurement_unit,
        qualitative_normal_values=body.qualitative_normal_values,
        source=body.source,
        notes=body.notes,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        authorised_by_id=current_user.id,
        authorised_at=datetime.now(timezone.utc),
    )
    db.add(rr)
    await db.flush()

    await record_audit_event(
        db,
        action="reference_range.create",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="reference_range",
        entity_id=rr.id,
        request=request,
    )
    await db.commit()

    return ReferenceRangeResponse(
        id=str(rr.id),
        applicable_sex=rr.applicable_sex,
        min_age_years=float(rr.min_age_years) if rr.min_age_years is not None else None,
        max_age_years=float(rr.max_age_years) if rr.max_age_years is not None else None,
        lower_limit=float(rr.lower_limit) if rr.lower_limit is not None else None,
        upper_limit=float(rr.upper_limit) if rr.upper_limit is not None else None,
        unit=rr.unit,
        qualitative_normal_values=rr.qualitative_normal_values,
        source=rr.source,
        notes=rr.notes,
        is_active=rr.is_active,
    )
