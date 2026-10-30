"""ML dataset, model, experiment, prediction, anomaly and data quality ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[str] = mapped_column(Text, nullable=False)
    licence: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    registered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    versions: Mapped[list["DatasetVersion"]] = relationship("DatasetVersion", back_populates="dataset")
    registered_by: Mapped["User | None"] = relationship("User", foreign_keys=[registered_by_id])  # type: ignore[name-defined]


class DatasetVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    version_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feature_names: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="versions")


class MLModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ml_models"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    versions: Mapped[list["MLModelVersion"]] = relationship("MLModelVersion", back_populates="model")
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])  # type: ignore[name-defined]


class MLModelVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ml_model_versions"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    version_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True,
    )
    hyperparameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feature_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preprocessing_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evaluation_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    train_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Controlled internal registry — NOT arbitrary user uploads
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    artifact_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trained_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    model: Mapped["MLModel"] = relationship("MLModel", back_populates="versions")
    trained_by: Mapped["User | None"] = relationship("User", foreign_keys=[trained_by_id])  # type: ignore[name-defined]


class MLExperiment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ml_experiments"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    experiment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    dataset_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True,
    )
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_model_versions.id", ondelete="SET NULL"), nullable=True,
    )
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])  # type: ignore[name-defined]
    predictions: Mapped[list["MLPrediction"]] = relationship("MLPrediction", back_populates="experiment")

    __table_args__ = (Index("ix_ml_experiments_type_status", "experiment_type", "status"),)


class MLPrediction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ml_predictions"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_experiments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_model_versions.id", ondelete="SET NULL"), nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    prediction_value: Mapped[dict | None] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)

    experiment: Mapped["MLExperiment"] = relationship("MLExperiment", back_populates="predictions")

    __table_args__ = (Index("ix_ml_predictions_entity", "entity_type", "entity_id"),)


class AnomalyRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    IMPORTANT: anomaly_score is a STATISTICAL SIGNAL, NOT a clinical diagnosis.
    All anomaly records require human review by qualified personnel.
    """
    __tablename__ = "anomaly_records"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_experiments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detection_method: Mapped[str] = mapped_column(String(64), nullable=False)
    contributing_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewed_by: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by_id])  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_anomaly_records_entity", "entity_type", "entity_id"),
        Index("ix_anomaly_records_review_status", "review_status"),
    )


class DataQualityIssue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Proposed corrections NEVER applied automatically — require authorised human review."""
    __tablename__ = "data_quality_issues"

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="warning")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_correction: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolved_by: Mapped["User | None"] = relationship("User", foreign_keys=[resolved_by_id])  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_dq_issues_entity", "entity_type", "entity_id"),
        Index("ix_dq_issues_status_severity", "resolution_status", "severity"),
    )
