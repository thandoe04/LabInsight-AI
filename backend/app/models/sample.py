"""Sample registration and status tracking ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

SAMPLE_STATUSES = frozenset({
    "registered", "collected", "received", "processing",
    "completed", "rejected", "archived",
})

VALID_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "registered": frozenset({"collected", "rejected"}),
    "collected": frozenset({"received", "rejected"}),
    "received": frozenset({"processing", "rejected"}),
    "processing": frozenset({"completed", "rejected"}),
    "completed": frozenset({"archived"}),
    "rejected": frozenset({"archived"}),
    "archived": frozenset(),
}


class Sample(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "samples"

    sample_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    sample_type: Mapped[str] = mapped_column(String(64), nullable=False)
    collection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="registered", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    patient: Mapped["Patient"] = relationship("Patient", back_populates="samples")  # type: ignore[name-defined]
    status_history: Mapped[list["SampleStatusHistory"]] = relationship(
        "SampleStatusHistory", back_populates="sample",
        order_by="SampleStatusHistory.changed_at",
    )
    results: Mapped[list["TestResult"]] = relationship("TestResult", back_populates="sample")  # type: ignore[name-defined]
    registered_by: Mapped["User | None"] = relationship("User", foreign_keys=[registered_by_id])  # type: ignore[name-defined]

    __table_args__ = (Index("ix_samples_patient_status", "patient_id", "status"),)

    def __repr__(self) -> str:
        return f"<Sample {self.sample_code}>"


class SampleStatusHistory(Base, UUIDPrimaryKeyMixin):
    """Immutable record of sample status transitions."""
    __tablename__ = "sample_status_history"

    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped["Sample"] = relationship("Sample", back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship("User", foreign_keys=[changed_by_id])  # type: ignore[name-defined]
