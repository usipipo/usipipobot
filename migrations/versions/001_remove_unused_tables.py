"""
Remove unused tables: achievements, user_achievements, user_stats, tasks, 
user_tasks, tickets, ai_conversations, transactions

Revision ID: 001
Revises: 
Create Date: 2026-02-18 19:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_remove_unused_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop unused tables.
    
    Order matters due to foreign key constraints:
    1. First drop child tables with FKs (user_achievements, user_tasks)
    2. Then drop parent tables (achievements, tasks, user_stats, tickets, ai_conversations, transactions)
    """
    op.drop_table('user_achievements', if_exists=True)
    op.drop_table('user_stats', if_exists=True)
    op.drop_table('achievements', if_exists=True)
    op.drop_table('user_tasks', if_exists=True)
    op.drop_table('tasks', if_exists=True)
    op.drop_table('tickets', if_exists=True)
    op.drop_table('ai_conversations', if_exists=True)
    op.drop_table('transactions', if_exists=True)


def downgrade() -> None:
    """
    Recreate all dropped tables (for rollback capability).
    
    Reverse order of upgrade:
    1. First create parent tables
    2. Then create child tables with FKs
    """
    # Create parent tables first
    
    # achievements table
    op.create_table(
        'achievements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('tier', sa.String(), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=False),
        sa.Column('reward_stars', sa.Integer(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='achievements_pkey')
    )
    
    # user_stats table
    op.create_table(
        'user_stats',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('total_data_consumed_gb', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('days_active', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_referrals', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_stars_deposited', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_keys_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_games_won', sa.Integer(), server_default='0', nullable=False),
        sa.Column('vip_months_purchased', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_active_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='user_stats_user_id_fkey'),
        sa.PrimaryKeyConstraint('user_id', name='user_stats_pkey')
    )
    
    # tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reward_stars', sa.Integer(), nullable=False),
        sa.Column('guide_text', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.telegram_id'], ondelete='SET NULL', name='tasks_created_by_fkey'),
        sa.PrimaryKeyConstraint('id', name='tasks_pkey')
    )
    
    # tickets table
    op.create_table(
        'tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('user_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='tickets_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='tickets_pkey')
    )
    
    # ai_conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('user_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='active', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('messages', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='ai_conversations_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='ai_conversations_pkey')
    )
    
    # transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('telegram_payment_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='transactions_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='transactions_pkey')
    )
    
    # Create child tables with foreign keys
    
    # user_achievements table
    op.create_table(
        'user_achievements',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('achievement_id', sa.String(), nullable=False),
        sa.Column('current_value', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reward_claimed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('reward_claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE', name='user_achievements_achievement_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='user_achievements_user_id_fkey'),
        sa.PrimaryKeyConstraint('user_id', 'achievement_id', name='user_achievements_pkey')
    )
    
    # user_tasks table
    op.create_table(
        'user_tasks',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reward_claimed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('reward_claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE', name='user_tasks_task_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE', name='user_tasks_user_id_fkey'),
        sa.PrimaryKeyConstraint('user_id', 'task_id', name='user_tasks_pkey')
    )
