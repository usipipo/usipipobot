"""Consolidated schema - All tables and fixes

Revision ID: 001_consolidated_schema
Revises:
Create Date: 2026-03-17

This is a consolidated migration that replaces all previous migrations.
It represents the current state of the database schema as of March 17, 2026.

Previous migrations consolidated:
- 000_initial_consolidated: Initial consolidated schema
- 4adf62d6a62f: Add user bonus tracking fields
- 5c8f2a9b1d3e: Add consumption billing tables
- remove_tickets_table: Remove tickets table (reverted)
- 20260302_add_tickets_tables: Add tickets tables
- add_subscriptions_001: Add subscription plans tables
- fix_crypto_int32_001: Fix crypto_orders and crypto_transactions user_id type
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_consolidated_schema"
down_revision = None  # This is now the first migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with current schema."""

    # Create users table
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("language_code", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("status", sa.String(), server_default="active", nullable=True),
        sa.Column("role", sa.String(), server_default="user", nullable=True),
        sa.Column("max_keys", sa.Integer(), server_default="2", nullable=False),
        sa.Column("referral_code", sa.String(), nullable=True),
        sa.Column("referred_by", sa.BigInteger(), nullable=True),
        sa.Column("referral_credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("wallet_address", sa.String(), nullable=True),
        sa.Column(
            "free_data_limit_bytes", sa.BigInteger(), server_default="10737418240", nullable=False
        ),
        sa.Column("free_data_used_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("purchase_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("loyalty_bonus_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("welcome_bonus_used", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("referred_users_with_purchase", sa.Integer(), server_default="0", nullable=False),
        sa.Column("consumption_mode_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("has_pending_debt", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("current_billing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("consumption_mode_activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("telegram_id"),
    )

    # Create vpn_keys table
    op.create_table(
        "vpn_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "key_type", sa.Enum("wireguard", "outline", name="key_type_enum"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_data", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("used_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "data_limit_bytes", sa.BigInteger(), server_default="10737418240", nullable=False
        ),
        sa.Column(
            "billing_reset_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vpn_keys_user_id", "vpn_keys", ["user_id"])

    # Create data_packages table
    op.create_table(
        "data_packages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "package_type",
            sa.Enum(
                "basic", "estandar", "avanzado", "premium", "unlimited", name="package_type_enum"
            ),
            nullable=False,
        ),
        sa.Column("data_limit_bytes", sa.BigInteger(), nullable=False),
        sa.Column("data_used_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("stars_paid", sa.Integer(), nullable=False),
        sa.Column(
            "purchased_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("telegram_payment_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_packages_user_id", "data_packages", ["user_id"])

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=True),
        sa.Column("telegram_payment_id", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

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
        sa.Column(
            "status",
            sa.Enum("open", "closed", "pending", name="ticket_status_enum"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["closed_by"], ["users.telegram_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_user_id", "tickets", ["user_id"])

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
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_from_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])
    op.create_index("ix_ticket_messages_user_id", "ticket_messages", ["user_id"])

    # Create consumption_billings table
    op.create_table(
        "consumption_billings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("cycle_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cycle_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_bytes_consumed", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("total_amount_stars", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "completed", "failed", name="consumption_billing_status_enum"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consumption_billings_user_id", "consumption_billings", ["user_id"])

    # Create consumption_invoices table
    op.create_table(
        "consumption_invoices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("billing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bytes_consumed", sa.BigInteger(), nullable=False),
        sa.Column("amount_stars", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "paid", "failed", name="consumption_invoice_status_enum"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["billing_id"], ["consumption_billings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consumption_invoices_user_id", "consumption_invoices", ["user_id"])
    op.create_index("ix_consumption_invoices_billing_id", "consumption_invoices", ["billing_id"])

    # Create subscription_plans table
    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_type", sa.String(length=20), nullable=False),
        sa.Column("stars_paid", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.String(length=255), nullable=False),
        sa.Column(
            "starts_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscription_plans_user_id", "subscription_plans", ["user_id"])

    # Create crypto_orders table (with BIGINT user_id - fix_crypto_int32_001)
    op.create_table(
        "crypto_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("package_type", sa.String(length=50), nullable=False, default="basic"),
        sa.Column("amount_usdt", sa.Float(), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("tron_dealer_order_id", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "completed", "failed", "expired", name="crypto_order_status"),
            nullable=False,
            default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crypto_orders_user_id", "crypto_orders", ["user_id"])
    op.create_index("ix_crypto_orders_wallet_address", "crypto_orders", ["wallet_address"])
    op.create_index("ix_crypto_orders_status", "crypto_orders", ["status"])
    op.create_index("ix_crypto_orders_expires_at", "crypto_orders", ["expires_at"])
    op.create_index("ix_crypto_orders_tx_hash", "crypto_orders", ["tx_hash"])

    # Create crypto_transactions table (with BIGINT user_id - fix_crypto_int32_001)
    op.create_table(
        "crypto_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("token_symbol", sa.String(length=10), nullable=False, default="USDT"),
        sa.Column("tx_hash", sa.String(length=66), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "failed", name="crypto_tx_status"),
            nullable=False,
            default="pending",
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tx_hash"),
    )
    op.create_index("ix_crypto_transactions_user_id", "crypto_transactions", ["user_id"])
    op.create_index(
        "ix_crypto_transactions_wallet_address", "crypto_transactions", ["wallet_address"]
    )
    op.create_index("ix_crypto_transactions_tx_hash", "crypto_transactions", ["tx_hash"])
    op.create_index("ix_crypto_transactions_status", "crypto_transactions", ["status"])

    # Create webhook_tokens table
    op.create_table(
        "webhook_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False, default="tron_dealer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_tokens_token_hash", "webhook_tokens", ["token_hash"])
    op.create_index("ix_webhook_tokens_expires_at", "webhook_tokens", ["expires_at"])

    # Create foreign key for users.current_billing_id (after consumption_billings table exists)
    op.create_foreign_key(
        "fk_users_current_billing_id",
        "users",
        "consumption_billings",
        ["current_billing_id"],
        ["id"],
    )


def downgrade() -> None:
    """Drop all tables (NOT RECOMMENDED - use only for testing)."""
    # Drop all tables in reverse order of creation
    op.drop_table("webhook_tokens")
    op.drop_table("crypto_transactions")
    op.drop_table("crypto_orders")
    op.drop_table("subscription_plans")
    op.drop_table("consumption_invoices")
    op.drop_table("consumption_billings")
    op.drop_table("ticket_messages")
    op.drop_table("tickets")
    op.drop_table("transactions")
    op.drop_table("data_packages")
    op.drop_table("vpn_keys")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS key_type_enum")
    op.execute("DROP TYPE IF EXISTS package_type_enum")
    op.execute("DROP TYPE IF EXISTS ticket_status_enum")
    op.execute("DROP TYPE IF EXISTS consumption_billing_status_enum")
    op.execute("DROP TYPE IF EXISTS consumption_invoice_status_enum")
    op.execute("DROP TYPE IF EXISTS crypto_order_status")
    op.execute("DROP TYPE IF EXISTS crypto_tx_status")
