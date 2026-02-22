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


class TestUpdateBalance:
    @pytest.mark.asyncio
    async def test_update_balance_deposit_increases(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 100
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.update_balance(
            telegram_id=123456789,
            amount=50,
            transaction_type="deposit",
            description="Test deposit",
            reference_id="ref-123",
            telegram_payment_id="pay-123",
        )

        assert result is True
        assert sample_user.balance_stars == 150

    @pytest.mark.asyncio
    async def test_update_balance_records_transaction(self, payment_service, mock_user_repo, mock_transaction_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        await payment_service.update_balance(
            telegram_id=123456789,
            amount=50,
            transaction_type="deposit",
            description="Test deposit",
            reference_id="ref-123",
            telegram_payment_id="pay-123",
        )

        mock_transaction_repo.record_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_balance_user_not_found(self, payment_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        result = await payment_service.update_balance(
            telegram_id=999,
            amount=50,
            transaction_type="deposit",
            description="Test",
            reference_id="ref-123",
            telegram_payment_id="pay-123",
        )

        assert result is False


class TestDeductBalance:
    @pytest.mark.asyncio
    async def test_deduct_balance_success(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 100
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.deduct_balance(
            telegram_id=123456789,
            amount=30,
            description="Purchase",
        )

        assert result is True
        assert sample_user.balance_stars == 70

    @pytest.mark.asyncio
    async def test_deduct_balance_insufficient(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 10
        mock_user_repo.get_by_id.return_value = sample_user

        result = await payment_service.deduct_balance(
            telegram_id=123456789,
            amount=50,
            description="Purchase",
        )

        assert result is False


class TestGetUserBalance:
    @pytest.mark.asyncio
    async def test_get_user_balance_returns_value(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 150
        mock_user_repo.get_by_id.return_value = sample_user

        balance = await payment_service.get_user_balance(123456789)

        assert balance == 150

    @pytest.mark.asyncio
    async def test_get_user_balance_not_found(self, payment_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        balance = await payment_service.get_user_balance(999)

        assert balance is None


class TestActivateVip:
    @pytest.mark.asyncio
    async def test_activate_vip_sets_expiry(self, payment_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.activate_vip(123456789, days=30)

        assert result is True
        assert sample_user.is_vip is True
        assert sample_user.vip_expires_at is not None


class TestAddStorage:
    @pytest.mark.asyncio
    async def test_add_storage_increases(self, payment_service, mock_user_repo, sample_user):
        sample_user.free_data_limit_bytes = 10 * 1024**3
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.add_storage(123456789, gb=5)

        assert result is True
        assert sample_user.free_data_limit_bytes == 15 * 1024**3
