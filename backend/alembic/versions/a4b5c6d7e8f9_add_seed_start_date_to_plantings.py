"""add seed_start_date to plantings

Revision ID: a4b5c6d7e8f9
Revises: d3e4f5a6b7c8
Create Date: 2026-09-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'plantings',
        sa.Column('seed_start_date', sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('plantings', 'seed_start_date')
