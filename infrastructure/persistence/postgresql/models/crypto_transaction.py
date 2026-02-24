from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import Column, DateTime, String, Float, Integer, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from infrastructure.persistence.postgresql.models.base import Base


class CryptoTransactionModel(Base):
    __tablename__ = "crypto_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False)
    amount = Column(Float, nullable=False)
    token_symbol = Column(String(10), nullable=False, default="USDT")
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum("pending", "confirmed", "failed", name="crypto_tx_status"),
        nullable=False,
        default="pending"
    )
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    raw_payload = Column(JSON, default=dict)

    @classmethod
    def from_entity(cls, entity) -> "CryptoTransactionModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            wallet_address=entity.wallet_address,
            amount=entity.amount,
            token_symbol=entity.token_symbol,
            tx_hash=entity.tx_hash,
            status=entity.status.value if hasattr(entity.status, 'value') else entity.status,
            confirmed_at=entity.confirmed_at,
            created_at=entity.created_at,
            raw_payload=entity.raw_payload
        )

    def to_entity(self):
        from domain.entities.crypto_transaction import CryptoTransaction, CryptoTransactionStatus
        return CryptoTransaction(
            id=self.id,
            user_id=self.user_id,
            wallet_address=self.wallet_address,
            amount=self.amount,
            token_symbol=self.token_symbol,
            tx_hash=self.tx_hash,
            status=CryptoTransactionStatus(self.status),
            confirmed_at=self.confirmed_at,
            created_at=self.created_at,
            raw_payload=self.raw_payload or {}
        )


class WebhookTokenModel(Base):
    __tablename__ = "webhook_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    purpose = Column(String(50), nullable=False, default="tron_dealer")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSON, default=dict)

    @classmethod
    def from_entity(cls, entity) -> "WebhookTokenModel":
        return cls(
            id=entity.id,
            token_hash=entity.token_hash,
            purpose=entity.purpose,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
            used_at=entity.used_at,
            metadata=entity.metadata
        )

    def to_entity(self):
        from domain.entities.crypto_transaction import WebhookToken
        return WebhookToken(
            id=self.id,
            token_hash=self.token_hash,
            purpose=self.purpose,
            created_at=self.created_at,
            expires_at=self.expires_at,
            used_at=self.used_at,
            metadata=self.metadata or {}
        )
