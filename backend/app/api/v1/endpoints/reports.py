"""
Reports API endpoints.
Provides generation, metadata tracking, and secure downloads for PDF, CSV, and Excel exports.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.laboratory import LaboratoryTest
from app.models.result import TestResult
from app.models.sample import Sample
from app.models.system import Report
from app.reporting.generator import generate_csv_report, generate_excel_report, generate_pdf_report
from app.security.dependencies import CurrentUser
from app.services.audit import record_audit_event

router = APIRouter()
_settings = get_settings()


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=256)
    report_type: str = Field(..., pattern="^(samples|results|quality|activity)$")
    format: str = Field(..., pattern="^(pdf|csv|excel)$")
    filters: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    format: str
    status: str
    generated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List previously generated reports."""
    q = select(Report).order_by(Report.created_at.desc())
    res = await db.execute(q)
    reports = res.scalars().all()

    return [
        ReportResponse(
            id=str(r.id),
            title=r.title,
            report_type=r.report_type,
            format=r.format,
            status=r.status,
            generated_at=r.generated_at,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: Request,
    body: ReportCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate and register a laboratory analytics or operational report."""
    rep = Report(
        title=body.title,
        report_type=body.report_type,
        format=body.format,
        status="ready",
        filters=body.filters,
        generated_by_id=current_user.id,
        generated_at=datetime.now(timezone.utc),
    )
    db.add(rep)
    await db.flush()

    await record_audit_event(
        db,
        action="report.generate",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="report",
        entity_id=rep.id,
        metadata={"format": body.format, "type": body.report_type},
        request=request,
    )
    await db.commit()

    return ReportResponse(
        id=str(rep.id),
        title=rep.title,
        report_type=rep.report_type,
        format=rep.format,
        status=rep.status,
        generated_at=rep.generated_at,
        created_at=rep.created_at,
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Stream dynamically compiled report file in PDF, CSV, or Excel format."""
    q = select(Report).where(Report.id == report_id)
    rep = (await db.execute(q)).scalar_one_or_none()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")

    headers: list[str] = []
    rows: list[list[Any]] = []

    if rep.report_type == "samples":
        headers = ["Sample Code", "Type", "Status", "Collected At", "Received At"]
        s_q = select(Sample).order_by(Sample.created_at.desc()).limit(200)
        samples = (await db.execute(s_q)).scalars().all()
        for s in samples:
            rows.append([
                s.sample_code,
                s.sample_type,
                s.status,
                s.collected_at.strftime("%Y-%m-%d %H:%M") if s.collected_at else "",
                s.received_at.strftime("%Y-%m-%d %H:%M") if s.received_at else "",
            ])
    else:  # results or other
        headers = ["Sample", "Test Code", "Test Name", "Value", "Unit", "Flag", "Status", "Measured At"]
        r_q = select(TestResult).options(selectinload(TestResult.sample), selectinload(TestResult.test)).order_by(TestResult.measured_at.desc()).limit(200)
        results = (await db.execute(r_q)).scalars().all()
        for r in results:
            flag = "HIGH" if r.is_above_upper_limit else ("LOW" if r.is_below_lower_limit else "NORMAL")
            val = r.numeric_value if r.numeric_value is not None else r.qualitative_value
            rows.append([
                r.sample.sample_code if r.sample else "",
                r.test.test_code if r.test else "",
                r.test.name if r.test else "",
                val,
                r.measurement_unit or "",
                flag,
                r.status,
                r.measured_at.strftime("%Y-%m-%d %H:%M"),
            ])

    filename = f"{rep.title.replace(' ', '_')}_{rep.id}.{rep.format}"

    if rep.format == "csv":
        buf = generate_csv_report(rep.title, headers, rows)
        media_type = "text/csv"
    elif rep.format == "excel":
        buf = generate_excel_report(rep.title, headers, rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{rep.title.replace(' ', '_')}_{rep.id}.xlsx"
    else:
        buf = generate_pdf_report(rep.title, headers, rows, current_user.full_name)
        media_type = "application/pdf"

    await record_audit_event(
        db,
        action="report.download",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="report",
        entity_id=rep.id,
        request=request,
    )
    await db.commit()

    return StreamingResponse(
        buf,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
