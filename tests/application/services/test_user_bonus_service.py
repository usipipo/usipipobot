import pytest
from datetime import datetime, timezone, timedelta

from domain.entities.user import User
from domain.entities.data_package import DataPackage, PackageType
from application.services.user_bonus_service import UserBonusService, BonusCalculation


class TestCalculateWelcomeBonus:
    def test_first_purchase_gets_welcome_bonus(self):
        user = User(telegram_id=123, purchase_count=0, welcome_bonus_used=False)
        service = UserBonusService()

        bonus = service.calculate_welcome_bonus(user)

        assert bonus.percent == 20
        assert "Bienvenida" in bonus.description

    def test_second_purchase_no_welcome_bonus(self):
        user = User(telegram_id=123, purchase_count=1, welcome_bonus_used=True)
        service = UserBonusService()

        bonus = service.calculate_welcome_bonus(user)

        assert bonus.percent == 0


class TestCalculateLoyaltyBonus:
    def test_no_loyalty_bonus_for_new_user(self):
        user = User(telegram_id=123, purchase_count=0, loyalty_bonus_percent=0)
        service = UserBonusService()

        bonus = service.calculate_loyalty_bonus(user)

        assert bonus.percent == 0

    def test_loyalty_bonus_applies_when_set(self):
        user = User(telegram_id=123, purchase_count=5, loyalty_bonus_percent=25)
        service = UserBonusService()

        bonus = service.calculate_loyalty_bonus(user)

        assert bonus.percent == 25
        assert "Fidelidad" in bonus.description

    def test_get_loyalty_bonus_for_purchase_count(self):
        service = UserBonusService()

        assert service.get_loyalty_bonus_for_purchase_count(1) == 0
        assert service.get_loyalty_bonus_for_purchase_count(3) == 10
        assert service.get_loyalty_bonus_for_purchase_count(5) == 25  # 10+15
        assert service.get_loyalty_bonus_for_purchase_count(10) == 50  # 10+15+25


class TestCalculateQuickRenewalBonus:
    def test_quick_renewal_bonus_when_package_expires_soon(self):
        user = User(telegram_id=123)
        expires_soon = datetime.now(timezone.utc) + timedelta(days=3)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_soon
            )
        ]
        service = UserBonusService()

        bonus = service.calculate_quick_renewal_bonus(user, active_packages)

        assert bonus.percent == 15
        assert "Recarga Rápida" in bonus.description

    def test_no_quick_renewal_when_package_expires_later(self):
        user = User(telegram_id=123)
        expires_later = datetime.now(timezone.utc) + timedelta(days=15)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_later
            )
        ]
        service = UserBonusService()

        bonus = service.calculate_quick_renewal_bonus(user, active_packages)

        assert bonus.percent == 0

    def test_no_quick_renewal_when_no_active_packages(self):
        user = User(telegram_id=123)
        service = UserBonusService()

        bonus = service.calculate_quick_renewal_bonus(user, [])

        assert bonus.percent == 0


class TestCalculateReferralBonus:
    def test_referral_bonus_with_referrals(self):
        user = User(telegram_id=123, referred_users_with_purchase=3)
        service = UserBonusService()

        bonus = service.calculate_referral_bonus_gb(user)

        assert bonus.gb_amount == 15  # 3 * 5GB
        assert "Referidos" in bonus.description

    def test_no_referral_bonus_without_referrals(self):
        user = User(telegram_id=123, referred_users_with_purchase=0)
        service = UserBonusService()

        bonus = service.calculate_referral_bonus_gb(user)

        assert bonus.gb_amount == 0
        assert bonus.percent == 0


class TestCalculateTotalBonus:
    def test_total_bonus_accumulates(self):
        user = User(
            telegram_id=123,
            purchase_count=0,
            welcome_bonus_used=False,
            loyalty_bonus_percent=25
        )
        expires_soon = datetime.now(timezone.utc) + timedelta(days=3)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_soon
            )
        ]
        service = UserBonusService()

        total_percent, bonuses = service.calculate_total_bonus(user, active_packages)

        # Welcome (20%) + Loyalty (25%) + Quick Renewal (15%) = 60%
        assert total_percent == 60
        assert len(bonuses) == 3

    def test_total_bonus_with_referred_first_purchase(self):
        user = User(telegram_id=123, purchase_count=1, welcome_bonus_used=True)
        service = UserBonusService()

        total_percent, bonuses = service.calculate_total_bonus(
            user, [], is_referred_user_first_purchase=True
        )

        # Referral first purchase bonus (10%)
        assert total_percent == 10
        assert len(bonuses) == 1
        assert "Referido Primera Compra" in bonuses[0].description

    def test_no_bonuses_for_regular_user(self):
        user = User(
            telegram_id=123,
            purchase_count=2,
            welcome_bonus_used=True,
            loyalty_bonus_percent=0
        )
        expires_later = datetime.now(timezone.utc) + timedelta(days=15)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_later
            )
        ]
        service = UserBonusService()

        total_percent, bonuses = service.calculate_total_bonus(user, active_packages)

        assert total_percent == 0
        assert len(bonuses) == 0
