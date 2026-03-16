"""Subscription plan domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PlanType(str, Enum):
    """Subscription plan types."""

    ONE_MONTH = "one_month"
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"


@dataclass
class SubscriptionPlan:
    """Represents an active subscription plan for a user.

    Attributes:
        user_id: Telegram ID of the user
        plan_type: Type of plan (1, 3, or 6 months)
        stars_paid: Total stars paid for this plan
        payment_id: Payment reference for idempotency
        starts_at: Plan activation datetime
        expires_at: Plan expiration datetime
        id: Unique plan identifier
        is_active: Whether plan is currently active
        created_at: Record creation datetime
        updated_at: Record last update datetime
    """

    user_id: int
    plan_type: PlanType
    stars_paid: int
    payment_id: str
    starts_at: datetime
    expires_at: datetime
    id: Optional[uuid.UUID] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid.uuid4()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    @property
    def duration_days(self) -> int:
        """Returns plan duration in days."""
        duration_map = {
            PlanType.ONE_MONTH: 30,
            PlanType.THREE_MONTHS: 90,
            PlanType.SIX_MONTHS: 180,
        }
        return duration_map.get(self.plan_type, 0)

    @property
    def days_remaining(self) -> int:
        """Returns days remaining until expiration."""
        now = datetime.now(timezone.utc)
        delta = self.expires_at - now
        return max(0, delta.days)

    @property
    def is_expiring_soon(self) -> bool:
        """True if plan expires in less than 3 days."""
        return self.days_remaining <= 3

    @property
    def is_expired(self) -> bool:
        """True if plan has expired."""
        now = datetime.now(timezone.utc)
        return now > self.expires_at

    def deactivate(self) -> None:
        """Deactivate this subscription plan."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
