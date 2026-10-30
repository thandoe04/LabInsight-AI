"""
Statistical Data Analytics API endpoints.
Provides robust descriptive statistics, distributions, correlations, and trends.
Includes explicit clinical disclaimers and data limitation indicators.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from scipy import stats
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.laboratory import LaboratoryTest, TestCategory
from app.models.result import TestResult
from app.models.sample import Sample
from app.security.dependencies import CurrentUser

router = APIRouter()

CLINICAL_DISCLAIMER = (
    "NOTICE: Statistical summary and analytics only. This is not a medical diagnostic tool, "
    "and correlation does not establish causation. Reference intervals and statistical metrics "
    "must be interpreted by qualified laboratory professionals."
)


class DescriptiveStatsResponse(BaseModel):
    test_id: str
    test_code: str
    test_name: str
    sample_count: int
    missing_count: int
    missing_percentage: float
    mean: float | None
    median: float | None
    std_dev: float | None
    variance: float | None
    min: float | None
    max: float | None
    q1: float | None
    q3: float | None
    iqr: float | None
    skewness: float | None
    kurtosis: float | None
    measurement_unit: str | None
    disclaimer: str = CLINICAL_DISCLAIMER


class DistributionBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int


class DistributionResponse(BaseModel):
    test_code: str
    bins: list[DistributionBin]
    total_records: int
    disclaimer: str = CLINICAL_DISCLAIMER


class CorrelationMatrixResponse(BaseModel):
    tests: list[str]
    matrix: list[list[float | None]]
    sample_overlap: int
    disclaimer: str = CLINICAL_DISCLAIMER


class TrendPoint(BaseModel):
    date: str
    average_value: float
    count: int


class TimeSeriesTrendResponse(BaseModel):
    test_code: str
    points: list[TrendPoint]
    disclaimer: str = CLINICAL_DISCLAIMER


@router.get("/statistics/{test_id}", response_model=DescriptiveStatsResponse)
async def get_test_statistics(
    test_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> Any:
    """Calculate comprehensive descriptive statistics for numeric test values."""
    t_res = await db.execute(select(LaboratoryTest).where(LaboratoryTest.id == test_id))
    test = t_res.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test definition not found.")

    query = select(TestResult.numeric_value).where(TestResult.test_id == test_id)
    if start_date:
        query = query.where(TestResult.measured_at >= start_date)
    if end_date:
        query = query.where(TestResult.measured_at <= end_date)

    result = await db.execute(query)
    raw_values = result.scalars().all()

    total_records = len(raw_values)
    valid_values = [float(v) for v in raw_values if v is not None]
    valid_count = len(valid_values)
    missing_count = total_records - valid_count
    missing_pct = round((missing_count / total_records * 100), 2) if total_records > 0 else 0.0

    if valid_count < 2:
        return DescriptiveStatsResponse(
            test_id=str(test.id),
            test_code=test.test_code,
            test_name=test.name,
            sample_count=valid_count,
            missing_count=missing_count,
            missing_percentage=missing_pct,
            mean=valid_values[0] if valid_count == 1 else None,
            median=valid_values[0] if valid_count == 1 else None,
            std_dev=None,
            variance=None,
            min=valid_values[0] if valid_count == 1 else None,
            max=valid_values[0] if valid_count == 1 else None,
            q1=valid_values[0] if valid_count == 1 else None,
            q3=valid_values[0] if valid_count == 1 else None,
            iqr=None,
            skewness=None,
            kurtosis=None,
            measurement_unit=test.measurement_unit,
        )

    arr = np.array(valid_values, dtype=np.float64)
    q1, median, q3 = np.percentile(arr, [25, 50, 75])
    iqr = q3 - q1

    # Skewness and kurtosis
    skew_val = float(stats.skew(arr)) if not math.isnan(stats.skew(arr)) else None
    kurt_val = float(stats.kurtosis(arr)) if not math.isnan(stats.kurtosis(arr)) else None

    return DescriptiveStatsResponse(
        test_id=str(test.id),
        test_code=test.test_code,
        test_name=test.name,
        sample_count=valid_count,
        missing_count=missing_count,
        missing_percentage=missing_pct,
        mean=round(float(np.mean(arr)), 4),
        median=round(float(median), 4),
        std_dev=round(float(np.std(arr, ddof=1)), 4),
        variance=round(float(np.var(arr, ddof=1)), 4),
        min=round(float(np.min(arr)), 4),
        max=round(float(np.max(arr)), 4),
        q1=round(float(q1), 4),
        q3=round(float(q3), 4),
        iqr=round(float(iqr), 4),
        skewness=round(skew_val, 4) if skew_val is not None else None,
        kurtosis=round(kurt_val, 4) if kurt_val is not None else None,
        measurement_unit=test.measurement_unit,
    )


@router.get("/distribution/{test_id}", response_model=DistributionResponse)
async def get_test_distribution(
    test_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    num_bins: int = Query(10, ge=3, le=50),
) -> Any:
    """Generate histogram bins for numeric test values."""
    t_res = await db.execute(select(LaboratoryTest).where(LaboratoryTest.id == test_id))
    test = t_res.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test definition not found.")

    res = await db.execute(
        select(TestResult.numeric_value).where(
            TestResult.test_id == test_id,
            TestResult.numeric_value.is_not(None),
        )
    )
    vals = [float(v) for v in res.scalars().all()]
    if not vals:
        return DistributionResponse(test_code=test.test_code, bins=[], total_records=0)

    arr = np.array(vals)
    counts, bin_edges = np.histogram(arr, bins=num_bins)

    bins: list[DistributionBin] = []
    for i in range(len(counts)):
        bins.append(
            DistributionBin(
                bin_start=round(float(bin_edges[i]), 2),
                bin_end=round(float(bin_edges[i + 1]), 2),
                count=int(counts[i]),
            )
        )

    return DistributionResponse(
        test_code=test.test_code,
        bins=bins,
        total_records=len(vals),
    )


@router.get("/correlations", response_model=CorrelationMatrixResponse)
async def get_correlation_matrix(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    test_ids: list[uuid.UUID] = Query(...),
) -> Any:
    """Compute Pearson correlation matrix across selected numeric tests on common samples."""
    if len(test_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 tests for correlation analysis.")

    # Retrieve tests metadata
    tests_res = await db.execute(select(LaboratoryTest).where(LaboratoryTest.id.in_(test_ids)))
    tests = {t.id: t.test_code for t in tests_res.scalars().all()}

    # Pull results
    res = await db.execute(
        select(TestResult.sample_id, TestResult.test_id, TestResult.numeric_value).where(
            TestResult.test_id.in_(test_ids),
            TestResult.numeric_value.is_not(None),
        )
    )
    rows = res.all()

    # Build DataFrame: rows = samples, columns = test_codes
    data_dict: dict[uuid.UUID, dict[str, float]] = {}
    for sample_id, t_id, val in rows:
        code = tests.get(t_id)
        if not code:
            continue
        if sample_id not in data_dict:
            data_dict[sample_id] = {}
        data_dict[sample_id][code] = float(val)

    test_codes = [tests[tid] for tid in test_ids if tid in tests]
    df = pd.DataFrame.from_dict(data_dict, orient="index")
    df = df.reindex(columns=test_codes)

    corr_df = df.corr(method="pearson")
    matrix: list[list[float | None]] = []
    for _, row in corr_df.iterrows():
        row_vals: list[float | None] = []
        for val in row:
            if math.isnan(val):
                row_vals.append(None)
            else:
                row_vals.append(round(float(val), 3))
        matrix.append(row_vals)

    return CorrelationMatrixResponse(
        tests=test_codes,
        matrix=matrix,
        sample_overlap=len(df.dropna()),
    )


@router.get("/trends/{test_id}", response_model=TimeSeriesTrendResponse)
async def get_time_series_trends(
    test_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Aggregated average values by month for time-series trend visualisation."""
    t_res = await db.execute(select(LaboratoryTest).where(LaboratoryTest.id == test_id))
    test = t_res.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test definition not found.")

    res = await db.execute(
        select(
            func.date_trunc("month", TestResult.measured_at).label("month"),
            func.avg(TestResult.numeric_value).label("avg_val"),
            func.count(TestResult.id).label("cnt"),
        )
        .where(
            TestResult.test_id == test_id,
            TestResult.numeric_value.is_not(None),
        )
        .group_by("month")
        .order_by("month")
    )
    rows = res.all()

    points: list[TrendPoint] = []
    for r in rows:
        points.append(
            TrendPoint(
                date=r.month.strftime("%b %Y") if r.month else "",
                average_value=round(float(r.avg_val), 3) if r.avg_val else 0.0,
                count=int(r.cnt),
            )
        )

    return TimeSeriesTrendResponse(test_code=test.test_code, points=points)
