"""
Add data_packages table and free_data fields to users

Revision ID: 002_add_data_packages
Revises: 001_remove_unused_tables
Create Date: 2026-02-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002_add_data_packages'
down_revision: Union[str, None] = '001_remove_unused_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE package_type_enum AS ENUM ('basic', 'premium', 'unlimited')")

    op.create_table(
        'data_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('package_type', postgresql.ENUM('basic', 'premium', 'unlimited', name='package_type_enum', create_type=False), nullable=False),
        sa.Column('data_limit_bytes', sa.BigInteger(), nullable=False),
        sa.Column('data_used_bytes', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('stars_paid', sa.Integer(), nullable=False),
        sa.Column('purchased_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('telegram_payment_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='data_packages_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='data_packages_pkey')
    )

    op.create_index('ix_data_packages_user_id', 'data_packages', ['user_id'])
    op.create_index('ix_data_packages_is_active', 'data_packages', ['is_active'])

    op.add_column('users', sa.Column('free_data_limit_bytes', sa.BigInteger(), server_default='10737418240', nullable=False))
    op.add_column('users', sa.Column('free_data_used_bytes', sa.BigInteger(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'free_data_used_bytes')
    op.drop_column('users', 'free_data_limit_bytes')

    op.drop_index('ix_data_packages_is_active', table_name='data_packages')
    op.drop_index('ix_data_packages_user_id', table_name='data_packages')

    op.drop_table('data_packages')

    op.execute('DROP TYPE package_type_enum')
