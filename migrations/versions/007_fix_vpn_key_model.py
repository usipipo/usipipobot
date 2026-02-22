"""
Fix VpnKeyModel: rename last_used_at to last_seen_at, add missing fields

Revision ID: 007_fix_vpn_key_model
Revises: 006_add_missing_user_fields
Create Date: 2026-02-22 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '007_fix_vpn_key_model'
down_revision: Union[str, None] = '006_add_missing_user_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('vpn_keys', 'last_used_at', new_column_name='last_seen_at')
    
    op.add_column('vpn_keys', sa.Column('data_limit_bytes', sa.BigInteger(), server_default='10737418240', nullable=True))
    op.add_column('vpn_keys', sa.Column('billing_reset_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('vpn_keys', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('vpn_keys', 'expires_at')
    op.drop_column('vpn_keys', 'billing_reset_at')
    op.drop_column('vpn_keys', 'data_limit_bytes')
    op.alter_column('vpn_keys', 'last_seen_at', new_column_name='last_used_at')
