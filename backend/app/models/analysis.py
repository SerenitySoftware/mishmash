import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Analysis(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analyses"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)  # pip requirements.txt or R packages
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    star_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fork_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forked_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=True
    )

    owner = relationship("User", back_populates="analyses")
    forked_from = relationship("Analysis", remote_side="Analysis.id", foreign_keys=[forked_from_id])
    datasets = relationship("AnalysisDataset", back_populates="analysis", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="analysis", order_by="AnalysisRun.created_at.desc()")


class AnalysisDataset(Base):
    __tablename__ = "analysis_datasets"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True
    )
    version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alias: Mapped[str | None] = mapped_column(String(50), nullable=True)

    analysis = relationship("Analysis", back_populates="datasets")
    dataset = relationship("Dataset")


class AnalysisRun(Base, UUIDMixin):
    __tablename__ = "analysis_runs"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Proof of work fields
    pow_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pow_nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pow_verified: Mapped[bool | None] = mapped_column(default=False, nullable=True)
    environment_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    analysis = relationship("Analysis", back_populates="runs")
