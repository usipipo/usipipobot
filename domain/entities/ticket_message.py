import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    """Retorna datetime actual en UTC."""
    return datetime.now(timezone.utc)


@dataclass
class TicketMessage:
    """Entidad que representa un mensaje en un ticket."""

    ticket_id: uuid.UUID
    from_user_id: int
    message: str
    is_from_admin: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_utc_now)
