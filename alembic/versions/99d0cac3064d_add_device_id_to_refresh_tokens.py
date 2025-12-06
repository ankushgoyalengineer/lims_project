"""add device_id to refresh_tokens

Revision ID: 99d0cac3064d
Revises: 6cfba6863f88
Create Date: 2025-12-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "99d0cac3064d"
down_revision = "6cfba6863f88"
branch_labels = None
depends_on = None


def _column_exists(conn, table, col):
    # PRAGMA table_info does not accept bound parameters for the table name.
    # We format the table name into the SQL string. The table name is static in our usage.
    cur = conn.execute(sa.text(f"PRAGMA table_info({table})"))
    cols = [r[1] for r in cur.fetchall()]
    return col in cols


def _index_exists(conn, index_name):
    cur = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": index_name},
    )
    return cur.fetchone() is not None


def upgrade():
    bind = op.get_bind()

    # add column if missing
    if not _column_exists(bind, "refresh_tokens", "device_id"):
        with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
            batch_op.add_column(sa.Column("device_id", sa.String(length=128), nullable=True))

    # create index only if missing
    if not _index_exists(bind, "ix_refresh_tokens_device_id"):
        op.create_index("ix_refresh_tokens_device_id", "refresh_tokens", ["device_id"], unique=False)


def downgrade():
    bind = op.get_bind()
    if _index_exists(bind, "ix_refresh_tokens_device_id"):
        try:
            op.drop_index("ix_refresh_tokens_device_id", table_name="refresh_tokens")
        except Exception:
            pass
    # skipping DROP COLUMN for sqlite in downgrade
