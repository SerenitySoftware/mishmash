import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Publication(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "publications"

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    author = relationship("User", back_populates="publications")
    references = relationship(
        "PublicationReference", back_populates="publication", cascade="all, delete-orphan"
    )


class PublicationReference(Base):
    __tablename__ = "publication_references"

    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    ref_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    ref_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    publication = relationship("Publication", back_populates="references")
