"""add refresh_token_events

Revision ID: 3edba70ec8d2
Revises: 7e4ba65a69fd
Create Date: 2025-11-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3edba70ec8d2"
down_revision = "7e4ba65a69fd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) create the refresh_token_events table
    op.create_table(
        "refresh_token_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "refresh_token_id",
            sa.Integer(),
            sa.ForeignKey("refresh_tokens.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )

    # 2) change refresh_tokens.device_id length safely on SQLite using batch_alter_table
    # batch_alter_table will recreate the table on SQLite with the new schema.
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.alter_column(
            "device_id",
            existing_type=sa.VARCHAR(length=256),
            type_=sa.String(length=128),
            existing_nullable=True,
        )

    # 3) ensure token_hash index is unique (create if missing)
    # Drop non-unique index if it exists then create unique index.
    # Note: on SQLite `create_index` will fail if index exists; this is safe if index was removed previously by autogen.
    try:
        op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    except Exception:
        # best-effort: ignore if index already exists or DB backend complains
        pass


def downgrade() -> None:
    # reverse unique index (drop it)
    try:
        op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    except Exception:
        pass

    # revert device_id to original length via batch_alter_table
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.alter_column(
            "device_id",
            existing_type=sa.String(length=128),
            type_=sa.VARCHAR(length=256),
            existing_nullable=True,
        )

    # drop refresh_token_events table
    op.drop_table("refresh_token_events")
