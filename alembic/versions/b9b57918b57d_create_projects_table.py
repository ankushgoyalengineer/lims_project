"""create projects table

Revision ID: b9b57918b57d
Revises: 35504c57cc7c
Create Date: 2025-10-24 20:37:51.543925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b9b57918b57d'
down_revision: Union[str, Sequence[str], None] = '35504c57cc7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # create projects table only
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="projects_owner_id_fkey"),
        postgresql_ignore_search_path=False,
    )
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_projects_id"), table_name="projects")
    op.drop_table("projects")

