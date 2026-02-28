import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class InvoiceStatus(str, Enum):
    """Estados posibles de una factura de consumo."""

    PENDING = "pending"      # Factura generada, esperando pago
    PAID = "paid"            # Factura pagada exitosamente
    EXPIRED = "expired"      # Factura vencida (30 minutos)
    CANCELLED = "cancelled"  # Factura cancelada manualmente


@dataclass
class ConsumptionInvoice:
    """
    Entidad que representa una factura de pago por consumo.

    Cada factura tiene un tiempo límite de 30 minutos para ser pagada.
    Se asocia con un ciclo de facturación (ConsumptionBilling).
    """

    billing_id: uuid.UUID
    user_id: int
    amount_usd: Decimal
    wallet_address: str  # Dirección de wallet para recibir el pago
    status: InvoiceStatus = InvoiceStatus.PENDING
    id: Optional[uuid.UUID] = None
    expires_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    transaction_hash: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Tiempo de expiración: 30 minutos
    EXPIRATION_MINUTES: int = field(default=30, repr=False)

    def __post_init__(self):
        if self.id is None:
            self.id = uuid.uuid4()
        if self.expires_at is None:
            self.expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.EXPIRATION_MINUTES
            )

    @property
    def is_pending(self) -> bool:
        """Verifica si la factura está pendiente de pago."""
        return self.status == InvoiceStatus.PENDING

    @property
    def is_paid(self) -> bool:
        """Verifica si la factura está pagada."""
        return self.status == InvoiceStatus.PAID

    @property
    def is_expired(self) -> bool:
        """Verifica si la factura ha expirado."""
        if self.status == InvoiceStatus.EXPIRED:
            return True
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_usdt_payment(self) -> bool:
        """Verifica si es un pago en USDT (basado en la dirección)."""
        # Las direcciones BSC comienzan con 0x
        return self.wallet_address.startswith("0x")

    @property
    def time_remaining_seconds(self) -> int:
        """Retorna los segundos restantes para pagar la factura."""
        if self.status != InvoiceStatus.PENDING or self.expires_at is None:
            return 0
        remaining = (self.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))

    @property
    def time_remaining_formatted(self) -> str:
        """Retorna el tiempo restante formateado (MM:SS)."""
        seconds = self.time_remaining_seconds
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def mark_as_paid(self, transaction_hash: str) -> None:
        """
        Marca la factura como pagada.

        Args:
            transaction_hash: Hash de la transacción blockchain
        """
        if self.status != InvoiceStatus.PENDING:
            raise ValueError("Solo se pueden pagar facturas pendientes")

        if self.is_expired:
            raise ValueError("La factura ha expirado")

        self.status = InvoiceStatus.PAID
        self.paid_at = datetime.now(timezone.utc)
        self.transaction_hash = transaction_hash

    def mark_as_expired(self) -> None:
        """Marca la factura como expirada."""
        if self.status == InvoiceStatus.PAID:
            raise ValueError("No se puede expirar una factura ya pagada")

        self.status = InvoiceStatus.EXPIRED

    def get_payment_instructions(self) -> str:
        """
        Genera instrucciones de pago para mostrar al usuario.
        Sanitiza la dirección de wallet para no exponer datos sensibles completos.
        """
        masked_wallet = self._mask_wallet_address()
        return (
            f"💰 *Instrucciones de Pago*\n\n"
            f"Monto: *${self.amount_usd:.2f} USDT*\n"
            f"Red: *BSC (BEP20)*\n"
            f"Wallet: `{masked_wallet}`\n\n"
            f"⏱️ Tiempo restante: *{self.time_remaining_formatted}*\n\n"
            f"⚠️ Envíe exactamente el monto indicado."
        )

    def _mask_wallet_address(self) -> str:
        """
        Mascara la dirección de wallet para mostrar solo parte.
        Ejemplo: 0x1234...5678
        """
        if len(self.wallet_address) <= 12:
            return self.wallet_address
        return f"{self.wallet_address[:6]}...{self.wallet_address[-4:]}"

    def get_formatted_amount(self) -> str:
        """Retorna el monto formateado para mostrar."""
        return f"${self.amount_usd:.2f} USD"

    def __repr__(self) -> str:
        return (
            f"<ConsumptionInvoice(id={self.id}, billing_id={self.billing_id}, "
            f"amount=${self.amount_usd}, status={self.status.value})>"
        )
