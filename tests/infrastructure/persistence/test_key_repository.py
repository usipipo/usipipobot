import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.vpn_key import VpnKey, KeyType


class TestKeyRepository:
    """Tests for KeyRepository using mocks."""

    @pytest.mark.asyncio
    async def test_save_new_key(self, mock_key_repo):
        key = VpnKey(
            id=str(uuid.uuid4()),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="New Key",
            key_data="ss://test",
            external_id="key-123",
        )
        mock_key_repo.save.return_value = key

        result = await mock_key_repo.save(key, current_user_id=123456789)

        mock_key_repo.save.assert_called_once()
        assert result.key_type == KeyType.OUTLINE

    @pytest.mark.asyncio
    async def test_save_existing_key(self, mock_key_repo, sample_vpn_key):
        mock_key_repo.save.return_value = sample_vpn_key

        result = await mock_key_repo.save(sample_vpn_key, current_user_id=123456789)

        mock_key_repo.save.assert_called_once()
        assert result == sample_vpn_key

    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_keys(self, mock_key_repo, sample_vpn_key):
        mock_key_repo.get_by_user_id.return_value = [sample_vpn_key]

        result = await mock_key_repo.get_by_user_id(123456789, current_user_id=123456789)

        assert len(result) == 1
        assert result[0].user_id == 123456789

    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_empty(self, mock_key_repo):
        mock_key_repo.get_by_user_id.return_value = []

        result = await mock_key_repo.get_by_user_id(999, current_user_id=123456789)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_active_returns_only_active(self, mock_key_repo, sample_vpn_key):
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
    async def test_delete_soft_deletes(self, mock_key_repo):
        mock_key_repo.delete.return_value = True

        result = await mock_key_repo.delete(uuid.uuid4(), current_user_id=123456789)

        assert result is True
        mock_key_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_usage_success(self, mock_key_repo):
        mock_key_repo.update_usage.return_value = True

        result = await mock_key_repo.update_usage(uuid.uuid4(), 1024, current_user_id=123456789)

        assert result is True
        mock_key_repo.update_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_data_usage_success(self, mock_key_repo):
        mock_key_repo.reset_data_usage.return_value = True

        result = await mock_key_repo.reset_data_usage(uuid.uuid4(), current_user_id=123456789)

        assert result is True
        mock_key_repo.reset_data_usage.assert_called_once()
