"""SQLAlchemy models for jobs and their requirements."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentaudit.adapters.db.base import Base
from talentaudit.domain.enums import JobStatus


class JobModel(Base):
    """Persisted recruiter-created job policy."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.DRAFT.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    requirements: Mapped[list[RequirementModel]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="RequirementModel.position",
    )


class RequirementModel(Base):
    """Persisted required or preferred skill."""

    __tablename__ = "job_requirements"
    __table_args__ = (
        UniqueConstraint("job_id", "skill", name="uq_job_requirement_skill"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    min_years: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1)

    job: Mapped[JobModel] = relationship(back_populates="requirements")
