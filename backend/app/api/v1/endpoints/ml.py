"""
Machine Learning & Data Intelligence API endpoints.
Provides experiment management, anomaly detection runs, clustering analyses,
and human review workflows for detected defects and statistical anomalies.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.ml.anomaly_detection import run_anomaly_detection
from app.ml.clustering import run_clustering
from app.ml.data_quality import check_data_quality
from app.models.laboratory import LaboratoryTest
from app.models.ml import (
    AnomalyRecord,
    DataQualityIssue,
    Dataset,
    DatasetVersion,
    MLExperiment,
    MLModel,
    MLModelVersion,
    MLPrediction,
)
from app.models.result import TestResult
from app.models.sample import Sample
from app.security.dependencies import CurrentUser
from app.services.audit import record_audit_event

router = APIRouter()

CLINICAL_SAFETY_DISCLAIMER = (
    "SAFETY NOTICE: Machine Learning outputs are statistical patterns and anomaly scores. "
    "They are NOT clinical diagnoses and do not assess probability of disease. "
    "Review by qualified laboratory personnel is mandatory before any clinical interpretation."
)


# ─── Schemas ────────────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=256)
    experiment_type: str = Field(..., pattern="^(anomaly_detection|clustering|data_quality)$")
    algorithm: str = "isolation_forest"
    config: dict[str, Any] = Field(default_factory=dict)
    test_ids: list[uuid.UUID] = Field(default_factory=list)


class ExperimentResponse(BaseModel):
    id: str
    name: str
    experiment_type: str
    status: str
    config: dict | None
    results: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    disclaimer: str = CLINICAL_SAFETY_DISCLAIMER


class AnomalyReviewUpdate(BaseModel):
    review_status: str = Field(..., pattern="^(reviewed|dismissed|escalated)$")
    reviewer_notes: str = Field(..., min_length=3)


class AnomalyResponse(BaseModel):
    id: str
    experiment_id: str
    entity_type: str
    entity_id: str
    anomaly_score: float
    is_anomaly: bool
    detection_method: str
    contributing_features: dict | None
    review_status: str
    reviewer_notes: str | None
    reviewed_at: datetime | None
    created_at: datetime
    disclaimer: str = CLINICAL_SAFETY_DISCLAIMER


class DataQualityReviewUpdate(BaseModel):
    resolution_status: str = Field(..., pattern="^(resolved|dismissed|false_positive)$")
    resolution_notes: str = Field(..., min_length=3)


class DataQualityResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    field_name: str | None
    issue_type: str
    severity: str
    description: str
    proposed_correction: dict | None
    resolution_status: str
    resolution_notes: str | None
    resolved_at: datetime | None
    created_at: datetime


# ─── Experiments ────────────────────────────────────────────────────────────

@router.get("/experiments", response_model=list[ExperimentResponse])
async def list_experiments(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    experiment_type: str | None = None,
) -> Any:
    """List executed and configured ML experiments."""
    q = select(MLExperiment).order_by(MLExperiment.created_at.desc())
    if experiment_type:
        q = q.where(MLExperiment.experiment_type == experiment_type)
    res = await db.execute(q)
    exps = res.scalars().all()

    return [
        ExperimentResponse(
            id=str(e.id),
            name=e.name,
            experiment_type=e.experiment_type,
            status=e.status,
            config=e.config,
            results=e.results,
            error_message=e.error_message,
            started_at=e.started_at,
            completed_at=e.completed_at,
            created_at=e.created_at,
        )
        for e in exps
    ]


@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: Request,
    body: ExperimentCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new ML experiment configuration."""
    exp = MLExperiment(
        name=body.name,
        experiment_type=body.experiment_type,
        status="pending",
        config={
            "algorithm": body.algorithm,
            "test_ids": [str(t) for t in body.test_ids],
            **body.config,
        },
        created_by_id=current_user.id,
    )
    db.add(exp)
    await db.flush()

    await record_audit_event(
        db,
        action="ml.experiment.create",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="ml_experiment",
        entity_id=exp.id,
        request=request,
    )
    await db.commit()

    return ExperimentResponse(
        id=str(exp.id),
        name=exp.name,
        experiment_type=exp.experiment_type,
        status=exp.status,
        config=exp.config,
        results=None,
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=exp.created_at,
    )


