"""
Add missing user fields: status, role, max_keys, balance_stars, etc.

Revision ID: 006_add_missing_user_fields
Revises: 005_add_transactions
Create Date: 2026-02-22 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '006_add_missing_user_fields'
down_revision: Union[str, None] = '005_add_transactions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('status', sa.String(), server_default='active', nullable=True))
    op.add_column('users', sa.Column('role', sa.String(), server_default='user', nullable=True))
    op.add_column('users', sa.Column('max_keys', sa.Integer(), server_default='2', nullable=True))
    op.add_column('users', sa.Column('balance_stars', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('total_deposited', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('referral_code', sa.String(), nullable=True))
    op.add_column('users', sa.Column('referred_by', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('total_referral_earnings', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('is_vip', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('users', sa.Column('vip_expires_at', sa.DateTime(timezone=True), nullable=True))
    
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)
    op.create_index('ix_users_referred_by', 'users', ['referred_by'])


def downgrade() -> None:
    op.drop_index('ix_users_referred_by', table_name='users')
    op.drop_index('ix_users_referral_code', table_name='users')
    op.drop_column('users', 'vip_expires_at')
    op.drop_column('users', 'is_vip')
    op.drop_column('users', 'total_referral_earnings')
    op.drop_column('users', 'referred_by')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'total_deposited')
    op.drop_column('users', 'balance_stars')
    op.drop_column('users', 'max_keys')
    op.drop_column('users', 'role')
    op.drop_column('users', 'status')
