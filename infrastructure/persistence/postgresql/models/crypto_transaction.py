from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import Column, DateTime, String, Float, Integer, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.entities.crypto_transaction import CryptoTransaction, CryptoTransactionStatus, WebhookToken
from infrastructure.persistence.postgresql.models.base import Base


class CryptoTransactionModel(Base):
    __tablename__ = "crypto_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.telegram_id"), nullable=False, index=True)
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    token_symbol: Mapped[str] = mapped_column(String(10), nullable=False, default="USDT")
    tx_hash: Mapped[str] = mapped_column(String(66), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("pending", "confirmed", "failed", name="crypto_tx_status"),
        nullable=False,
        default="pending"
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    @classmethod
    def from_entity(cls, entity: CryptoTransaction) -> "CryptoTransactionModel":
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

    def to_entity(self) -> CryptoTransaction:
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

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False, default="tron_dealer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    @classmethod
    def from_entity(cls, entity: WebhookToken) -> "WebhookTokenModel":
        return cls(
            id=entity.id,
            token_hash=entity.token_hash,
            purpose=entity.purpose,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
            used_at=entity.used_at,
            extra_data=entity.extra_data
        )

    def to_entity(self) -> WebhookToken:
        return WebhookToken(
            id=self.id,
            token_hash=self.token_hash,
            purpose=self.purpose,
            created_at=self.created_at,
            expires_at=self.expires_at,
            used_at=self.used_at,
            extra_data=self.extra_data or {}
        )
