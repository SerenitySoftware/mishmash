"""Add environment pinning, quality profiles, changelogs

Revision ID: 004
Revises: 003
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Analysis environment pinning
    op.add_column("analyses", sa.Column("requirements", sa.Text, nullable=True))

    # Dataset version quality and changelog
    op.add_column("dataset_versions", sa.Column("quality_profile", JSONB, nullable=True))
    op.add_column("dataset_versions", sa.Column("change_summary", JSONB, nullable=True))
    op.add_column("dataset_versions", sa.Column("changelog", sa.Text, nullable=True))

    # GIN indexes for full-text search on analyses and publications
    op.execute(
        "CREATE INDEX idx_analyses_search ON analyses "
        "USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')))"
    )
    op.execute(
        "CREATE INDEX idx_publications_search ON publications "
        "USING GIN (to_tsvector('english', title || ' ' || COALESCE(body, '')))"
    )


def downgrade() -> None:
    op.drop_index("idx_publications_search")
    op.drop_index("idx_analyses_search")
    op.drop_column("dataset_versions", "changelog")
    op.drop_column("dataset_versions", "change_summary")
    op.drop_column("dataset_versions", "quality_profile")
    op.drop_column("analyses", "requirements")
