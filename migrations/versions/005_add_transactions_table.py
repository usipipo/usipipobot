"""
Add transactions table

Revision ID: 005_add_transactions
Revises: 004_update_package_type_enum
Create Date: 2026-02-21 22:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '005_add_transactions'
down_revision: Union[str, None] = '004_update_package_type_enum'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('telegram_payment_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='transactions_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='transactions_pkey')
    )

    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_type', 'transactions', ['transaction_type'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_transactions_created_at', table_name='transactions')
    op.drop_index('ix_transactions_type', table_name='transactions')
    op.drop_index('ix_transactions_user_id', table_name='transactions')
    op.drop_table('transactions')
