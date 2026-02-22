import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from application.services.payment_service import PaymentService
from domain.entities.user import User, UserRole


@pytest.fixture
def payment_service(mock_user_repo, mock_transaction_repo):
    return PaymentService(
        user_repo=mock_user_repo,
        transaction_repo=mock_transaction_repo,
    )


class TestRecordTransaction:
    @pytest.mark.asyncio
    async def test_record_transaction_success(self, payment_service, mock_user_repo, mock_transaction_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_transaction_repo.record_transaction.return_value = True

        result = await payment_service.record_transaction(
            telegram_id=123456789,
            amount=50,
            transaction_type="purchase",
            description="Test purchase",
            reference_id="ref-123",
            telegram_payment_id="pay-123",
        )

        assert result is True
        mock_transaction_repo.record_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_transaction_user_not_found(self, payment_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        result = await payment_service.record_transaction(
            telegram_id=999,
            amount=50,
            transaction_type="purchase",
            description="Test",
        )

        assert result is False


class TestRedeemCredits:
    @pytest.mark.asyncio
    async def test_redeem_credits_success(self, payment_service, mock_user_repo, sample_user):
        sample_user.referral_credits = 100
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.redeem_credits(
            telegram_id=123456789,
            credits=30,
            description="Test redemption",
        )

        assert result is True
        assert sample_user.referral_credits == 70

    @pytest.mark.asyncio
    async def test_redeem_credits_insufficient(self, payment_service, mock_user_repo, sample_user):
        sample_user.referral_credits = 10
        mock_user_repo.get_by_id.return_value = sample_user

        result = await payment_service.redeem_credits(
            telegram_id=123456789,
            credits=50,
            description="Test",
        )

        assert result is False


class TestGetUserCredits:
    @pytest.mark.asyncio
    async def test_get_user_credits_returns_value(self, payment_service, mock_user_repo, sample_user):
        sample_user.referral_credits = 150
        mock_user_repo.get_by_id.return_value = sample_user

        credits = await payment_service.get_user_credits(123456789)

        assert credits == 150

    @pytest.mark.asyncio
    async def test_get_user_credits_not_found(self, payment_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        credits = await payment_service.get_user_credits(999)

        assert credits is None


class TestAddStorage:
    @pytest.mark.asyncio
    async def test_add_storage_increases(self, payment_service, mock_user_repo, sample_user):
        sample_user.free_data_limit_bytes = 10 * 1024**3
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.add_storage(123456789, gb=5)

        assert result is True
        assert sample_user.free_data_limit_bytes == 15 * 1024**3
