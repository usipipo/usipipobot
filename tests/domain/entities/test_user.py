import pytest

from domain.entities.user import User, UserRole, UserStatus


class TestUserBonusTrackingFields:
    def test_user_has_default_bonus_values(self):
        user = User(telegram_id=12345)

        assert user.purchase_count == 0
        assert user.loyalty_bonus_percent == 0
        assert user.welcome_bonus_used == False
        assert user.referred_users_with_purchase == 0

    def test_user_can_set_bonus_values(self):
        user = User(
            telegram_id=12345,
            purchase_count=5,
            loyalty_bonus_percent=25,
            welcome_bonus_used=True,
            referred_users_with_purchase=3,
        )

        assert user.purchase_count == 5
        assert user.loyalty_bonus_percent == 25
        assert user.welcome_bonus_used == True
        assert user.referred_users_with_purchase == 3
