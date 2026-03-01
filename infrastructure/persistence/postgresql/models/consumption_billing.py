import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.entities.consumption_billing import ConsumptionBilling, BillingStatus
from infrastructure.persistence.postgresql.models.base import Base


class ConsumptionBillingModel(Base):
    """Modelo SQLAlchemy para ciclos de facturación por consumo."""

    __tablename__ = "consumption_billings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Usamos Numeric para precisión decimal exacta
    mb_consumed: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False, default=Decimal("0.00")
    )
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False, default=Decimal("0.00")
    )
    price_per_mb_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 12), nullable=False, default=Decimal("0.000439453125")
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(
            "active", "closed", "paid", "cancelled",
            name="billing_status_enum"
        ),
        nullable=False,
        default="active",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def from_entity(cls, entity: ConsumptionBilling) -> "ConsumptionBillingModel":
        """Convierte una entidad de dominio a modelo SQLAlchemy."""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            mb_consumed=entity.mb_consumed,
            total_cost_usd=entity.total_cost_usd,
            price_per_mb_usd=entity.price_per_mb_usd,
            status=entity.status.value,
            created_at=entity.created_at,
        )

    def to_entity(self) -> ConsumptionBilling:
        """Convierte el modelo SQLAlchemy a entidad de dominio."""
        entity = ConsumptionBilling(
            id=self.id,
            user_id=self.user_id,
            started_at=self.started_at,
            status=BillingStatus(self.status),
            ended_at=self.ended_at,
            mb_consumed=self.mb_consumed,
            total_cost_usd=self.total_cost_usd,
            price_per_mb_usd=self.price_per_mb_usd,
            created_at=self.created_at,
        )
        return entity
