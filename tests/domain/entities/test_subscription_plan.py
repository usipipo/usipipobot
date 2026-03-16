"""Tests for SubscriptionPlan entity."""

from datetime import datetime, timedelta, timezone

import pytest

from domain.entities.subscription_plan import PlanType, SubscriptionPlan


class TestSubscriptionPlanEntity:
    def test_create_subscription_plan(self):
        """Test creating a subscription plan entity."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)

        plan = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_123",
            starts_at=now,
            expires_at=expires,
        )

        assert plan.user_id == 123
        assert plan.plan_type == PlanType.ONE_MONTH
        assert plan.stars_paid == 360
        assert plan.payment_id == "pay_123"
        assert plan.is_active is True
        assert plan.id is not None

    def test_duration_days_property(self):
        """Test duration_days returns correct values per plan type."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=90)

        plan_1m = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_1m",
            starts_at=now,
            expires_at=expires,
        )
        plan_3m = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.THREE_MONTHS,
            stars_paid=960,
            payment_id="pay_3m",
            starts_at=now,
            expires_at=expires,
        )
        plan_6m = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.SIX_MONTHS,
            stars_paid=1560,
            payment_id="pay_6m",
            starts_at=now,
            expires_at=expires,
        )

        assert plan_1m.duration_days == 30
        assert plan_3m.duration_days == 90
        assert plan_6m.duration_days == 180

    def test_days_remaining_property(self):
        """Test days_remaining calculation."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=15)

        plan = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_123",
            starts_at=now,
            expires_at=expires,
        )

        # Allow 1 day tolerance for test execution time
        assert plan.days_remaining in [14, 15]

    def test_is_expiring_soon_property(self):
        """Test is_expiring_soon returns True when < 3 days."""
        now = datetime.now(timezone.utc)
        expires_soon = now + timedelta(days=2)
        expires_later = now + timedelta(days=5)

        plan_soon = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_soon",
            starts_at=now,
            expires_at=expires_soon,
        )
        plan_later = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_later",
            starts_at=now,
            expires_at=expires_later,
        )

        assert plan_soon.is_expiring_soon is True
        assert plan_later.is_expiring_soon is False

    def test_is_expired_property(self):
        """Test is_expired returns True when past expiration."""
        now = datetime.now(timezone.utc)
        expired = now - timedelta(days=5)
        active = now + timedelta(days=5)

        plan_expired = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_expired",
            starts_at=now - timedelta(days=35),
            expires_at=expired,
        )
        plan_active = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_active",
            starts_at=now,
            expires_at=active,
        )

        assert plan_expired.is_expired is True
        assert plan_active.is_expired is False
