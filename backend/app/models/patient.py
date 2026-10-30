"""Patient ORM model. Minimises PII, uses pseudonymous codes."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Patient(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    patient_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    biological_sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    samples: Mapped[list["Sample"]] = relationship("Sample", back_populates="patient")  # type: ignore[name-defined]
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])  # type: ignore[name-defined]
    updated_by: Mapped["User | None"] = relationship("User", foreign_keys=[updated_by_id])  # type: ignore[name-defined]
    archived_by: Mapped["User | None"] = relationship("User", foreign_keys=[archived_by_id])  # type: ignore[name-defined]

    __table_args__ = (Index("ix_patients_code_active", "patient_code", "is_active"),)

    def __repr__(self) -> str:
        return f"<Patient {self.patient_code}>"
