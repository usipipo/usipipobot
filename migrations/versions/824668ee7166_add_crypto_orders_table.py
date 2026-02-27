"""Add crypto_orders table

Revision ID: 824668ee7166
Revises: 6c2bf050c380
Create Date: 2026-02-26 09:11:22.955585

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "824668ee7166"
down_revision: Union[str, Sequence[str], None] = "6c2bf050c380"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first
    crypto_order_status = sa.Enum(
        "pending", "completed", "failed", "expired", name="crypto_order_status"
    )
    crypto_order_status.create(op.get_bind(), checkfirst=True)

    # Create the crypto_orders table
    op.create_table(
        "crypto_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "package_type", sa.String(length=50), nullable=False, server_default="basic"
        ),
        sa.Column("amount_usdt", sa.Float(), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("tron_dealer_order_id", sa.String(length=100), nullable=True),
        sa.Column(
            "status", crypto_order_status, nullable=False, server_default="pending"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_crypto_orders_user_id", "crypto_orders", ["user_id"])
    op.create_index(
        "ix_crypto_orders_wallet_address", "crypto_orders", ["wallet_address"]
    )
    op.create_index("ix_crypto_orders_status", "crypto_orders", ["status"])
    op.create_index("ix_crypto_orders_expires_at", "crypto_orders", ["expires_at"])
    op.create_index("ix_crypto_orders_tx_hash", "crypto_orders", ["tx_hash"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index("ix_crypto_orders_tx_hash", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_expires_at", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_status", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_wallet_address", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_user_id", table_name="crypto_orders")

    # Drop the table
    op.drop_table("crypto_orders")

    # Drop the enum type
    crypto_order_status = sa.Enum(
        "pending", "completed", "failed", "expired", name="crypto_order_status"
    )
    crypto_order_status.drop(op.get_bind(), checkfirst=True)
