"""Initial consolidated schema

Revision ID: 000_initial_consolidated
Revises:
Create Date: 2026-02-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "000_initial_consolidated"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete database schema."""
    # Create enum types
    op.execute("CREATE TYPE key_type_enum AS ENUM ('wireguard', 'outline')")
    op.execute(
        "CREATE TYPE package_type_enum AS ENUM "
        "('basic', 'estandar', 'avanzado', 'premium', 'unlimited')"
    )
    op.execute("CREATE TYPE crypto_tx_status AS ENUM ('pending', 'confirmed', 'failed')")
    op.execute(
        "CREATE TYPE crypto_order_status AS ENUM " "('pending', 'completed', 'failed', 'expired')"
    )

    # users table
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("language_code", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.Column("status", sa.String(), server_default="active", nullable=True),
        sa.Column("role", sa.String(), server_default="user", nullable=True),
        sa.Column("max_keys", sa.Integer(), server_default="2", nullable=False),
        sa.Column("referral_code", sa.String(), nullable=True),
        sa.Column("referred_by", sa.BigInteger(), nullable=True),
        sa.Column("referral_credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("wallet_address", sa.String(), nullable=True),
        sa.Column(
            "free_data_limit_bytes",
            sa.BigInteger(),
            server_default="10737418240",
            nullable=False,
        ),
        sa.Column("free_data_used_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("telegram_id"),
    )

    # vpn_keys table
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
            "key_type",
            postgresql.ENUM("wireguard", "outline", name="key_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_data", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("used_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "data_limit_bytes",
            sa.BigInteger(),
            server_default="10737418240",
            nullable=False,
        ),
        sa.Column(
            "billing_reset_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # data_packages table
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
            postgresql.ENUM(
                "basic",
                "estandar",
                "avanzado",
                "premium",
                "unlimited",
                name="package_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("data_limit_bytes", sa.BigInteger(), nullable=False),
        sa.Column("data_used_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("stars_paid", sa.Integer(), nullable=False),
        sa.Column(
            "purchased_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("telegram_payment_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # transactions table
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # tickets table
    op.create_table(
        "tickets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="open", nullable=False),
        sa.Column("priority", sa.String(), server_default="medium", nullable=False),
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
        sa.Column("response", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # crypto_transactions table
    op.create_table(
        "crypto_transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("token_symbol", sa.String(length=10), server_default="USDT", nullable=False),
        sa.Column("tx_hash", sa.String(length=66), unique=True, nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "confirmed",
                "failed",
                name="crypto_tx_status",
                create_type=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("raw_payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # webhook_tokens table
    op.create_table(
        "webhook_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "purpose",
            sa.String(length=50),
            server_default="tron_dealer",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )

    # crypto_orders table
    op.create_table(
        "crypto_orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "package_type",
            sa.String(length=50),
            server_default="basic",
            nullable=False,
        ),
        sa.Column("amount_usdt", sa.Float(), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("tron_dealer_order_id", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "completed",
                "failed",
                "expired",
                name="crypto_order_status",
                create_type=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_vpn_keys_user_id", "vpn_keys", ["user_id"])
    op.create_index("ix_data_packages_user_id", "data_packages", ["user_id"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_crypto_transactions_user_id", "crypto_transactions", ["user_id"])
    op.create_index("ix_crypto_transactions_tx_hash", "crypto_transactions", ["tx_hash"])
    op.create_index("ix_crypto_orders_user_id", "crypto_orders", ["user_id"])
    op.create_index("ix_crypto_orders_wallet_address", "crypto_orders", ["wallet_address"])
    op.create_index("ix_crypto_orders_status", "crypto_orders", ["status"])
    op.create_index("ix_crypto_orders_expires_at", "crypto_orders", ["expires_at"])
    op.create_index("ix_crypto_orders_tx_hash", "crypto_orders", ["tx_hash"])
    op.create_index("ix_webhook_tokens_token_hash", "webhook_tokens", ["token_hash"])
    op.create_index("ix_webhook_tokens_expires_at", "webhook_tokens", ["expires_at"])


def downgrade() -> None:
    """Drop all tables and types."""
    # Drop indexes
    op.drop_index("ix_webhook_tokens_expires_at", table_name="webhook_tokens")
    op.drop_index("ix_webhook_tokens_token_hash", table_name="webhook_tokens")
    op.drop_index("ix_crypto_orders_tx_hash", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_expires_at", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_status", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_wallet_address", table_name="crypto_orders")
    op.drop_index("ix_crypto_orders_user_id", table_name="crypto_orders")
    op.drop_index("ix_crypto_transactions_tx_hash", table_name="crypto_transactions")
    op.drop_index("ix_crypto_transactions_user_id", table_name="crypto_transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_data_packages_user_id", table_name="data_packages")
    op.drop_index("ix_vpn_keys_user_id", table_name="vpn_keys")

    # Drop tables
    op.drop_table("crypto_orders")
    op.drop_table("webhook_tokens")
    op.drop_table("crypto_transactions")
    op.drop_table("tickets")
    op.drop_table("transactions")
    op.drop_table("data_packages")
    op.drop_table("vpn_keys")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS crypto_order_status")
    op.execute("DROP TYPE IF EXISTS crypto_tx_status")
    op.execute("DROP TYPE IF EXISTS package_type_enum")
    op.execute("DROP TYPE IF EXISTS key_type_enum")
