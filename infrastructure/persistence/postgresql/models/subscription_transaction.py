"""SQLAlchemy model for subscription transaction."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.entities.subscription_transaction import (
    SubscriptionTransaction,
    SubscriptionTransactionStatus,
)
from infrastructure.persistence.postgresql.models.base import Base


class SubscriptionTransactionModel(Base):
    """SQLAlchemy model for subscription transactions."""

    __tablename__ = "subscription_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True
    )
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_stars: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(
            "pending",
            "completed",
            "expired",
            "failed",
            name="subscription_transaction_status",
        ),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    @classmethod
    def from_entity(cls, entity: SubscriptionTransaction) -> "SubscriptionTransactionModel":
        """Create model from entity."""
        return cls(
            id=entity.id,
            transaction_id=entity.transaction_id,
            user_id=entity.user_id,
            plan_type=entity.plan_type,
            amount_stars=entity.amount_stars,
            payload=entity.payload,
            status=(entity.status.value if hasattr(entity.status, "value") else entity.status),
            created_at=entity.created_at,
            expires_at=entity.expires_at,
            completed_at=entity.completed_at,
        )

    def to_entity(self) -> SubscriptionTransaction:
        """Convert model to entity."""
        return SubscriptionTransaction(
            id=self.id,
            transaction_id=self.transaction_id,
            user_id=self.user_id,
            plan_type=self.plan_type,
            amount_stars=self.amount_stars,
            payload=self.payload,
            status=SubscriptionTransactionStatus(self.status),
            created_at=self.created_at,
            expires_at=self.expires_at,
            completed_at=self.completed_at,
        )
