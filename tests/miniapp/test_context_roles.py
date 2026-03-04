"""
Tests for MiniAppContext role recognition.

Issue #252: Mini App Web no reconoce roles de usuario desde la base de datos
"""

import pytest
from unittest.mock import MagicMock

from config import settings
from domain.entities.user import User, UserRole
from miniapp.routes_common import MiniAppContext
from miniapp.services.miniapp_auth import TelegramUser


class TestMiniAppContextIsAdmin:
    """Tests for MiniAppContext.is_admin property."""

    def test_is_admin_true_when_db_user_has_admin_role(self):
        """User with ADMIN role in DB should be recognized as admin."""
        telegram_user = TelegramUser(
            id=12345,
            first_name="Test",
            username="testuser"
        )
        db_user = User(
            telegram_id=12345,
            username="testuser",
            role=UserRole.ADMIN
        )

        ctx = MiniAppContext(user=telegram_user, db_user=db_user)

        assert ctx.is_admin is True

    def test_is_admin_false_when_db_user_has_user_role(self):
        """User with USER role in DB should NOT be admin."""
        telegram_user = TelegramUser(
            id=12345,
            first_name="Test",
            username="testuser"
        )
        db_user = User(
            telegram_id=12345,
            username="testuser",
            role=UserRole.USER
        )

        ctx = MiniAppContext(user=telegram_user, db_user=db_user)

        assert ctx.is_admin is False

    def test_is_admin_true_when_telegram_id_matches_admin_id(self):
        """User matching ADMIN_ID should be admin even without db_user."""
        admin_id = int(settings.ADMIN_ID)
        telegram_user = TelegramUser(
            id=admin_id,
            first_name="Admin",
            username="adminuser"
        )

        ctx = MiniAppContext(user=telegram_user, db_user=None)

        assert ctx.is_admin is True

    def test_is_admin_false_when_no_db_user_and_not_admin_id(self):
        """User without db_user and not matching ADMIN_ID should NOT be admin."""
        telegram_user = TelegramUser(
            id=99999,  # Different from ADMIN_ID
            first_name="Regular",
            username="regularuser"
        )

        ctx = MiniAppContext(user=telegram_user, db_user=None)

        assert ctx.is_admin is False

    def test_is_admin_db_role_takes_precedence_over_admin_id(self):
        """DB role should be checked before ADMIN_ID fallback."""
        # User with ADMIN role in DB but different ID from ADMIN_ID
        telegram_user = TelegramUser(
            id=55555,  # Different from ADMIN_ID
            first_name="Secondary",
            username="secondaryadmin"
        )
        db_user = User(
            telegram_id=55555,
            username="secondaryadmin",
            role=UserRole.ADMIN
        )

        ctx = MiniAppContext(user=telegram_user, db_user=db_user)

        # Should be admin because of DB role, even though ID doesn't match ADMIN_ID
        assert ctx.is_admin is True

    def test_is_admin_with_none_db_user(self):
        """Context without db_user should use ADMIN_ID fallback only."""
        telegram_user = TelegramUser(
            id=int(settings.ADMIN_ID),
            first_name="Fallback",
            username="fallbackadmin"
        )

        ctx = MiniAppContext(user=telegram_user, db_user=None)

        assert ctx.is_admin is True
