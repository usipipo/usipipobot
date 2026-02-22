"""add tickets table

Revision ID: 007
Revises: 006_add_missing_user_fields
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_tickets_table'
down_revision = '006_add_missing_user_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), server_default='open'),
        sa.Column('priority', sa.String(), server_default='medium'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.BigInteger(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
    )
    
    op.create_index('ix_tickets_user_id', 'tickets', ['user_id'])
    op.create_index('ix_tickets_status', 'tickets', ['status'])


def downgrade():
    op.drop_index('ix_tickets_status', table_name='tickets')
    op.drop_index('ix_tickets_user_id', table_name='tickets')
    op.drop_table('tickets')
