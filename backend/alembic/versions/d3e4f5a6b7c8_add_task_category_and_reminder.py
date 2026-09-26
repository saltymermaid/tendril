"""add category and push-reminder fields to tasks

Revision ID: d3e4f5a6b7c8
Revises: b7c8d9e0f1a2
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tasks',
        sa.Column('category', sa.String(20), nullable=False, server_default='general'),
    )
    op.add_column(
        'tasks',
        sa.Column('remind_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'tasks',
        sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('tasks', 'reminder_sent')
    op.drop_column('tasks', 'remind_at')
    op.drop_column('tasks', 'category')
