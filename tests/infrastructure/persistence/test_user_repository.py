import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.entities.vpn_key import VpnKey, KeyType
from domain.entities.user import User, UserStatus


class TestVpnKeyRepository:
    """Tests for KeyRepository using mocks."""

    @pytest.mark.asyncio
    async def test_save_key_calls_repo(self, mock_key_repo):
        key = VpnKey(
            id=str(uuid.uuid4()),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Test Key",
            key_data="ss://test",
            external_id="key-123",
        )
        mock_key_repo.save.return_value = key

        result = await mock_key_repo.save(key, current_user_id=123456789)

        mock_key_repo.save.assert_called_once_with(key, current_user_id=123456789)
        assert result == key

    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_keys(self, mock_key_repo, sample_vpn_key):
        mock_key_repo.get_by_user_id.return_value = [sample_vpn_key]

        result = await mock_key_repo.get_by_user_id(123456789, current_user_id=123456789)

        assert len(result) == 1
        assert result[0].user_id == 123456789

    @pytest.mark.asyncio
    async def test_get_all_active_returns_keys(self, mock_key_repo, sample_vpn_key):
        mock_key_repo.get_all_active.return_value = [sample_vpn_key]

        result = await mock_key_repo.get_all_active(current_user_id=123456789)

        assert len(result) == 1
        assert result[0].is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_key_repo, sample_vpn_key):
        mock_key_repo.get_by_id.return_value = sample_vpn_key

        result = await mock_key_repo.get_by_id(sample_vpn_key.id, current_user_id=123456789)

        assert result is not None
        assert result.id == sample_vpn_key.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_key_repo):
        mock_key_repo.get_by_id.return_value = None

        result = await mock_key_repo.get_by_id(uuid.uuid4(), current_user_id=123456789)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, mock_key_repo):
        mock_key_repo.delete.return_value = True

        result = await mock_key_repo.delete(uuid.uuid4(), current_user_id=123456789)

        assert result is True
        mock_key_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_usage(self, mock_key_repo):
        mock_key_repo.update_usage.return_value = True

        result = await mock_key_repo.update_usage(uuid.uuid4(), 1024, current_user_id=123456789)

        assert result is True
        mock_key_repo.update_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_data_usage(self, mock_key_repo):
        mock_key_repo.reset_data_usage.return_value = True

        result = await mock_key_repo.reset_data_usage(uuid.uuid4(), current_user_id=123456789)

        assert result is True
        mock_key_repo.reset_data_usage.assert_called_once()


class TestUserRepository:
    """Tests for UserRepository using mocks."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_user(self, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user

        result = await mock_user_repo.get_by_id(123456789, current_user_id=123456789)

        assert result is not None
        assert result.telegram_id == 123456789
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none(self, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        result = await mock_user_repo.get_by_id(999, current_user_id=123456789)

        assert result is None

    @pytest.mark.asyncio
    async def test_save_new_user(self, mock_user_repo):
        user = User(telegram_id=123456789, username="newuser")
        mock_user_repo.save.return_value = user

        result = await mock_user_repo.save(user, current_user_id=123456789)

        mock_user_repo.save.assert_called_once_with(user, current_user_id=123456789)
        assert result.telegram_id == 123456789

    @pytest.mark.asyncio
    async def test_save_existing_user(self, mock_user_repo, sample_user):
        mock_user_repo.save.return_value = sample_user

        result = await mock_user_repo.save(sample_user, current_user_id=123456789)

        mock_user_repo.save.assert_called_once()
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, mock_user_repo):
        mock_user_repo.exists.return_value = True

        result = await mock_user_repo.exists(123456789, current_user_id=123456789)

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self, mock_user_repo):
        mock_user_repo.exists.return_value = False

        result = await mock_user_repo.exists(999, current_user_id=123456789)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_by_referral_code_found(self, mock_user_repo, sample_user):
        sample_user.referral_code = "ABC123"
        mock_user_repo.get_by_referral_code.return_value = sample_user

        result = await mock_user_repo.get_by_referral_code("ABC123", current_user_id=123456789)

        assert result is not None
        assert result.referral_code == "ABC123"

    @pytest.mark.asyncio
    async def test_get_by_referral_code_not_found(self, mock_user_repo):
        mock_user_repo.get_by_referral_code.return_value = None

        result = await mock_user_repo.get_by_referral_code("INVALID", current_user_id=123456789)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_referrals_returns_list(self, mock_user_repo, sample_user):
        mock_user_repo.get_referrals.return_value = [
            {"telegram_id": 111, "username": "ref1"},
            {"telegram_id": 222, "username": "ref2"},
        ]

        result = await mock_user_repo.get_referrals(123456789, current_user_id=123456789)

        assert isinstance(result, list)
        assert len(result) == 2
