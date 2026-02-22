"""
Tests para ReferralService.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock

from application.services.referral_service import ReferralService, ReferralStats
from domain.entities.user import User


class TestRegisterReferral:
    """Tests para register_referral."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_referral_code = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        repo.update_referral_credits = AsyncMock(return_value=True)
        repo.get_referrals_by_user = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        repo = AsyncMock()
        repo.record_transaction = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_register_referral_success(
        self, service, mock_user_repo, mock_transaction_repo
    ):
        referrer = User(
            telegram_id=123,
            referral_code="ABC123",
            referral_credits=0,
        )
        new_user = User(
            telegram_id=456,
            referral_code="DEF456",
            referral_credits=0,
            referred_by=None,
        )

        mock_user_repo.get_by_referral_code.return_value = referrer
        mock_user_repo.get_by_id.return_value = new_user

        result = await service.register_referral(456, "ABC123", 123)

        assert result["success"] is True
        assert result["referrer_id"] == 123
        mock_user_repo.update_referral_credits.assert_called()
        mock_transaction_repo.record_transaction.assert_called()

    @pytest.mark.asyncio
    async def test_register_referral_invalid_code(
        self, service, mock_user_repo
    ):
        mock_user_repo.get_by_referral_code.return_value = None

        result = await service.register_referral(456, "INVALID", 123)

        assert result["success"] is False
        assert result["error"] == "invalid_code"

    @pytest.mark.asyncio
    async def test_register_referral_self_referral(
        self, service, mock_user_repo
    ):
        referrer = User(
            telegram_id=123,
            referral_code="ABC123",
        )
        mock_user_repo.get_by_referral_code.return_value = referrer

        result = await service.register_referral(123, "ABC123", 123)

        assert result["success"] is False
        assert result["error"] == "self_referral"

    @pytest.mark.asyncio
    async def test_register_referral_already_referred(
        self, service, mock_user_repo
    ):
        referrer = User(
            telegram_id=123,
            referral_code="ABC123",
        )
        new_user = User(
            telegram_id=456,
            referral_code="DEF456",
            referred_by=999,
        )

        mock_user_repo.get_by_referral_code.return_value = referrer
        mock_user_repo.get_by_id.return_value = new_user

        result = await service.register_referral(456, "ABC123", 123)

        assert result["success"] is False
        assert result["error"] == "already_referred"


class TestGetReferralStats:
    """Tests para get_referral_stats."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_referrals_by_user = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_referral_stats_success(
        self, service, mock_user_repo
    ):
        user = User(
            telegram_id=123,
            referral_code="ABC123",
            referral_credits=200,
            referred_by=None,
        )
        mock_user_repo.get_by_id.return_value = user

        stats = await service.get_referral_stats(123, 123)

        assert stats.referral_code == "ABC123"
        assert stats.referral_credits == 200
        assert stats.total_referrals == 0

    @pytest.mark.asyncio
    async def test_get_referral_stats_user_not_found(
        self, service, mock_user_repo
    ):
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Usuario no encontrado"):
            await service.get_referral_stats(999, 999)


class TestRedeemCreditsForData:
    """Tests para redeem_credits_for_data."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        repo.update_referral_credits = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        repo = AsyncMock()
        repo.record_transaction = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_redeem_credits_for_data_success(
        self, service, mock_user_repo, mock_transaction_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=250,
            free_data_limit_bytes=10 * 1024**3,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_data(123, 200, 123)

        assert result["success"] is True
        assert result["gb_added"] == 2
        assert result["credits_spent"] == 200

    @pytest.mark.asyncio
    async def test_redeem_credits_insufficient(
        self, service, mock_user_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=50,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_data(123, 200, 123)

        assert result["success"] is False
        assert result["error"] == "insufficient_credits"


class TestRedeemCreditsForSlot:
    """Tests para redeem_credits_for_slot."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.update_referral_credits = AsyncMock(return_value=True)
        repo.increment_max_keys = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        repo = AsyncMock()
        repo.record_transaction = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_redeem_credits_for_slot_success(
        self, service, mock_user_repo, mock_transaction_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=600,
            max_keys=2,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_slot(123, 123)

        assert result["success"] is True
        assert result["slots_added"] == 1
        assert result["credits_spent"] == 500

    @pytest.mark.asyncio
    async def test_redeem_credits_for_slot_insufficient(
        self, service, mock_user_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=100,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_slot(123, 123)

        assert result["success"] is False
        assert result["error"] == "insufficient_credits"
