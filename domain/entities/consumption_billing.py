import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class BillingStatus(str, Enum):
    """Estados posibles de un ciclo de facturación por consumo."""

    ACTIVE = "active"      # Ciclo en curso, consumiendo
    CLOSED = "closed"      # Ciclo cerrado, esperando pago
    PAID = "paid"          # Ciclo pagado, completado
    CANCELLED = "cancelled"  # Ciclo cancelado (no implementado inicialmente)


@dataclass
class ConsumptionBilling:
    """
    Entidad que representa un ciclo de facturación por consumo.

    Cada usuario puede tener un ciclo activo a la vez.
    El ciclo dura 30 días o hasta que se cierre manualmente.
    """

    user_id: int
    started_at: datetime
    status: BillingStatus = BillingStatus.ACTIVE
    id: Optional[uuid.UUID] = None
    ended_at: Optional[datetime] = None
    mb_consumed: Decimal = Decimal("0.00")
    total_cost_usd: Decimal = Decimal("0.00")
    price_per_mb_usd: Decimal = Decimal("0.000439453125")  # Default: $0.45/GB
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.id is None:
            self.id = uuid.uuid4()

    @property
    def is_active(self) -> bool:
        """Verifica si el ciclo está activo (consumiendo)."""
        return self.status == BillingStatus.ACTIVE

    @property
    def is_closed(self) -> bool:
        """Verifica si el ciclo está cerrado (esperando pago)."""
        return self.status == BillingStatus.CLOSED

    @property
    def is_paid(self) -> bool:
        """Verifica si el ciclo está pagado."""
        return self.status == BillingStatus.PAID

    @property
    def gb_consumed(self) -> Decimal:
        """Retorna el consumo en GB con 2 decimales."""
        return (self.mb_consumed / Decimal("1024")).quantize(Decimal("0.01"))

    def add_consumption(self, mb_used: Decimal) -> None:
        """
        Agrega consumo al ciclo y recalcula el costo total.

        Args:
            mb_used: Cantidad de MB consumidos (puede incluir decimales)
        """
        if self.status != BillingStatus.ACTIVE:
            raise ValueError("No se puede agregar consumo a un ciclo no activo")

        self.mb_consumed += Decimal(str(mb_used))
        self._recalculate_cost()

    def _recalculate_cost(self) -> None:
        """Recalcula el costo total basado en MB consumidos."""
        # Costo = MB * precio por MB
        self.total_cost_usd = (self.mb_consumed * self.price_per_mb_usd).quantize(
            Decimal("0.000001")  # Precisión de 6 decimales
        )

    def close_cycle(self) -> None:
        """
        Cierra el ciclo de facturación.
        Cambia el estado a CLOSED y registra el tiempo de cierre.
        """
        if self.status != BillingStatus.ACTIVE:
            raise ValueError("Solo se pueden cerrar ciclos activos")

        self.status = BillingStatus.CLOSED
        self.ended_at = datetime.now(timezone.utc)
        self._recalculate_cost()

    def mark_as_paid(self) -> None:
        """
        Marca el ciclo como pagado.
        Solo aplicable a ciclos cerrados.
        """
        if self.status != BillingStatus.CLOSED:
            raise ValueError("Solo se pueden pagar ciclos cerrados")

        self.status = BillingStatus.PAID

    def get_formatted_cost(self) -> str:
        """Retorna el costo formateado para mostrar al usuario."""
        return f"${self.total_cost_usd:.2f} USD"

    def get_formatted_consumption(self) -> str:
        """Retorna el consumo formateado para mostrar al usuario."""
        if self.mb_consumed < 1024:
            return f"{self.mb_consumed:.2f} MB"
        return f"{self.gb_consumed:.2f} GB"

    def __repr__(self) -> str:
        return (
            f"<ConsumptionBilling(id={self.id}, user_id={self.user_id}, "
            f"status={self.status.value}, mb_consumed={self.mb_consumed})>"
        )
