"""PostgreSQL repository for subscription plans."""

import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.subscription_plan import PlanType, SubscriptionPlan
from domain.interfaces.isubscription_repository import ISubscriptionRepository
from utils.logger import logger

from .base_repository import BasePostgresRepository
from .models.subscription_plan import SubscriptionPlanModel


def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize datetime to UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PostgresSubscriptionRepository(BasePostgresRepository, ISubscriptionRepository):
    """PostgreSQL implementation of ISubscriptionRepository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _model_to_entity(self, model: SubscriptionPlanModel) -> SubscriptionPlan:
        """Convert SQLAlchemy model to domain entity."""
        return SubscriptionPlan(
            id=model.id,
            user_id=model.user_id,
            plan_type=PlanType(model.plan_type),
            stars_paid=model.stars_paid,
            payment_id=model.payment_id,
            starts_at=_normalize_datetime(model.starts_at) or datetime.now(timezone.utc),
            expires_at=_normalize_datetime(model.expires_at),
            is_active=model.is_active,
            created_at=_normalize_datetime(model.created_at),
            updated_at=_normalize_datetime(model.updated_at),
        )

    def _entity_to_model(self, entity: SubscriptionPlan) -> SubscriptionPlanModel:
        """Convert domain entity to SQLAlchemy model."""
        return SubscriptionPlanModel(
            id=entity.id if entity.id else uuid.uuid4(),
            user_id=entity.user_id,
            plan_type=(
                entity.plan_type.value
                if isinstance(entity.plan_type, PlanType)
                else entity.plan_type
            ),
            stars_paid=entity.stars_paid,
            payment_id=entity.payment_id,
            starts_at=entity.starts_at,
            expires_at=entity.expires_at,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def save(self, plan: SubscriptionPlan, current_user_id: int) -> SubscriptionPlan:
        """Save or update a subscription plan."""
        await self._set_current_user(current_user_id)
        try:
            if plan.id:
                existing = await self.session.get(SubscriptionPlanModel, plan.id)
                if existing:
                    existing.plan_type = (
                        plan.plan_type.value
                        if isinstance(plan.plan_type, PlanType)
                        else plan.plan_type
                    )
                    existing.stars_paid = plan.stars_paid
                    existing.payment_id = plan.payment_id
                    existing.starts_at = plan.starts_at
                    existing.expires_at = plan.expires_at
                    existing.is_active = plan.is_active
                    await self.session.commit()
                    await self.session.refresh(existing)
                    logger.info(f"📦 Subscription plan updated: {plan.id}")
                    return replace(plan)

            model = self._entity_to_model(plan)
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            logger.info(f"📦 Subscription plan created: {model.id}")
            return replace(plan, id=model.id)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error saving subscription plan: {e}")
            raise

    async def get_by_id(
        self, plan_id: uuid.UUID, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get subscription by ID."""
        await self._set_current_user(current_user_id)
        try:
            result = await self.session.execute(
                select(SubscriptionPlanModel).where(SubscriptionPlanModel.id == plan_id)
            )
            model = result.scalars().first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"❌ Error getting subscription by ID: {e}")
            raise

    async def get_by_payment_id(
        self, payment_id: str, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get subscription by payment ID (for idempotency)."""
        await self._set_current_user(current_user_id)
        try:
            result = await self.session.execute(
                select(SubscriptionPlanModel).where(SubscriptionPlanModel.payment_id == payment_id)
            )
            model = result.scalars().first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"❌ Error getting subscription by payment_id: {e}")
            raise

    async def get_active_by_user(
        self, user_id: int, current_user_id: int
    ) -> Optional[SubscriptionPlan]:
        """Get active subscription for a user."""
        await self._set_current_user(current_user_id)
        try:
            result = await self.session.execute(
                select(SubscriptionPlanModel)
                .where(
                    SubscriptionPlanModel.user_id == user_id,
                    SubscriptionPlanModel.is_active == True,
                    SubscriptionPlanModel.expires_at > datetime.now(timezone.utc),
                )
                .order_by(SubscriptionPlanModel.expires_at.desc())
            )
            model = result.scalars().first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"❌ Error getting active subscription for user {user_id}: {e}")
            raise

    async def get_expiring_plans(self, days: int, current_user_id: int) -> List[SubscriptionPlan]:
        """Get plans expiring within N days."""
        await self._set_current_user(current_user_id)
        try:
            now = datetime.now(timezone.utc)
            future_date = now + timedelta(days=days)
            result = await self.session.execute(
                select(SubscriptionPlanModel)
                .where(
                    SubscriptionPlanModel.is_active == True,
                    SubscriptionPlanModel.expires_at > now,
                    SubscriptionPlanModel.expires_at <= future_date,
                )
                .order_by(SubscriptionPlanModel.expires_at.asc())
            )
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"❌ Error getting expiring plans: {e}")
            raise

    async def get_expired_plans(self, current_user_id: int) -> List[SubscriptionPlan]:
        """Get all expired plans."""
        await self._set_current_user(current_user_id)
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(SubscriptionPlanModel)
                .where(
                    SubscriptionPlanModel.is_active == True, SubscriptionPlanModel.expires_at < now
                )
                .order_by(SubscriptionPlanModel.expires_at.asc())
            )
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"❌ Error getting expired plans: {e}")
            raise

    async def deactivate(self, plan_id: uuid.UUID, current_user_id: int) -> bool:
        """Deactivate a subscription plan."""
        await self._set_current_user(current_user_id)
        try:
            model = await self.session.get(SubscriptionPlanModel, plan_id)
            if model:
                model.is_active = False
                await self.session.commit()
                logger.info(f"📦 Subscription plan deactivated: {plan_id}")
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error deactivating subscription plan {plan_id}: {e}")
            raise
