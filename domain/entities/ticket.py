from enum import Enum


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
