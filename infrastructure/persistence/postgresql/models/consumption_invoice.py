import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.entities.consumption_invoice import ConsumptionInvoice, InvoiceStatus
from infrastructure.persistence.postgresql.models.base import Base


class ConsumptionInvoiceModel(Base):
    """Modelo SQLAlchemy para facturas de consumo."""

    __tablename__ = "consumption_invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consumption_billings.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False
    )
    wallet_address: Mapped[str] = mapped_column(
        String(42), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(
            "pending", "paid", "expired", "cancelled",
            name="invoice_status_enum"
        ),
        nullable=False,
        default="pending",
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    transaction_hash: Mapped[Optional[str]] = mapped_column(
        String(66), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def from_entity(cls, entity: ConsumptionInvoice) -> "ConsumptionInvoiceModel":
        """Convierte una entidad de dominio a modelo SQLAlchemy."""
        return cls(
            id=entity.id,
            billing_id=entity.billing_id,
            user_id=entity.user_id,
            amount_usd=entity.amount_usd,
            wallet_address=entity.wallet_address,
            status=entity.status.value,
            expires_at=entity.expires_at,
            paid_at=entity.paid_at,
            transaction_hash=entity.transaction_hash,
            created_at=entity.created_at,
        )

    def to_entity(self) -> ConsumptionInvoice:
        """Convierte el modelo SQLAlchemy a entidad de dominio."""
        entity = ConsumptionInvoice(
            id=self.id,
            billing_id=self.billing_id,
            user_id=self.user_id,
            amount_usd=self.amount_usd,
            wallet_address=self.wallet_address,
            status=InvoiceStatus(self.status),
            expires_at=self.expires_at,
            paid_at=self.paid_at,
            transaction_hash=self.transaction_hash,
            created_at=self.created_at,
        )
        return entity
