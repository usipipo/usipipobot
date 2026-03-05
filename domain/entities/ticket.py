import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TicketCategory(str, Enum):
    """Categorías de tickets de soporte."""

    VPN_FAIL = "vpn_fail"
    PAYMENT = "payment"
    ACCOUNT = "account"
    OTHER = "other"


class TicketPriority(str, Enum):
    """Prioridades de tickets."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, Enum):
    """Estados posibles de un ticket."""

    OPEN = "open"
    RESPONDED = "responded"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Ticket:
    """
    Entidad que representa un ticket de soporte.
    """

    user_id: int
    category: TicketCategory
    priority: TicketPriority
    subject: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: TicketStatus = field(default=TicketStatus.OPEN)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    admin_notes: Optional[str] = None

    @property
    def ticket_number(self) -> str:
        """Genera número de ticket legible (T-XXXXXXX)."""
        return f"T-{str(self.id)[:8].upper()}"

    @property
    def is_open(self) -> bool:
        """Verifica si el ticket está abierto."""
        return self.status in [TicketStatus.OPEN, TicketStatus.RESPONDED]

    @property
    def is_resolved(self) -> bool:
        """Verifica si el ticket está resuelto."""
        return self.status == TicketStatus.RESOLVED

    @property
    def is_closed(self) -> bool:
        """Verifica si el ticket está cerrado."""
        return self.status == TicketStatus.CLOSED

    def update_status(
        self, new_status: TicketStatus, admin_id: Optional[int] = None
    ) -> None:
        """Actualiza el estado del ticket."""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        if new_status == TicketStatus.RESOLVED:
            self.resolved_at = datetime.now(timezone.utc)
            self.resolved_by = admin_id
