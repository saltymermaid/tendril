"""add seed_start_days to varieties

Revision ID: c1d2e3f4a5b6
Revises: a30778483dfc
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a30778483dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'varieties',
        sa.Column('seed_start_days', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('varieties', 'seed_start_days')
