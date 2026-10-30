"""
Dashboard API endpoints.
Provides real-time laboratory statistics, activity streams, and aggregated metrics.
All counts and distributions are queried dynamically from the PostgreSQL database.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.laboratory import LaboratoryTest, TestCategory
from app.models.ml import AnomalyRecord, DataQualityIssue
from app.models.patient import Patient
from app.models.result import TestResult
from app.models.sample import Sample
from app.security.dependencies import CurrentUser

router = APIRouter()


class DashboardSummary(BaseModel):
    total_patients: int
    total_samples: int
    total_tests: int
    completed_tests: int
    pending_tests: int
    verified_results: int
    data_quality_issues: int
    statistical_anomalies: int


class CategoryDistribution(BaseModel):
    category_name: str
    count: int


class SampleStatusDistribution(BaseModel):
    status: str
    count: int


class MonthlyTrend(BaseModel):
    month: str
    samples: int
    results: int


class DashboardCharts(BaseModel):
    sample_status_distribution: list[SampleStatusDistribution]
    test_category_distribution: list[CategoryDistribution]
    monthly_activity: list[MonthlyTrend]


class ActivityItem(BaseModel):
    id: str
    entity_type: str
    description: str
    timestamp: datetime
    status: str


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return aggregated count metrics queried directly from the database."""
    # Patient count
    p_res = await db.execute(select(func.count(Patient.id)).where(Patient.is_active.is_(True)))
    total_patients = p_res.scalar() or 0

    # Sample count
    s_res = await db.execute(select(func.count(Sample.id)))
    total_samples = s_res.scalar() or 0

    # Test count
    t_res = await db.execute(select(func.count(LaboratoryTest.id)).where(LaboratoryTest.is_active.is_(True)))
    total_tests = t_res.scalar() or 0

    # Test results breakdown
    completed_res = await db.execute(select(func.count(TestResult.id)).where(TestResult.status == "verified"))
    completed_tests = completed_res.scalar() or 0

    pending_res = await db.execute(select(func.count(TestResult.id)).where(TestResult.status == "pending"))
    pending_tests = pending_res.scalar() or 0

    verified_res = await db.execute(select(func.count(TestResult.id)).where(TestResult.status.in_(["verified", "corrected"])))
    verified_results = verified_res.scalar() or 0

    # Data quality issues open
    dq_res = await db.execute(select(func.count(DataQualityIssue.id)).where(DataQualityIssue.resolution_status == "open"))
    data_quality_issues = dq_res.scalar() or 0

    # Anomalies detected
    anom_res = await db.execute(select(func.count(AnomalyRecord.id)).where(AnomalyRecord.is_anomaly.is_(True)))
    statistical_anomalies = anom_res.scalar() or 0

    return DashboardSummary(
        total_patients=total_patients,
        total_samples=total_samples,
        total_tests=total_tests,
        completed_tests=completed_tests,
        pending_tests=pending_tests,
        verified_results=verified_results,
        data_quality_issues=data_quality_issues,
        statistical_anomalies=statistical_anomalies,
    )


@router.get("/charts", response_model=DashboardCharts)
async def get_dashboard_charts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return chart series data for laboratory operations and test distributions."""
    # 1. Sample status distribution
    status_q = await db.execute(
        select(Sample.status, func.count(Sample.id))
        .group_by(Sample.status)
    )
    status_dist = [
        SampleStatusDistribution(status=row[0], count=row[1])
        for row in status_q.all()
    ]

    # 2. Test category distribution
    cat_q = await db.execute(
        select(TestCategory.name, func.count(LaboratoryTest.id))
        .join(LaboratoryTest, LaboratoryTest.category_id == TestCategory.id)
        .group_by(TestCategory.name)
    )
    cat_dist = [
        CategoryDistribution(category_name=row[0], count=row[1])
        for row in cat_q.all()
    ]

    # 3. Monthly activity for the past 6 months
    monthly_activity: list[MonthlyTrend] = []
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        target_month_date = now - timedelta(days=i * 30)
        month_label = target_month_date.strftime("%b %Y")
        
        # Approximate 30-day window
        window_start = target_month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # 30 days after
        window_end = window_start + timedelta(days=31)

        s_cnt = await db.execute(
            select(func.count(Sample.id)).where(
                Sample.created_at >= window_start,
                Sample.created_at < window_end,
            )
        )
        r_cnt = await db.execute(
            select(func.count(TestResult.id)).where(
                TestResult.created_at >= window_start,
                TestResult.created_at < window_end,
            )
        )
        monthly_activity.append(
            MonthlyTrend(
                month=month_label,
                samples=s_cnt.scalar() or 0,
                results=r_cnt.scalar() or 0,
            )
        )

    return DashboardCharts(
        sample_status_distribution=status_dist,
        test_category_distribution=cat_dist,
        monthly_activity=monthly_activity,
    )


@router.get("/activity", response_model=list[ActivityItem])
async def get_recent_activity(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return recent operational events across samples and test results."""
    # Grab the 10 most recent samples
    samples_q = await db.execute(
        select(Sample).order_by(Sample.created_at.desc()).limit(10)
    )
    samples = samples_q.scalars().all()

    items: list[ActivityItem] = []
    for s in samples:
        items.append(
            ActivityItem(
                id=str(s.id),
                entity_type="sample",
                description=f"Sample {s.sample_code} ({s.sample_type}) registered with status '{s.status}'",
                timestamp=s.created_at,
                status=s.status,
            )
        )

    # Sort combined activity chronologically descending
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[:15]
