"""Add auth, social features, proof of work

Revision ID: 002
Revises: 001
Create Date: 2026-04-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User auth fields
    op.add_column("users", sa.Column("username", sa.String(100), unique=True, nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text, nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean, server_default="true", nullable=False))

    # Dataset social fields
    op.add_column("datasets", sa.Column("license", sa.String(100), nullable=True))
    op.add_column("datasets", sa.Column("is_public", sa.Boolean, server_default="true", nullable=False))
    op.add_column("datasets", sa.Column("star_count", sa.Integer, server_default="0", nullable=False))
    op.add_column("datasets", sa.Column("fork_count", sa.Integer, server_default="0", nullable=False))
    op.add_column("datasets", sa.Column("download_count", sa.Integer, server_default="0", nullable=False))
    op.add_column("datasets", sa.Column(
        "forked_from_id", UUID(as_uuid=True),
        sa.ForeignKey("datasets.id"), nullable=True,
    ))

    # Analysis social + PoW fields
    op.add_column("analyses", sa.Column("star_count", sa.Integer, server_default="0", nullable=False))
    op.add_column("analyses", sa.Column("fork_count", sa.Integer, server_default="0", nullable=False))
    op.add_column("analyses", sa.Column(
        "forked_from_id", UUID(as_uuid=True),
        sa.ForeignKey("analyses.id"), nullable=True,
    ))

    # Analysis run PoW fields
    op.add_column("analysis_runs", sa.Column("pow_hash", sa.String(128), nullable=True))
    op.add_column("analysis_runs", sa.Column("pow_nonce", sa.String(64), nullable=True))
    op.add_column("analysis_runs", sa.Column("pow_verified", sa.Boolean, server_default="false", nullable=True))
    op.add_column("analysis_runs", sa.Column("environment_hash", sa.String(128), nullable=True))

    # Stars table
    op.create_table(
        "stars",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "target_type", "target_id", name="uq_stars_user_target"),
    )
    op.create_index("idx_stars_target", "stars", ["target_type", "target_id"])


def downgrade() -> None:
    op.drop_index("idx_stars_target")
    op.drop_table("stars")

    op.drop_column("analysis_runs", "environment_hash")
    op.drop_column("analysis_runs", "pow_verified")
    op.drop_column("analysis_runs", "pow_nonce")
    op.drop_column("analysis_runs", "pow_hash")

    op.drop_column("analyses", "forked_from_id")
    op.drop_column("analyses", "fork_count")
    op.drop_column("analyses", "star_count")

    op.drop_column("datasets", "forked_from_id")
    op.drop_column("datasets", "download_count")
    op.drop_column("datasets", "fork_count")
    op.drop_column("datasets", "star_count")
    op.drop_column("datasets", "is_public")
    op.drop_column("datasets", "license")

    op.drop_column("users", "is_active")
    op.drop_column("users", "bio")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
