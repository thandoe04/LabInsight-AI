"""
Laboratory result ORM models.
Results are never silently overwritten — all corrections are versioned.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TestResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "test_results"

    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("laboratory_tests.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    numeric_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    qualitative_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    measurement_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Reference interval flags — NOT diagnoses
    is_above_upper_limit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_below_lower_limit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reference_range_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reference_ranges.id", ondelete="SET NULL"), nullable=True,
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    recorded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    sample: Mapped["Sample"] = relationship("Sample", back_populates="results")  # type: ignore[name-defined]
    test: Mapped["LaboratoryTest"] = relationship("LaboratoryTest", back_populates="results")  # type: ignore[name-defined]
    reference_range: Mapped["ReferenceRange | None"] = relationship("ReferenceRange", foreign_keys=[reference_range_id])  # type: ignore[name-defined]
    revisions: Mapped[list["ResultRevision"]] = relationship(
        "ResultRevision", back_populates="result", order_by="ResultRevision.revised_at",
    )
    verification: Mapped["ResultVerification | None"] = relationship(
        "ResultVerification", back_populates="result", uselist=False,
    )
    recorded_by: Mapped["User | None"] = relationship("User", foreign_keys=[recorded_by_id])  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_test_results_sample_test", "sample_id", "test_id"),
        Index("ix_test_results_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<TestResult sample={self.sample_id} test={self.test_id}>"


class ResultRevision(Base, UUIDPrimaryKeyMixin):
    """Immutable record of a result correction. Never deleted."""
    __tablename__ = "result_revisions"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_results.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    revision_number: Mapped[int] = mapped_column(nullable=False)
    previous_numeric_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    previous_qualitative_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    new_numeric_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    new_qualitative_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    revised_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    revised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    result: Mapped["TestResult"] = relationship("TestResult", back_populates="revisions")
    revised_by: Mapped["User | None"] = relationship("User", foreign_keys=[revised_by_id])  # type: ignore[name-defined]


class ResultVerification(Base, UUIDPrimaryKeyMixin):
    """Verification record. A verified result requires explicit revision with mandatory reason."""
    __tablename__ = "result_verifications"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_results.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    verified_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    result: Mapped["TestResult"] = relationship("TestResult", back_populates="verification")
    verified_by: Mapped["User"] = relationship("User", foreign_keys=[verified_by_id])  # type: ignore[name-defined]
