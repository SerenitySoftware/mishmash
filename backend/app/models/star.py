"""Stars for datasets and analyses."""
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Star(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stars"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'dataset' or 'analysis'
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    user = relationship("User", back_populates="stars")

    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_stars_user_target"),
    )
