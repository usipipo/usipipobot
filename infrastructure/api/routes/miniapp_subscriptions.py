"""
Rutas de suscripciones para la Mini App.

Incluye endpoints para ver planes, activar suscripciones y gestionar estado premium.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.services.common.container import get_service
from application.services.subscription_service import SubscriptionService
from miniapp.routes_common import get_current_user
from utils.logger import logger

router = APIRouter(tags=["Mini App Web - Subscriptions"])


class SubscriptionPlanResponse(BaseModel):
    """Response model for subscription plans."""

    plan_type: str
    name: str
    duration_months: int
    stars: int
    data_limit: str
    bonus_percent: int = 0


class UserSubscriptionResponse(BaseModel):
    """Response model for user's active subscription."""

    is_premium: bool
    plan_type: Optional[str] = None
    plan_name: Optional[str] = None
    stars_paid: Optional[int] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    is_expiring_soon: Optional[bool] = None


class ActivateSubscriptionRequest(BaseModel):
    """Request model for activating a subscription."""

    plan_type: str
    payment_id: str


class ActivateSubscriptionResponse(BaseModel):
    """Response model for subscription activation."""

    success: bool
    message: str
    subscription: Optional[UserSubscriptionResponse] = None


@router.get("/api/subscriptions/plans")
async def get_subscription_plans(current_user: dict = Depends(get_current_user)):
    """
    Get available subscription plans.

    Returns list of all available subscription plans with pricing.
    """
    logger.info(f"📋 User {current_user['id']} fetching subscription plans")
    try:
        subscription_service = get_service(SubscriptionService)
        plans = subscription_service.get_available_plans()

        return [
            SubscriptionPlanResponse(
                plan_type=plan.plan_type.value,
                name=plan.name,
                duration_months=plan.duration_months,
                stars=plan.stars,
                data_limit=plan.data_limit,
                bonus_percent=plan.bonus_percent,
            )
            for plan in plans
        ]
    except Exception as e:
        logger.error(f"Error fetching subscription plans: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener planes")


@router.get("/api/subscriptions/status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """
    Get user's current subscription status.

    Returns premium status and active subscription details.
    """
    user_id = current_user["id"]
    logger.info(f"📊 User {user_id} checking subscription status")
    try:
        subscription_service = get_service(SubscriptionService)

        is_premium = await subscription_service.is_premium_user(user_id, user_id)
        subscription = await subscription_service.get_user_subscription(user_id, user_id)

        if not is_premium or not subscription:
            return UserSubscriptionResponse(is_premium=False)

        plan_option = subscription_service.get_plan_option(subscription.plan_type.value)
        plan_name = plan_option.name if plan_option else subscription.plan_type.value

        return UserSubscriptionResponse(
            is_premium=True,
            plan_type=subscription.plan_type.value,
            plan_name=plan_name,
            stars_paid=subscription.stars_paid,
            starts_at=subscription.starts_at,
            expires_at=subscription.expires_at,
            days_remaining=subscription.days_remaining,
            is_expiring_soon=subscription.is_expiring_soon,
        )
    except Exception as e:
        logger.error(f"Error fetching subscription status: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estado de suscripción")


@router.post("/api/subscriptions/activate")
async def activate_subscription(
    request: ActivateSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Activate a subscription plan.

    Activates subscription after payment verification.
    For now, simulates payment success (TODO: integrate with Telegram Stars payment).
    """
    user_id = current_user["id"]
    logger.info(f"💎 User {user_id} activating subscription: {request.plan_type}")
    try:
        subscription_service = get_service(SubscriptionService)

        # Check for existing active subscription
        is_premium = await subscription_service.is_premium_user(user_id, user_id)
        if is_premium:
            raise HTTPException(status_code=400, detail="Ya tienes una suscripción activa")

        # Get plan details
        plan_option = subscription_service.get_plan_option(request.plan_type)
        if not plan_option:
            raise HTTPException(status_code=400, detail="Plan no válido")

        # Activate subscription (payment verification would go here)
        subscription = await subscription_service.activate_subscription(
            user_id=user_id,
            plan_type=request.plan_type,
            stars_paid=plan_option.stars,
            payment_id=request.payment_id,
            current_user_id=user_id,
        )

        plan_name = plan_option.name if plan_option else subscription.plan_type.value

        return ActivateSubscriptionResponse(
            success=True,
            message=f"Suscripción {plan_name} activada exitosamente",
            subscription=UserSubscriptionResponse(
                is_premium=True,
                plan_type=subscription.plan_type.value,
                plan_name=plan_name,
                stars_paid=subscription.stars_paid,
                starts_at=subscription.starts_at,
                expires_at=subscription.expires_at,
                days_remaining=subscription.days_remaining,
                is_expiring_soon=subscription.is_expiring_soon,
            ),
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Subscription activation failed for user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating subscription: {e}")
        raise HTTPException(status_code=500, detail="Error al activar suscripción")


@router.get("/api/subscriptions/check/{user_id}")
async def check_user_subscription(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Check subscription status for a specific user (admin only).

    Allows admins to check any user's subscription status.
    """
    logger.info(f"🔍 Admin {current_user['id']} checking subscription for user {user_id}")
    try:
        subscription_service = get_service(SubscriptionService)

        is_premium = await subscription_service.is_premium_user(user_id, current_user["id"])
        subscription = await subscription_service.get_user_subscription(user_id, current_user["id"])

        if not is_premium or not subscription:
            return UserSubscriptionResponse(is_premium=False)

        plan_option = subscription_service.get_plan_option(subscription.plan_type.value)
        plan_name = plan_option.name if plan_option else subscription.plan_type.value

        return UserSubscriptionResponse(
            is_premium=True,
            plan_type=subscription.plan_type.value,
            plan_name=plan_name,
            stars_paid=subscription.stars_paid,
            starts_at=subscription.starts_at,
            expires_at=subscription.expires_at,
            days_remaining=subscription.days_remaining,
            is_expiring_soon=subscription.is_expiring_soon,
        )
    except Exception as e:
        logger.error(f"Error checking user subscription: {e}")
        raise HTTPException(status_code=500, detail="Error al verificar suscripción")
