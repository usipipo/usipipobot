from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Ticket:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: int = 0
    subject: str = ""
    message: str = ""
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    response: Optional[str] = None

    @property
    def is_open(self) -> bool:
        return self.status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS)

    @property
    def status_emoji(self) -> str:
        emojis = {
            TicketStatus.OPEN: "🟡",
            TicketStatus.IN_PROGRESS: "🔵",
            TicketStatus.RESOLVED: "🟢",
            TicketStatus.CLOSED: "⚫",
        }
        return emojis.get(self.status, "⚪")

    def add_response(self, response: str, admin_id: int) -> None:
        self.response = response
        self.resolved_by = admin_id
        self.resolved_at = datetime.now(timezone.utc)
        self.status = TicketStatus.RESOLVED
        self.updated_at = datetime.now(timezone.utc)

    def close(self) -> None:
        self.status = TicketStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)

    def set_in_progress(self) -> None:
        self.status = TicketStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
