from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    datasets = relationship("Dataset", back_populates="owner", lazy="selectin")
    analyses = relationship("Analysis", back_populates="owner", lazy="selectin")
    comments = relationship("Comment", back_populates="author", lazy="selectin")
    publications = relationship("Publication", back_populates="author", lazy="selectin")
