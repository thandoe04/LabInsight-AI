"""Laboratory test catalogue and reference interval ORM models."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TestCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "test_categories"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tests: Mapped[list["LaboratoryTest"]] = relationship("LaboratoryTest", back_populates="category")

    def __repr__(self) -> str:
        return f"<TestCategory {self.name}>"


class LaboratoryTest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Laboratory test definition, configured by authorised administrators.
    Not assumed to be identical across laboratories.
    """
    __tablename__ = "laboratory_tests"

    test_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_categories.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    measurement_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_type: Mapped[str] = mapped_column(String(16), nullable=False, default="numeric")
    allowed_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    category: Mapped["TestCategory"] = relationship("TestCategory", back_populates="tests")
    reference_ranges: Mapped[list["ReferenceRange"]] = relationship("ReferenceRange", back_populates="test")
    results: Mapped[list["TestResult"]] = relationship("TestResult", back_populates="test")  # type: ignore[name-defined]
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])  # type: ignore[name-defined]

    __table_args__ = (Index("ix_lab_tests_code_active", "test_code", "is_active"),)

    def __repr__(self) -> str:
        return f"<LaboratoryTest {self.test_code}>"


class ReferenceRange(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Configurable reference intervals.
    NOT invented by the software — configured by authorised admins with documented sources.
    Being outside a reference interval is a STATISTICAL FLAG, not a diagnosis.
    """
    __tablename__ = "reference_ranges"

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("laboratory_tests.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    applicable_sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    min_age_years: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    max_age_years: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    lower_limit: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    upper_limit: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qualitative_normal_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    authorised_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    authorised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    test: Mapped["LaboratoryTest"] = relationship("LaboratoryTest", back_populates="reference_ranges")
    authorised_by: Mapped["User | None"] = relationship("User", foreign_keys=[authorised_by_id])  # type: ignore[name-defined]

    __table_args__ = (Index("ix_ref_ranges_test_active", "test_id", "is_active"),)
