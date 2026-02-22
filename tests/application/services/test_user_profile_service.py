import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from application.services.user_profile_service import UserProfileService, UserProfileSummary
from application.services.referral_service import ReferralStats
from domain.entities.user import User, UserStatus, UserRole


class TestGetUserProfileSummary:
    """Tests for get_user_profile_summary."""

    @pytest.fixture
    def mock_transaction_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_data_package_service(self):
        service = AsyncMock()
        service.get_user_data_summary = AsyncMock()
        return service

    @pytest.fixture
    def mock_referral_service(self):
        service = AsyncMock()
        service.get_referral_stats = AsyncMock()
        return service

    @pytest.fixture
    def mock_vpn_service(self):
        service = AsyncMock()
        service.get_user_status = AsyncMock()
        return service

    @pytest.fixture
    def service(
        self,
        mock_transaction_repo,
        mock_data_package_service,
        mock_referral_service,
        mock_vpn_service,
    ):
        return UserProfileService(
            transaction_repo=mock_transaction_repo,
            data_package_service=mock_data_package_service,
            referral_service=mock_referral_service,
            vpn_service=mock_vpn_service,
        )

    @pytest.mark.asyncio
    async def test_get_user_profile_summary_success(
        self,
        service,
        mock_vpn_service,
        mock_data_package_service,
        mock_referral_service,
    ):
        user = User(
            telegram_id=123,
            username="testuser",
            full_name="Test User",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
            max_keys=3,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        mock_key = MagicMock()
        mock_key.used_bytes = 1024 * 1024 * 100

        mock_key_unused = MagicMock()
        mock_key_unused.used_bytes = 0

        mock_vpn_service.get_user_status.return_value = {
            "user": user,
            "keys_count": 2,
            "keys": [mock_key, mock_key_unused],
            "total_used_gb": 5.0,
            "total_limit_gb": 20.0,
            "remaining_gb": 15.0,
        }

        mock_data_package_service.get_user_data_summary.return_value = {
            "active_packages": 3,
            "free_plan": {"remaining_gb": 2.5},
        }

        mock_referral_service.get_referral_stats.return_value = ReferralStats(
            referral_code="TEST123",
            total_referrals=5,
            referral_credits=200,
            referred_by=456,
        )

        result = await service.get_user_profile_summary(123, 123)

        assert result is not None
        assert result.user_id == 123
        assert result.username == "testuser"
        assert result.full_name == "Test User"
        assert result.status == "active"
        assert result.role == "user"
        assert result.max_keys == 3
        assert result.keys_count == 2
        assert result.keys_used == 1
        assert result.total_used_gb == 5.0
        assert result.total_limit_gb == 20.0
        assert result.remaining_gb == 15.0
        assert result.free_data_remaining_gb == 2.5
        assert result.active_packages == 3
        assert result.referral_code == "TEST123"
        assert result.total_referrals == 5
        assert result.referral_credits == 200
        assert result.referred_by == 456

    @pytest.mark.asyncio
    async def test_get_user_profile_summary_user_not_found(
        self,
        service,
        mock_vpn_service,
    ):
        mock_vpn_service.get_user_status.return_value = {
            "user": None,
            "keys_count": 0,
            "keys": [],
            "total_used_gb": 0.0,
            "total_limit_gb": 0.0,
            "remaining_gb": 0.0,
        }

        result = await service.get_user_profile_summary(999, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_profile_summary_admin_user(
        self,
        service,
        mock_vpn_service,
        mock_data_package_service,
        mock_referral_service,
    ):
        user = User(
            telegram_id=123,
            username="adminuser",
            full_name="Admin User",
            status=UserStatus.ACTIVE,
            role=UserRole.ADMIN,
            max_keys=999,
        )

        mock_vpn_service.get_user_status.return_value = {
            "user": user,
            "keys_count": 5,
            "keys": [],
            "total_used_gb": 100.0,
            "total_limit_gb": 500.0,
            "remaining_gb": 400.0,
        }

        mock_data_package_service.get_user_data_summary.return_value = {
            "active_packages": 10,
            "free_plan": {"remaining_gb": 0.0},
        }

        mock_referral_service.get_referral_stats.return_value = ReferralStats(
            referral_code="ADMIN123",
            total_referrals=0,
            referral_credits=0,
            referred_by=None,
        )

        result = await service.get_user_profile_summary(123, 123)

        assert result is not None
        assert result.role == "admin"
        assert result.max_keys == 999

    @pytest.mark.asyncio
    async def test_get_user_profile_summary_no_keys(
        self,
        service,
        mock_vpn_service,
        mock_data_package_service,
        mock_referral_service,
    ):
        user = User(
            telegram_id=123,
            username="newuser",
            full_name="New User",
        )

        mock_vpn_service.get_user_status.return_value = {
            "user": user,
            "keys_count": 0,
            "keys": [],
            "total_used_gb": 0.0,
            "total_limit_gb": 10.0,
            "remaining_gb": 10.0,
        }

        mock_data_package_service.get_user_data_summary.return_value = {
            "active_packages": 0,
            "free_plan": {"remaining_gb": 10.0},
        }

        mock_referral_service.get_referral_stats.return_value = ReferralStats(
            referral_code="NEW123",
            total_referrals=0,
            referral_credits=0,
            referred_by=None,
        )

        result = await service.get_user_profile_summary(123, 123)

        assert result is not None
        assert result.keys_count == 0
        assert result.keys_used == 0


class TestGetUserTransactions:
    """Tests for get_user_transactions."""

    @pytest.fixture
    def mock_transaction_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_data_package_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_referral_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_vpn_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_transaction_repo,
        mock_data_package_service,
        mock_referral_service,
        mock_vpn_service,
    ):
        return UserProfileService(
            transaction_repo=mock_transaction_repo,
            data_package_service=mock_data_package_service,
            referral_service=mock_referral_service,
            vpn_service=mock_vpn_service,
        )

    @pytest.mark.asyncio
    async def test_get_user_transactions_success(
        self,
        service,
        mock_transaction_repo,
    ):
        mock_transactions = [
            {
                "id": 1,
                "transaction_type": "referral_bonus",
                "amount": 100,
                "description": "Bonus for referral",
            },
            {
                "id": 2,
                "transaction_type": "package_purchase",
                "amount": -50,
                "description": "Basic package purchase",
            },
        ]
        mock_transaction_repo.get_user_transactions.return_value = mock_transactions

        result = await service.get_user_transactions(123, limit=10)

        assert len(result) == 2
        assert result[0]["transaction_type"] == "referral_bonus"
        assert result[1]["transaction_type"] == "package_purchase"
        mock_transaction_repo.get_user_transactions.assert_called_once_with(123, 10)

    @pytest.mark.asyncio
    async def test_get_user_transactions_empty(
        self,
        service,
        mock_transaction_repo,
    ):
        mock_transaction_repo.get_user_transactions.return_value = []

        result = await service.get_user_transactions(123, limit=10)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_transactions_custom_limit(
        self,
        service,
        mock_transaction_repo,
    ):
        mock_transactions = [{"id": i} for i in range(5)]
        mock_transaction_repo.get_user_transactions.return_value = mock_transactions

        result = await service.get_user_transactions(123, limit=5)

        mock_transaction_repo.get_user_transactions.assert_called_once_with(123, 5)

    @pytest.mark.asyncio
    async def test_get_user_transactions_error(
        self,
        service,
        mock_transaction_repo,
    ):
        mock_transaction_repo.get_user_transactions.side_effect = Exception("DB Error")

        result = await service.get_user_transactions(123, limit=10)

        assert result == []
