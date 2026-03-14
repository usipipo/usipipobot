"""Add tickets tables

Revision ID: 20260302_add_tickets_tables
Revises: remove_tickets_table
Create Date: 2026-03-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260302_add_tickets_tables"
down_revision = "remove_tickets_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tickets and ticket_messages tables."""
    # Create tickets table
    op.create_table(
        "tickets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=15), server_default="open", nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.BigInteger(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.telegram_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for tickets
    op.create_index("idx_tickets_user_id", "tickets", ["user_id"])
    op.create_index("idx_tickets_status", "tickets", ["status"])
    op.create_index("idx_tickets_category", "tickets", ["category"])
    op.create_index("idx_tickets_priority", "tickets", ["priority"])
    op.create_index("idx_tickets_created_at", "tickets", ["created_at"])

    # Create ticket_messages table
    op.create_table(
        "ticket_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_from_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for ticket_messages
    op.create_index("idx_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])


def downgrade() -> None:
    """Drop tickets and ticket_messages tables."""
    op.drop_index("idx_ticket_messages_ticket_id", table_name="ticket_messages")
    op.drop_table("ticket_messages")
    op.drop_index("idx_tickets_created_at", table_name="tickets")
    op.drop_index("idx_tickets_priority", table_name="tickets")
    op.drop_index("idx_tickets_category", table_name="tickets")
    op.drop_index("idx_tickets_status", table_name="tickets")
    op.drop_index("idx_tickets_user_id", table_name="tickets")
    op.drop_table("tickets")
