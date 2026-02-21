"""
Tests para DataPackageRepository.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.entities.data_package import DataPackage, PackageType
from infrastructure.persistence.postgresql.data_package_repository import \
    PostgresDataPackageRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    return PostgresDataPackageRepository(mock_session)


@pytest.fixture
def sample_data_package():
    return DataPackage(
        user_id=123456789,
        package_type=PackageType.PREMIUM,
        data_limit_bytes=10737418240,
        stars_paid=100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        id=None,
        data_used_bytes=0,
        is_active=True,
        telegram_payment_id="payment_123",
    )


@pytest.fixture
def sample_model():
    model = MagicMock()
    model.id = uuid.uuid4()
    model.user_id = 123456789
    model.package_type = "premium"
    model.data_limit_bytes = 10737418240
    model.data_used_bytes = 0
    model.stars_paid = 100
    model.purchased_at = datetime.now(timezone.utc)
    model.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    model.is_active = True
    model.telegram_payment_id = "payment_123"
    return model


class TestSaveNewPackage:
    @pytest.mark.asyncio
    async def test_save_new_package_sets_id(
        self, repository, mock_session, sample_data_package
    ):
        mock_session.get.return_value = None

        result = await repository.save(sample_data_package, current_user_id=123456789)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_save_new_package_calls_set_user(
        self, repository, mock_session, sample_data_package
    ):
        mock_session.get.return_value = None

        await repository.save(sample_data_package, current_user_id=123456789)

        mock_session.execute.assert_called()


class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity(
        self, repository, mock_session, sample_model
    ):
        package_id = sample_model.id
        mock_session.get.return_value = sample_model

        result = await repository.get_by_id(package_id, current_user_id=123456789)

        assert result is not None
        assert result.id == sample_model.id
        assert result.user_id == sample_model.user_id
        assert result.package_type == PackageType.PREMIUM
        assert result.data_limit_bytes == sample_model.data_limit_bytes

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self, repository, mock_session
    ):
        package_id = uuid.uuid4()
        mock_session.get.return_value = None

        result = await repository.get_by_id(package_id, current_user_id=123456789)

        assert result is None


class TestGetByUser:
    @pytest.mark.asyncio
    async def test_get_by_user_returns_list(
        self, repository, mock_session, sample_model
    ):
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [sample_model]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute.return_value = result_mock

        result = await repository.get_by_user(123456789, current_user_id=123456789)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].user_id == 123456789

    @pytest.mark.asyncio
    async def test_get_by_user_returns_empty_list_on_error(
        self, repository, mock_session
    ):
        mock_session.execute.side_effect = Exception("DB error")

        result = await repository.get_by_user(123456789, current_user_id=123456789)

        assert result == []


class TestUpdateUsage:
    @pytest.mark.asyncio
    async def test_update_usage_returns_true_on_success(self, repository, mock_session):
        package_id = uuid.uuid4()

        result = await repository.update_usage(
            package_id, 1024, current_user_id=123456789
        )

        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_update_usage_returns_false_on_error(self, repository, mock_session):
        package_id = uuid.uuid4()
        mock_session.execute.side_effect = Exception("DB error")

        result = await repository.update_usage(
            package_id, 1024, current_user_id=123456789
        )

        mock_session.rollback.assert_called_once()
        assert result is False


class TestDeactivate:
    @pytest.mark.asyncio
    async def test_deactivate_returns_true_on_success(self, repository, mock_session):
        package_id = uuid.uuid4()

        result = await repository.deactivate(package_id, current_user_id=123456789)

        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_returns_false_on_error(self, repository, mock_session):
        package_id = uuid.uuid4()
        mock_session.execute.side_effect = Exception("DB error")

        result = await repository.deactivate(package_id, current_user_id=123456789)

        mock_session.rollback.assert_called_once()
        assert result is False
