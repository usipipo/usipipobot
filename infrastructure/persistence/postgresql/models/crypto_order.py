import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from infrastructure.persistence.postgresql.models.base import Base


class CryptoOrderModel(Base):
    __tablename__ = "crypto_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.telegram_id"), nullable=False, index=True
    )
    package_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="basic"
    )
    amount_usdt: Mapped[float] = mapped_column(Float, nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    tron_dealer_order_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(
            "pending", "completed", "failed", "expired", name="crypto_order_status"
        ),
        nullable=False,
        default="pending",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    tx_hash: Mapped[Optional[str]] = mapped_column(
        String(66), nullable=True, index=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @classmethod
    def from_entity(cls, entity: CryptoOrder) -> "CryptoOrderModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            package_type=entity.package_type,
            amount_usdt=entity.amount_usdt,
            wallet_address=entity.wallet_address,
            tron_dealer_order_id=entity.tron_dealer_order_id,
            status=(
                entity.status.value
                if hasattr(entity.status, "value")
                else entity.status
            ),
            created_at=entity.created_at,
            expires_at=entity.expires_at,
            tx_hash=entity.tx_hash,
            confirmed_at=entity.confirmed_at,
        )

    def to_entity(self) -> CryptoOrder:
        return CryptoOrder(
            id=self.id,
            user_id=self.user_id,
            package_type=self.package_type,
            amount_usdt=self.amount_usdt,
            wallet_address=self.wallet_address,
            tron_dealer_order_id=self.tron_dealer_order_id,
            status=CryptoOrderStatus(self.status),
            created_at=self.created_at,
            expires_at=self.expires_at,
            tx_hash=self.tx_hash,
            confirmed_at=self.confirmed_at,
        )
