import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional


class CryptoOrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


ORDER_EXPIRATION_MINUTES = 30


@dataclass
class CryptoOrder:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: int = 0
    package_type: str = "basic"
    amount_usdt: float = 0.0
    wallet_address: str = ""
    tron_dealer_order_id: Optional[str] = None
    status: CryptoOrderStatus = CryptoOrderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(minutes=ORDER_EXPIRATION_MINUTES)
    )
    tx_hash: Optional[str] = None
    confirmed_at: Optional[datetime] = None

    @property
    def is_pending(self) -> bool:
        return self.status == CryptoOrderStatus.PENDING

    @property
    def is_completed(self) -> bool:
        return self.status == CryptoOrderStatus.COMPLETED

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def mark_completed(self, tx_hash: str) -> None:
        self.status = CryptoOrderStatus.COMPLETED
        self.tx_hash = tx_hash
        self.confirmed_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        self.status = CryptoOrderStatus.FAILED

    def mark_expired(self) -> None:
        self.status = CryptoOrderStatus.EXPIRED
