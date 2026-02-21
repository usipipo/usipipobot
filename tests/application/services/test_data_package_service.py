import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.services.data_package_service import (PACKAGE_OPTIONS,
                                                       DataPackageService)
from domain.entities.data_package import DataPackage, PackageType


@pytest.fixture
def mock_package_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_package_repo, mock_user_repo):
    return DataPackageService(package_repo=mock_package_repo, user_repo=mock_user_repo)


class TestGetAvailablePackages:
    def test_returns_all_package_options(self, service):
        packages = service.get_available_packages()

        assert len(packages) == 4
        assert packages[0].name == "Básico"
        assert packages[0].data_gb == 10
        assert packages[0].stars == 50

    def test_premium_has_bonus(self, service):
        packages = service.get_available_packages()
        premium = [p for p in packages if p.name == "Premium"][0]

        assert premium.bonus_percent == 30


class TestPurchasePackage:
    @pytest.mark.asyncio
    async def test_purchase_creates_package(
        self, service, mock_package_repo, mock_user_repo
    ):
        mock_user_repo.get_by_id.return_value = MagicMock(telegram_id=123)
        mock_package_repo.save.return_value = DataPackage(
            user_id=123,
            package_type=PackageType.BASIC,
            data_limit_bytes=10 * 1024**3,
            stars_paid=50,
            expires_at=datetime.now(timezone.utc) + timedelta(days=35),
        )

        result = await service.purchase_package(
            user_id=123,
            package_type="basic",
            telegram_payment_id="pay_123",
            current_user_id=123,
        )

        assert result is not None
        mock_package_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_purchase_invalid_package_raises(self, service):
        with pytest.raises(ValueError, match="Tipo de paquete inválido"):
            await service.purchase_package(
                user_id=123,
                package_type="invalid",
                telegram_payment_id="pay_123",
                current_user_id=123,
            )


class TestGetUserPackages:
    @pytest.mark.asyncio
    async def test_returns_user_packages(self, service, mock_package_repo):
        mock_package_repo.get_by_user.return_value = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10 * 1024**3,
                stars_paid=50,
                expires_at=datetime.now(timezone.utc) + timedelta(days=35),
            )
        ]

        result = await service.get_user_packages(123, current_user_id=123)

        assert len(result) == 1
        mock_package_repo.get_by_user.assert_called_once_with(123, 123)


class TestGetUserDataSummary:
    @pytest.mark.asyncio
    async def test_returns_aggregated_summary(
        self, service, mock_package_repo, mock_user_repo
    ):
        mock_package_repo.get_valid_by_user.return_value = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10 * 1024**3,
                stars_paid=50,
                data_used_bytes=5 * 1024**3,
                expires_at=datetime.now(timezone.utc) + timedelta(days=35),
            ),
            DataPackage(
                user_id=123,
                package_type=PackageType.PREMIUM,
                data_limit_bytes=100 * 1024**3,
                stars_paid=110,
                data_used_bytes=20 * 1024**3,
                expires_at=datetime.now(timezone.utc) + timedelta(days=35),
            ),
        ]
        mock_user_repo.get_by_id.return_value = None

        result = await service.get_user_data_summary(123, current_user_id=123)

        assert result["total_limit_gb"] == 110.0
        assert result["total_used_gb"] == 25.0
        assert result["remaining_gb"] == 85.0
        assert result["active_packages"] == 2

    @pytest.mark.asyncio
    async def test_returns_detailed_packages_info(
        self, service, mock_package_repo, mock_user_repo
    ):
        from domain.entities.user import User

        expires_at = datetime.now(timezone.utc) + timedelta(days=15)
        mock_package_repo.get_valid_by_user.return_value = [
            DataPackage(
                id=uuid.uuid4(),
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10 * 1024**3,
                stars_paid=50,
                data_used_bytes=int(3.2 * 1024**3),
                expires_at=expires_at,
                purchased_at=datetime.now(timezone.utc) - timedelta(days=20),
            )
        ]
        mock_user_repo.get_by_id.return_value = User(
            telegram_id=123,
            free_data_limit_bytes=10 * 1024**3,
            free_data_used_bytes=int(1.5 * 1024**3),
        )

        result = await service.get_user_data_summary(123, current_user_id=123)

        assert "packages" in result
        assert len(result["packages"]) == 1
        assert result["packages"][0]["name"] == "Básico"
        assert result["packages"][0]["days_remaining"] > 0
        assert "free_plan" in result
        assert result["free_plan"]["remaining_gb"] == 8.5
        assert result["remaining_gb"] == pytest.approx(15.3)


class TestConsumeData:
    @pytest.mark.asyncio
    async def test_consume_updates_usage(self, service, mock_package_repo):
        package = DataPackage(
            id=uuid.uuid4(),
            user_id=123,
            package_type=PackageType.BASIC,
            data_limit_bytes=10 * 1024**3,
            stars_paid=50,
            data_used_bytes=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=35),
        )
        mock_package_repo.get_valid_by_user.return_value = [package]
        mock_package_repo.update_usage.return_value = True

        await service.consume_data(123, 1024, current_user_id=123)

        mock_package_repo.update_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_consume_returns_false_when_no_packages(
        self, service, mock_package_repo
    ):
        mock_package_repo.get_valid_by_user.return_value = []

        result = await service.consume_data(123, 1024, current_user_id=123)

        assert result is False

    @pytest.mark.asyncio
    async def test_consume_returns_true_when_packages_exist(
        self, service, mock_package_repo
    ):
        package = DataPackage(
            id=uuid.uuid4(),
            user_id=123,
            package_type=PackageType.BASIC,
            data_limit_bytes=10 * 1024**3,
            stars_paid=50,
            data_used_bytes=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=35),
        )
        mock_package_repo.get_valid_by_user.return_value = [package]
        mock_package_repo.update_usage.return_value = True

        result = await service.consume_data(123, 1024, current_user_id=123)

        assert result is True


class TestExpireOldPackages:
    @pytest.mark.asyncio
    async def test_expire_deactivates_old_packages(self, service, mock_package_repo):
        expired_package = DataPackage(
            id=uuid.uuid4(),
            user_id=123,
            package_type=PackageType.BASIC,
            data_limit_bytes=10 * 1024**3,
            stars_paid=50,
            data_used_bytes=0,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        mock_package_repo.get_expired_packages.return_value = [expired_package]
        mock_package_repo.deactivate.return_value = True

        result = await service.expire_old_packages(admin_user_id=1)

        assert result == 1
        mock_package_repo.get_expired_packages.assert_called_once_with(1)
        mock_package_repo.deactivate.assert_called_once_with(expired_package.id, 1)

    @pytest.mark.asyncio
    async def test_expire_returns_zero_when_no_expired_packages(
        self, service, mock_package_repo
    ):
        mock_package_repo.get_expired_packages.return_value = []

        result = await service.expire_old_packages(admin_user_id=1)

        assert result == 0
