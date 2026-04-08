"""Add API keys and notifications

Revision ID: 003
Revises: 002
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # API keys
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_api_keys_user", "api_keys", ["user_id"])
    op.create_index("idx_api_keys_hash", "api_keys", ["key_hash"])

    # Notifications
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("is_read", sa.Boolean, server_default="false", nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("meta", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_notifications_user_unread", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_user_created", "notifications", ["user_id", "created_at"])

    # Add missing performance indexes from audit
    op.create_index("idx_dataset_versions_dataset", "dataset_versions", ["dataset_id"])
    op.create_index("idx_analysis_runs_analysis", "analysis_runs", ["analysis_id"])
    op.create_index("idx_datasets_owner", "datasets", ["owner_id"])
    op.create_index("idx_analyses_owner", "analyses", ["owner_id"])


def downgrade() -> None:
    op.drop_index("idx_analyses_owner")
    op.drop_index("idx_datasets_owner")
    op.drop_index("idx_analysis_runs_analysis")
    op.drop_index("idx_dataset_versions_dataset")
    op.drop_index("idx_notifications_user_created")
    op.drop_index("idx_notifications_user_unread")
    op.drop_table("notifications")
    op.drop_index("idx_api_keys_hash")
    op.drop_index("idx_api_keys_user")
    op.drop_table("api_keys")
