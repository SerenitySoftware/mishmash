import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Dataset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "datasets"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default="{}", nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    row_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    column_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    star_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fork_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forked_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    owner = relationship("User", back_populates="datasets")
    forked_from = relationship("Dataset", remote_side="Dataset.id", foreign_keys=[forked_from_id])
    versions = relationship(
        "DatasetVersion", back_populates="dataset", order_by="DatasetVersion.version"
    )
    outgoing_refs = relationship(
        "DatasetReference",
        foreign_keys="DatasetReference.source_id",
        back_populates="source",
    )
    incoming_refs = relationship(
        "DatasetReference",
        foreign_keys="DatasetReference.target_id",
        back_populates="target",
    )


class DatasetVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    row_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    column_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    quality_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    change_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # diff vs previous version
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    dataset = relationship("Dataset", back_populates="versions")

    __table_args__ = (
        {"comment": "Immutable dataset version snapshots"},
    )


class DatasetReference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_references"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), default="derived_from", nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    source = relationship("Dataset", foreign_keys=[source_id], back_populates="outgoing_refs")
    target = relationship("Dataset", foreign_keys=[target_id], back_populates="incoming_refs")
