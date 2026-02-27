import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CryptoTransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass
class CryptoTransaction:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: int = 0
    wallet_address: str = ""
    amount: float = 0.0
    token_symbol: str = "USDT"
    tx_hash: str = ""
    status: CryptoTransactionStatus = CryptoTransactionStatus.PENDING
    confirmed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_payload: dict = field(default_factory=dict)

    @property
    def is_confirmed(self) -> bool:
        return self.status == CryptoTransactionStatus.CONFIRMED

    def confirm(self) -> None:
        self.status = CryptoTransactionStatus.CONFIRMED
        self.confirmed_at = datetime.now(timezone.utc)

    def fail(self) -> None:
        self.status = CryptoTransactionStatus.FAILED


@dataclass
class WebhookToken:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    token_hash: str = ""
    purpose: str = "tron_dealer"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    used_at: Optional[datetime] = None
    extra_data: dict = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def mark_used(self) -> None:
        self.used_at = datetime.now(timezone.utc)
