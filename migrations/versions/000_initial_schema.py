"""
Initial schema: users and vpn_keys tables

Revision ID: 000_initial_schema
Revises: 
Create Date: 2026-02-21 22:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '000_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('language_code', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('telegram_id', name='users_pkey')
    )

    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    op.execute("CREATE TYPE key_type_enum AS ENUM ('wireguard', 'outline')")

    op.create_table(
        'vpn_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('key_type', postgresql.ENUM('wireguard', 'outline', name='key_type_enum', create_type=False), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_data', sa.String(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('used_bytes', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='vpn_keys_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='vpn_keys_pkey')
    )

    op.create_index('ix_vpn_keys_user_id', 'vpn_keys', ['user_id'])
    op.create_index('ix_vpn_keys_is_active', 'vpn_keys', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_vpn_keys_is_active', table_name='vpn_keys')
    op.drop_index('ix_vpn_keys_user_id', table_name='vpn_keys')
    op.drop_table('vpn_keys')
    op.execute('DROP TYPE key_type_enum')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')
