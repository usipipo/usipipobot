"""Repository interface for subscription operations."""

import uuid
from typing import List, Optional, Protocol

from domain.entities.subscription_plan import SubscriptionPlan


class ISubscriptionRepository(Protocol):
    """Repository interface for subscription operations."""

    async def save(self, plan: SubscriptionPlan, current_user_id: int) -> SubscriptionPlan:
        """Save or update a subscription plan."""
        ...

    async def get_by_id(
        self, plan_id: uuid.UUID, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get subscription by ID."""
        ...

    async def get_by_payment_id(
        self, payment_id: str, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get subscription by payment ID (for idempotency)."""
        ...

    async def get_active_by_user(
        self, user_id: int, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get active subscription for a user."""
        ...

    async def get_expiring_plans(self, days: int, current_user_id: int) -> List[SubscriptionPlan]:
        """Get plans expiring within N days."""
        ...

    async def get_expired_plans(self, current_user_id: int) -> List[SubscriptionPlan]:
        """Get all expired plans."""
        ...

    async def deactivate(self, plan_id: uuid.UUID, current_user_id: int) -> bool:
        """Deactivate a subscription plan."""
        ...
