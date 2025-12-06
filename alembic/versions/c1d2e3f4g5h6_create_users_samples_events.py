"""create users, samples, events tables

Revision ID: c1d2e3f4g5h6
Revises: b9b57918b57d
Create Date: 2025-11-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4g5h6"
down_revision: Union[str, Sequence[str], None] = "b9b57918b57d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=250), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=256), nullable=False),
        sa.Column("full_name", sa.String(length=250), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # samples table
    op.create_table(
        "samples",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("barcode", sa.String(length=128), nullable=False, unique=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("sample_type", sa.String(length=100), nullable=True),
        sa.Column("metadata_json", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="samples_project_id_fkey"),
        postgresql_ignore_search_path=False,
    )
    op.create_index(op.f("ix_samples_id"), "samples", ["id"], unique=False)
    op.create_index(op.f("ix_samples_barcode"), "samples", ["barcode"], unique=True)

    # events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_table("events")

    op.drop_index(op.f("ix_samples_barcode"), table_name="samples")
    op.drop_index(op.f("ix_samples_id"), table_name="samples")
    op.drop_table("samples")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