@router.post("/experiments/{experiment_id}/run", response_model=ExperimentResponse)
async def run_experiment(
    experiment_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Execute the configured ML pipeline on current laboratory records."""
    q = select(MLExperiment).where(MLExperiment.id == experiment_id)
    exp = (await db.execute(q)).scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    exp.status = "running"
    exp.started_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        config = exp.config or {}
        test_ids_raw = config.get("test_ids", [])
        test_ids = [uuid.UUID(tid) for tid in test_ids_raw] if test_ids_raw else []

        # Pull laboratory test data
        results_q = select(TestResult).options(selectinload(TestResult.test), selectinload(TestResult.sample))
        if test_ids:
            results_q = results_q.where(TestResult.test_id.in_(test_ids))
        results_q = results_q.where(TestResult.numeric_value.is_not(None))
        raw_results = (await db.execute(results_q)).scalars().all()

        if exp.experiment_type == "anomaly_detection":
            if len(raw_results) < 5:
                raise ValueError("Insufficient laboratory results to perform anomaly detection (minimum 5 required).")

            # Pivot data by sample
            sample_map: dict[uuid.UUID, dict[str, float]] = {}
            test_names: dict[str, str] = {}
            for r in raw_results:
                t_code = r.test.test_code if r.test else str(r.test_id)
                test_names[t_code] = r.test.name if r.test else t_code
                if r.sample_id not in sample_map:
                    sample_map[r.sample_id] = {}
                sample_map[r.sample_id][t_code] = float(r.numeric_value)

            feature_names = sorted(list(test_names.keys()))
            X_rows: list[list[float]] = []
            sample_ids_ordered: list[uuid.UUID] = []

            for s_id, t_dict in sample_map.items():
                # Only use samples that have values for features or impute with column mean
                row = [t_dict.get(fname, 0.0) for fname in feature_names]
                X_rows.append(row)
                sample_ids_ordered.append(s_id)

            X = np.array(X_rows, dtype=np.float64)
            algorithm = config.get("algorithm", "isolation_forest")
            contamination = float(config.get("contamination", 0.1))

            det_results = run_anomaly_detection(
                features=X,
                feature_names=feature_names,
                algorithm=algorithm,
                contamination=contamination,
            )

            # Persist anomaly records in database
            for i, is_anom in enumerate(det_results["is_anomaly"]):
                if is_anom:
                    anom_record = AnomalyRecord(
                        experiment_id=exp.id,
                        entity_type="sample",
                        entity_id=sample_ids_ordered[i],
                        anomaly_score=det_results["anomaly_scores"][i],
                        is_anomaly=True,
                        detection_method=algorithm,
                        contributing_features=det_results["contributing_features"][i],
                        review_status="pending",
                    )
                    db.add(anom_record)

            exp.results = det_results["summary"]
            exp.status = "completed"
            exp.completed_at = datetime.now(timezone.utc)

        elif exp.experiment_type == "clustering":
            if len(raw_results) < 4:
                raise ValueError("Insufficient data to perform clustering analysis (minimum 4 samples required).")

            # Extract numeric array
            X_rows = [[float(r.numeric_value)] for r in raw_results]
            X = np.array(X_rows, dtype=np.float64)
            algorithm = config.get("algorithm", "kmeans")

            cluster_res = run_clustering(
                features=X,
                algorithm=algorithm,
                hyperparameters=config,
            )
            exp.results = cluster_res
            exp.status = "completed"
            exp.completed_at = datetime.now(timezone.utc)

        elif exp.experiment_type == "data_quality":
            # Pull samples and results to run rule audits
            records_to_check: list[dict] = []
            for r in raw_results:
                records_to_check.append({
                    "id": r.id,
                    "sample_id": r.sample_id,
                    "test_code": r.test.test_code if r.test else "",
                    "numeric_value": float(r.numeric_value) if r.numeric_value is not None else None,
                    "result_type": r.test.result_type if r.test else "numeric",
                    "collected_at": r.sample.collected_at if r.sample else None,
                    "received_at": r.sample.received_at if r.sample else None,
                    "measurement_unit": r.measurement_unit,
                })

            dq_issues = check_data_quality(records_to_check)
            for iss in dq_issues:
                dq_entry = DataQualityIssue(
                    entity_type=iss["entity_type"],
                    entity_id=iss["entity_id"],
                    field_name=iss["field_name"],
                    issue_type=iss["issue_type"],
                    severity=iss["severity"],
                    description=iss["description"],
                    proposed_correction=iss["proposed_correction"],
                    resolution_status="open",
                )
                db.add(dq_entry)

            exp.results = {
                "total_records_screened": len(records_to_check),
                "issues_detected": len(dq_issues),
                "severity_breakdown": {
                    "critical": sum(1 for i in dq_issues if i["severity"] == "critical"),
                    "warning": sum(1 for i in dq_issues if i["severity"] == "warning"),
                    "error": sum(1 for i in dq_issues if i["severity"] == "error"),
                },
            }
            exp.status = "completed"
            exp.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        exp.status = "failed"
        exp.error_message = str(e)
        exp.completed_at = datetime.now(timezone.utc)

    await db.flush()
    await record_audit_event(
        db,
        action="ml.experiment.run",
        outcome="success" if exp.status == "completed" else "failure",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="ml_experiment",
        entity_id=exp.id,
        metadata={"status": exp.status, "type": exp.experiment_type},
        request=request,
    )
    await db.commit()

    return ExperimentResponse(
        id=str(exp.id),
        name=exp.name,
        experiment_type=exp.experiment_type,
        status=exp.status,
        config=exp.config,
        results=exp.results,
        error_message=exp.error_message,
        started_at=exp.started_at,
        completed_at=exp.completed_at,
        created_at=exp.created_at,
    )


# ─── Anomaly Review ─────────────────────────────────────────────────────────

@router.get("/anomalies", response_model=list[AnomalyResponse])
async def list_anomalies(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    review_status: str | None = None,
) -> Any:
    """Retrieve detected statistical anomaly records with reviewer comments."""
    q = select(AnomalyRecord).order_by(AnomalyRecord.created_at.desc())
    if review_status:
        q = q.where(AnomalyRecord.review_status == review_status)
    res = await db.execute(q)
    anomalies = res.scalars().all()

    return [
        AnomalyResponse(
            id=str(a.id),
            experiment_id=str(a.experiment_id),
            entity_type=a.entity_type,
            entity_id=str(a.entity_id),
            anomaly_score=float(a.anomaly_score),
            is_anomaly=a.is_anomaly,
            detection_method=a.detection_method,
            contributing_features=a.contributing_features,
            review_status=a.review_status,
            reviewer_notes=a.reviewer_notes,
            reviewed_at=a.reviewed_at,
            created_at=a.created_at,
        )
        for a in anomalies
    ]


@router.patch("/anomalies/{anomaly_id}/review", response_model=AnomalyResponse)
async def review_anomaly(
    anomaly_id: uuid.UUID,
    body: AnomalyReviewUpdate,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record authorized professional human review of a flagged statistical anomaly."""
    q = select(AnomalyRecord).where(AnomalyRecord.id == anomaly_id)
    rec = (await db.execute(q)).scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Anomaly record not found.")

    rec.review_status = body.review_status
    rec.reviewer_notes = body.reviewer_notes
    rec.reviewed_by_id = current_user.id
    rec.reviewed_at = datetime.now(timezone.utc)
    await db.flush()

    await record_audit_event(
        db,
        action="ml.anomaly.review",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="anomaly_record",
        entity_id=rec.id,
        metadata={"review_status": body.review_status},
        request=request,
    )
    await db.commit()

    return AnomalyResponse(
        id=str(rec.id),
        experiment_id=str(rec.experiment_id),
        entity_type=rec.entity_type,
        entity_id=str(rec.entity_id),
        anomaly_score=float(rec.anomaly_score),
        is_anomaly=rec.is_anomaly,
        detection_method=rec.detection_method,
        contributing_features=rec.contributing_features,
        review_status=rec.review_status,
        reviewer_notes=rec.reviewer_notes,
        reviewed_at=rec.reviewed_at,
        created_at=rec.created_at,
    )


# ─── Data Quality Review ───────────────────────────────────────────────────

@router.get("/data-quality", response_model=list[DataQualityResponse])
async def list_data_quality_issues(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    resolution_status: str | None = None,
) -> Any:
    """List detected data quality issues."""
    q = select(DataQualityIssue).order_by(DataQualityIssue.created_at.desc())
    if resolution_status:
        q = q.where(DataQualityIssue.resolution_status == resolution_status)
    res = await db.execute(q)
    issues = res.scalars().all()

    return [
        DataQualityResponse(
            id=str(i.id),
            entity_type=i.entity_type,
            entity_id=str(i.entity_id),
            field_name=i.field_name,
            issue_type=i.issue_type,
            severity=i.severity,
            description=i.description,
            proposed_correction=i.proposed_correction,
            resolution_status=i.resolution_status,
            resolution_notes=i.resolution_notes,
            resolved_at=i.resolved_at,
            created_at=i.created_at,
        )
        for i in issues
    ]


@router.patch("/data-quality/{issue_id}/resolve", response_model=DataQualityResponse)
async def resolve_data_quality_issue(
    issue_id: uuid.UUID,
    body: DataQualityReviewUpdate,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record human review decision for a detected data quality issue."""
    q = select(DataQualityIssue).where(DataQualityIssue.id == issue_id)
    iss = (await db.execute(q)).scalar_one_or_none()
    if not iss:
        raise HTTPException(status_code=404, detail="Data quality issue not found.")

    iss.resolution_status = body.resolution_status
    iss.resolution_notes = body.resolution_notes
    iss.resolved_by_id = current_user.id
    iss.resolved_at = datetime.now(timezone.utc)
    await db.flush()

    await record_audit_event(
        db,
        action="dq.issue.resolve",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="data_quality_issue",
        entity_id=iss.id,
        metadata={"resolution_status": body.resolution_status},
        request=request,
    )
    await db.commit()

    return DataQualityResponse(
        id=str(iss.id),
        entity_type=iss.entity_type,
        entity_id=str(iss.entity_id),
        field_name=iss.field_name,
        issue_type=iss.issue_type,
        severity=iss.severity,
        description=iss.description,
        proposed_correction=iss.proposed_correction,
        resolution_status=iss.resolution_status,
        resolution_notes=iss.resolution_notes,
        resolved_at=iss.resolved_at,
        created_at=iss.created_at,
    )
