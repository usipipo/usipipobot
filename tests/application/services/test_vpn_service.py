import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.services.vpn_service import VpnService
from domain.entities.user import User, UserRole
from domain.entities.vpn_key import VpnKey, KeyType


@pytest.fixture
def vpn_service(mock_user_repo, mock_key_repo, mock_outline_client, mock_wireguard_client):
    return VpnService(
        user_repo=mock_user_repo,
        key_repo=mock_key_repo,
        outline_client=mock_outline_client,
        wireguard_client=mock_wireguard_client,
    )


class TestCreateKey:
    @pytest.mark.asyncio
    async def test_create_outline_key_success(self, vpn_service, mock_user_repo, mock_key_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_key_repo.save.return_value = VpnKey(
            id=str(uuid.uuid4()),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Mi iPhone",
            key_data="ss://test@server:1234#TestKey",
            external_id="outline-key-123",
        )

        key = await vpn_service.create_key(
            telegram_id=123456789,
            key_type="outline",
            key_name="Mi iPhone",
            current_user_id=123456789,
        )

        assert key is not None
        assert key.key_type == KeyType.OUTLINE
        assert key.name == "Mi iPhone"
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wireguard_key_success(self, vpn_service, mock_user_repo, mock_key_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_key_repo.save.return_value = VpnKey(
            id=str(uuid.uuid4()),
            user_id=123456789,
            key_type=KeyType.WIREGUARD,
            name="Mi Laptop",
            key_data="[Interface]\nPrivateKey = xxx",
            external_id="wg-client-123",
        )

        key = await vpn_service.create_key(
            telegram_id=123456789,
            key_type="wireguard",
            key_name="Mi Laptop",
            current_user_id=123456789,
        )

        assert key is not None
        assert key.key_type == KeyType.WIREGUARD
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_key_auto_creates_user(self, vpn_service, mock_user_repo, mock_key_repo):
        mock_user_repo.get_by_id.return_value = None
        mock_user_repo.save.return_value = User(telegram_id=123456789)
        mock_key_repo.save.return_value = VpnKey(
            id=str(uuid.uuid4()),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Test Key",
            key_data="ss://test",
            external_id="key-123",
        )

        await vpn_service.create_key(
            telegram_id=123456789,
            key_type="outline",
            key_name="Test Key",
            current_user_id=123456789,
        )

        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_key_raises_when_limit_reached(self, vpn_service, mock_user_repo, sample_user):
        sample_user.keys = [MagicMock(is_active=True), MagicMock(is_active=True)]
        mock_user_repo.get_by_id.return_value = sample_user

        with pytest.raises(ValueError, match="Límite"):
            await vpn_service.create_key(
                telegram_id=123456789,
                key_type="outline",
                key_name="Test",
                current_user_id=123456789,
            )

    @pytest.mark.asyncio
    async def test_create_key_invalid_type_raises(self, vpn_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user

        with pytest.raises(ValueError, match="no soportado"):
            await vpn_service.create_key(
                telegram_id=123456789,
                key_type="invalid",
                key_name="Test",
                current_user_id=123456789,
            )


class TestRevokeKey:
    @pytest.mark.asyncio
    async def test_revoke_key_success(self, vpn_service, mock_key_repo, mock_user_repo, sample_vpn_key, sample_user):
        mock_key_repo.get_by_id.return_value = sample_vpn_key
        mock_user_repo.get_by_id.return_value = sample_user
        sample_user.referral_credits = 100
        mock_key_repo.delete.return_value = True

        result = await vpn_service.revoke_key(sample_vpn_key.id, 123456789)

        assert result is True
        mock_key_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_key_not_found(self, vpn_service, mock_key_repo):
        mock_key_repo.get_by_id.return_value = None

        result = await vpn_service.revoke_key(str(uuid.uuid4()), 123456789)

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_key_user_cannot_delete(self, vpn_service, mock_key_repo, mock_user_repo, sample_vpn_key, sample_user):
        sample_user.referral_credits = 0
        mock_key_repo.get_by_id.return_value = sample_vpn_key
        mock_user_repo.get_by_id.return_value = sample_user

        with pytest.raises(ValueError, match="créditos"):
            await vpn_service.revoke_key(sample_vpn_key.id, 123456789)


class TestGetUserStatus:
    @pytest.mark.asyncio
    async def test_get_user_status_returns_summary(self, vpn_service, mock_user_repo, mock_key_repo, sample_user, sample_vpn_key):
        mock_user_repo.get_by_id.return_value = sample_user
        sample_vpn_key.used_bytes = 5 * 1024**3
        mock_key_repo.get_by_user_id.return_value = [sample_vpn_key]

        status = await vpn_service.get_user_status(123456789, 123456789)

        assert status["user"] == sample_user
        assert status["keys_count"] == 1
        assert status["total_used_gb"] == pytest.approx(5.0)
        mock_user_repo.get_by_id.assert_called_once()
        mock_key_repo.get_by_user_id.assert_called_once()


class TestFetchRealUsage:
    @pytest.mark.asyncio
    async def test_fetch_outline_usage(self, vpn_service, mock_outline_client, sample_vpn_key):
        sample_vpn_key.key_type = KeyType.OUTLINE
        sample_vpn_key.external_id = "outline-key-123"
        mock_outline_client.get_metrics.return_value = {"outline-key-123": 2048}

        usage = await vpn_service.fetch_real_usage(sample_vpn_key)

        assert usage == 2048

    @pytest.mark.asyncio
    async def test_fetch_wireguard_usage(self, vpn_service, mock_wireguard_client, sample_vpn_key):
        sample_vpn_key.key_type = KeyType.WIREGUARD
        sample_vpn_key.external_id = "wg-client-123"
        mock_wireguard_client.get_peer_metrics.return_value = {"transfer_total": 4096}

        usage = await vpn_service.fetch_real_usage(sample_vpn_key)

        assert usage == 4096

    @pytest.mark.asyncio
    async def test_fetch_usage_returns_zero_on_error(self, vpn_service, mock_outline_client, sample_vpn_key):
        sample_vpn_key.key_type = KeyType.OUTLINE
        mock_outline_client.get_metrics.side_effect = Exception("Connection error")

        usage = await vpn_service.fetch_real_usage(sample_vpn_key)

        assert usage == 0


class TestRenameKey:
    @pytest.mark.asyncio
    async def test_rename_key_success(self, vpn_service, mock_key_repo, sample_vpn_key):
        mock_key_repo.get_by_id.return_value = sample_vpn_key
        mock_key_repo.save.return_value = sample_vpn_key

        result = await vpn_service.rename_key(str(sample_vpn_key.id), "New Name", 123456789)

        assert result is True
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_rename_key_not_found(self, vpn_service, mock_key_repo):
        mock_key_repo.get_by_id.return_value = None

        result = await vpn_service.rename_key(str(uuid.uuid4()), "New Name", 123456789)

        assert result is False


class TestCanUserCreateKey:
    @pytest.mark.asyncio
    async def test_can_create_returns_true(self, vpn_service, mock_key_repo, sample_user):
        mock_key_repo.get_by_user_id.return_value = [MagicMock()]

        can_create, message = await vpn_service.can_user_create_key(sample_user, 123456789)

        assert can_create is True
        assert message == ""

    @pytest.mark.asyncio
    async def test_cannot_create_when_limit_reached(self, vpn_service, mock_key_repo, sample_user):
        mock_key_repo.get_by_user_id.return_value = [MagicMock(), MagicMock()]

        can_create, message = await vpn_service.can_user_create_key(sample_user, 123456789)

        assert can_create is False
        assert "límite" in message.lower()


class TestGetServerStatus:
    @pytest.mark.asyncio
    async def test_get_outline_server_status(self, vpn_service, mock_outline_client):
        mock_outline_client.get_server_info.return_value = {"is_healthy": True, "total_keys": 10}

        status = await vpn_service.get_server_status("outline")

        assert status["location"] == "Miami, USA"
        assert status["ping"] == 35

    @pytest.mark.asyncio
    async def test_get_wireguard_server_status(self, vpn_service, mock_wireguard_client):
        mock_wireguard_client.get_usage.return_value = [{"total": 1024}, {"total": 2048}]

        status = await vpn_service.get_server_status("wireguard")

        assert status["location"] == "Miami, USA"

    @pytest.mark.asyncio
    async def test_get_server_status_handles_error(self, vpn_service, mock_outline_client):
        mock_outline_client.get_server_info.side_effect = Exception("Error")

        status = await vpn_service.get_server_status("outline")

        assert status["location"] == "Miami, USA"
