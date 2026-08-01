"""Add elasticsearch data source type

Revision ID: 002
Revises: 001
Create Date: 2026-08-01
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE datasourcetype ADD VALUE IF NOT EXISTS 'elasticsearch'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type
    pass
