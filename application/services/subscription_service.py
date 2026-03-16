"""Subscription service for managing user subscriptions."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from domain.entities.subscription_plan import PlanType, SubscriptionPlan
from domain.interfaces.isubscription_repository import ISubscriptionRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


@dataclass
class SubscriptionOption:
    """Subscription plan option."""

    name: str
    plan_type: PlanType
    duration_months: int
    stars: int
    usdt: float
    data_limit: str = "Unlimited"
    bonus_percent: int = 0


SUBSCRIPTION_OPTIONS: List[SubscriptionOption] = [
    SubscriptionOption(
        name="1 Month",
        plan_type=PlanType.ONE_MONTH,
        duration_months=1,
        stars=360,
        usdt=2.99,
    ),
    SubscriptionOption(
        name="3 Months",
        plan_type=PlanType.THREE_MONTHS,
        duration_months=3,
        stars=960,
        usdt=7.99,
        bonus_percent=11,  # ~10% discount
    ),
    SubscriptionOption(
        name="6 Months",
        plan_type=PlanType.SIX_MONTHS,
        duration_months=6,
        stars=1560,
        usdt=12.99,
        bonus_percent=13,  # ~15% discount
    ),
]


class SubscriptionService:
    """Service for managing subscription plans."""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        user_repo: IUserRepository,
    ):
        self.subscription_repo = subscription_repo
        self.user_repo = user_repo

    def get_available_plans(self) -> List[SubscriptionOption]:
        """Get all available subscription plans."""
        return SUBSCRIPTION_OPTIONS.copy()

    def get_plan_option(self, plan_type: str) -> Optional[SubscriptionOption]:
        """Get a specific plan option by type."""
        try:
            p_type = PlanType(plan_type.lower())
            for option in SUBSCRIPTION_OPTIONS:
                if option.plan_type == p_type:
                    return option
            return None
        except ValueError:
            return None

    async def is_premium_user(self, user_id: int, current_user_id: int) -> bool:
        """Check if user has an active subscription."""
        active_plan = await self.subscription_repo.get_active_by_user(user_id, current_user_id)
        return active_plan is not None and not active_plan.is_expired

    async def get_user_subscription(
        self, user_id: int, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get user's active subscription plan."""
        return await self.subscription_repo.get_active_by_user(user_id, current_user_id)

    async def activate_subscription(
        self,
        user_id: int,
        plan_type: str,
        stars_paid: int,
        payment_id: str,
        current_user_id: int,
    ) -> SubscriptionPlan:
        """Activate a new subscription for a user."""
        # Check for existing active subscription
        existing = await self.subscription_repo.get_active_by_user(user_id, current_user_id)
        if existing and not existing.is_expired:
            raise ValueError(f"User {user_id} already has an active subscription")

        # Check for idempotency (same payment_id)
        existing_by_payment = await self.subscription_repo.get_by_payment_id(
            payment_id, current_user_id
        )
        if existing_by_payment:
            logger.info(f"📦 Subscription already exists for payment {payment_id}")
            return existing_by_payment

        # Get plan option
        plan_option = self.get_plan_option(plan_type)
        if not plan_option:
            raise ValueError(f"Invalid plan type: {plan_type}")

        # Create new subscription
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=plan_option.duration_months * 30)

        plan = SubscriptionPlan(
            user_id=user_id,
            plan_type=PlanType(plan_type.lower()),
            stars_paid=stars_paid,
            payment_id=payment_id,
            starts_at=now,
            expires_at=expires,
            is_active=True,
        )

        saved_plan = await self.subscription_repo.save(plan, current_user_id)
        logger.info(
            f"📦 Subscription activated for user {user_id}: "
            f"{plan_option.name} ({stars_paid} stars)"
        )
        return saved_plan

    async def cancel_subscription(self, user_id: int, current_user_id: int) -> bool:
        """Cancel user's active subscription."""
        active_plan = await self.subscription_repo.get_active_by_user(user_id, current_user_id)
        if not active_plan:
            return False

        await self.subscription_repo.deactivate(active_plan.id, current_user_id)
        logger.info(f"📦 Subscription cancelled for user {user_id}")
        return True

    async def get_expiring_subscriptions(
        self, days: int = 3, current_user_id: int = 0
    ) -> List[SubscriptionPlan]:
        """Get subscriptions expiring within N days."""
        return await self.subscription_repo.get_expiring_plans(days, current_user_id)

    async def get_expired_subscriptions(self, current_user_id: int = 0) -> List[SubscriptionPlan]:
        """Get all expired subscriptions."""
        return await self.subscription_repo.get_expired_plans(current_user_id)

    async def get_user_data_limit(self, user_id: int, current_user_id: int) -> int:
        """
        Get user's data limit based on subscription status.
        Returns -1 for unlimited (premium users).
        """
        is_premium = await self.is_premium_user(user_id, current_user_id)
        if is_premium:
            return -1  # Unlimited data for premium users

        # Non-premium users get default limit (10GB)
        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if user:
            return user.free_data_limit_bytes
        return 10737418240  # Default 10GB
