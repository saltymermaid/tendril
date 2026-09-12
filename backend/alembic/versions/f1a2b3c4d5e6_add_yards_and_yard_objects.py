"""add yards and yard_objects

Revision ID: f1a2b3c4d5e6
Revises: e3f4a5b6c7d8
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'yards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'yard_objects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('yard_id', sa.Integer(), nullable=False),
        sa.Column('object_type', sa.String(length=20), nullable=False),
        sa.Column('container_id', sa.Integer(), nullable=True),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('square_x', sa.Integer(), nullable=False),
        sa.Column('square_y', sa.Integer(), nullable=False),
        sa.Column('square_width', sa.Integer(), nullable=True),
        sa.Column('square_height', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['yard_id'], ['yards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['container_id'], ['containers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('container_id', name='uq_yard_objects_container_id'),
    )


def downgrade() -> None:
    op.drop_table('yard_objects')
    op.drop_table('yards')
