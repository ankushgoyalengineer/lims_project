"""add refresh_tokens

Revision ID: 7e4ba65a69fd
Revises: 6141594263a1
Create Date: 2025-11-21 23:xx:xx.xxxxxx
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7e4ba65a69fd'
down_revision: Union[str, Sequence[str], None] = '6141594263a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=512), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="refresh_tokens_user_id_fkey"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=False)

    # For SQLite use batch_alter_table to set NOT NULL on projects.created_at
    with op.batch_alter_table("projects", recreate='always') as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    # For users boolean columns change nullability (using batch_alter_table for SQLite safety)
    with op.batch_alter_table("users", recreate='always') as batch_op:
        batch_op.alter_column(
            "is_active",
            existing_type=sa.Boolean(),
            nullable=True,
            existing_server_default=sa.text("true"),
        )
        batch_op.alter_column(
            "is_superuser",
            existing_type=sa.Boolean(),
            nullable=True,
            existing_server_default=sa.text("false"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    # revert users columns
    with op.batch_alter_table("users", recreate='always') as batch_op:
        batch_op.alter_column(
            "is_superuser",
            existing_type=sa.Boolean(),
            nullable=False,
            existing_server_default=sa.text("false"),
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.Boolean(),
            nullable=False,
            existing_server_default=sa.text("true"),
        )

    # revert projects.created_at to nullable (use batch_alter_table as well)
    with op.batch_alter_table("projects", recreate='always') as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.TIMESTAMP(),
            nullable=True,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    # drop refresh_tokens and indexes
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
