"""
Remove balance_stars and total_deposited columns

Revision ID: 009_remove_balance_fields
Revises: 008_business_model_v2
Create Date: 2026-02-22 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '009_remove_balance_fields'
down_revision: Union[str, None] = '008_business_model_v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'balance_stars')
    op.drop_column('users', 'total_deposited')


def downgrade() -> None:
    op.add_column('users', sa.Column('balance_stars', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('total_deposited', sa.Integer(), server_default='0', nullable=True))
