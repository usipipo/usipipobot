"""Tests for VpnInfrastructureService."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.services.vpn_infrastructure_service import VpnInfrastructureService
from config import settings
from domain.entities.vpn_key import KeyType, VpnKey


@pytest.fixture
def vpn_infra_service(
    mock_key_repo, mock_user_repo, mock_outline_client, mock_wireguard_client
):
    return VpnInfrastructureService(
        key_repository=mock_key_repo,
        user_repository=mock_user_repo,
        wireguard_client=mock_wireguard_client,
        outline_client=mock_outline_client,
    )


@pytest.fixture
def sample_wireguard_key():
    return VpnKey(
        id=str(uuid.uuid4()),
        user_id=123456789,
        key_type=KeyType.WIREGUARD,
        name="Test WG Key",
        key_data="[Interface]\nPrivateKey = xxx",
        external_id="wg-client-123",
        is_active=True,
        used_bytes=1024,
        last_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
    )


@pytest.fixture
def sample_outline_key():
    return VpnKey(
        id=str(uuid.uuid4()),
        user_id=123456789,
        key_type=KeyType.OUTLINE,
        name="Test Outline Key",
        key_data="ss://test@server:1234#TestKey",
        external_id="outline-key-123",
        is_active=True,
        used_bytes=2048,
        last_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
    )


class TestEnableKey:
    @pytest.mark.asyncio
    async def test_enable_key_wireguard_success(
        self,
        vpn_infra_service,
        mock_key_repo,
        mock_wireguard_client,
        sample_wireguard_key,
    ):
        mock_key_repo.get_by_id.return_value = sample_wireguard_key
        mock_wireguard_client.enable_peer.return_value = True
        mock_key_repo.save.return_value = sample_wireguard_key

        result = await vpn_infra_service.enable_key(
            key_id=str(sample_wireguard_key.id), key_type="wireguard"
        )

        assert result["success"] is True
        assert result["error"] is None
        mock_wireguard_client.enable_peer.assert_called_once_with("wg-client-123")
        mock_key_repo.save.assert_called_once()
        assert sample_wireguard_key.is_active is True

    @pytest.mark.asyncio
    async def test_enable_key_outline_success(
        self, vpn_infra_service, mock_key_repo, mock_outline_client, sample_outline_key
    ):
        mock_key_repo.get_by_id.return_value = sample_outline_key
        mock_outline_client.enable_key.return_value = True
        mock_key_repo.save.return_value = sample_outline_key

        result = await vpn_infra_service.enable_key(
            key_id=str(sample_outline_key.id), key_type="outline"
        )

        assert result["success"] is True
        assert result["error"] is None
        mock_outline_client.enable_key.assert_called_once_with("outline-key-123")
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_key_not_found(self, vpn_infra_service, mock_key_repo):
        mock_key_repo.get_by_id.return_value = None

        result = await vpn_infra_service.enable_key(
            key_id=str(uuid.uuid4()), key_type="wireguard"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_enable_key_server_failure(
        self,
        vpn_infra_service,
        mock_key_repo,
        mock_wireguard_client,
        sample_wireguard_key,
    ):
        mock_key_repo.get_by_id.return_value = sample_wireguard_key
        mock_wireguard_client.enable_peer.return_value = False

        result = await vpn_infra_service.enable_key(
            key_id=str(sample_wireguard_key.id), key_type="wireguard"
        )

        assert result["success"] is False
        assert result["error"] is not None


class TestDisableKey:
    @pytest.mark.asyncio
    async def test_disable_key_wireguard(
        self,
        vpn_infra_service,
        mock_key_repo,
        mock_wireguard_client,
        sample_wireguard_key,
    ):
        mock_key_repo.get_by_id.return_value = sample_wireguard_key
        mock_wireguard_client.disable_peer.return_value = True
        mock_key_repo.save.return_value = sample_wireguard_key

        result = await vpn_infra_service.disable_key(
            key_id=str(sample_wireguard_key.id), key_type="wireguard"
        )

        assert result["success"] is True
        assert result["error"] is None
        mock_wireguard_client.disable_peer.assert_called_once_with("wg-client-123")
        mock_key_repo.save.assert_called_once()
        assert sample_wireguard_key.is_active is False

    @pytest.mark.asyncio
    async def test_disable_key_outline(
        self, vpn_infra_service, mock_key_repo, mock_outline_client, sample_outline_key
    ):
        mock_key_repo.get_by_id.return_value = sample_outline_key
        mock_outline_client.disable_key.return_value = True
        mock_key_repo.save.return_value = sample_outline_key

        result = await vpn_infra_service.disable_key(
            key_id=str(sample_outline_key.id), key_type="outline"
        )

        assert result["success"] is True
        assert result["error"] is None
        mock_outline_client.disable_key.assert_called_once_with("outline-key-123")
        mock_key_repo.save.assert_called_once()
        assert sample_outline_key.is_active is False


class TestDeleteKeyComplete:
    @pytest.mark.asyncio
    async def test_delete_key_complete_success(
        self,
        vpn_infra_service,
        mock_key_repo,
        mock_wireguard_client,
        sample_wireguard_key,
    ):
        mock_key_repo.get_by_id.return_value = sample_wireguard_key
        mock_wireguard_client.delete_client.return_value = True
        mock_key_repo.delete.return_value = True

        result = await vpn_infra_service.delete_key_complete(
            key_id=str(sample_wireguard_key.id), key_type="wireguard"
        )

        assert result["success"] is True
        assert result["server_deleted"] is True
        assert result["db_deleted"] is True
        assert result["error"] is None
        mock_wireguard_client.delete_client.assert_called_once_with("wg-client-123")
        mock_key_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_key_complete_partial_failure(
        self,
        vpn_infra_service,
        mock_key_repo,
        mock_wireguard_client,
        sample_wireguard_key,
    ):
        mock_key_repo.get_by_id.return_value = sample_wireguard_key
        mock_wireguard_client.delete_client.return_value = False
        mock_key_repo.delete.return_value = True

        result = await vpn_infra_service.delete_key_complete(
            key_id=str(sample_wireguard_key.id), key_type="wireguard"
        )

        assert result["success"] is False
        assert result["server_deleted"] is False
        assert result["db_deleted"] is True
        assert result["error"] is not None


class TestGetServerMetrics:
    @pytest.mark.asyncio
    async def test_get_server_metrics(
        self, vpn_infra_service, mock_key_repo, mock_outline_client
    ):
        mock_outline_client.get_server_info.return_value = {
            "is_healthy": True,
            "total_keys": 10,
            "name": "Test Server",
        }
        mock_key_repo.get_all_keys.return_value = [
            MagicMock(key_type=KeyType.OUTLINE, is_active=True),
            MagicMock(key_type=KeyType.OUTLINE, is_active=False),
        ]

        result = await vpn_infra_service.get_server_metrics(server_type="outline")

        assert result["is_healthy"] is True
        assert result["total_keys"] == 2
        assert result["active_keys"] == 1
        assert result["server_type"] == "outline"


class TestCleanupGhostKeys:
    @pytest.mark.asyncio
    async def test_cleanup_ghost_keys(
        self, vpn_infra_service, mock_key_repo, mock_outline_client, sample_outline_key
    ):
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        sample_outline_key.last_seen_at = old_date
        sample_outline_key.is_active = True

        mock_key_repo.get_all_active.return_value = [sample_outline_key]
        mock_outline_client.disable_key.return_value = True
        mock_key_repo.save.return_value = sample_outline_key

        result = await vpn_infra_service.cleanup_ghost_keys(days_inactive=90)

        assert result["total_checked"] == 1
        assert result["ghosts_found"] == 1
        assert result["disabled_count"] == 1
        assert len(result["errors"]) == 0
        mock_outline_client.disable_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_ghost_keys_no_ghosts(
        self, vpn_infra_service, mock_key_repo, sample_outline_key
    ):
        recent_date = datetime.now(timezone.utc) - timedelta(days=30)
        sample_outline_key.last_seen_at = recent_date
        sample_outline_key.is_active = True

        mock_key_repo.get_all_active.return_value = [sample_outline_key]

        result = await vpn_infra_service.cleanup_ghost_keys(days_inactive=90)

        assert result["total_checked"] == 1
        assert result["ghosts_found"] == 0
        assert result["disabled_count"] == 0


class TestListServerKeys:
    @pytest.mark.asyncio
    async def test_list_server_keys(
        self, vpn_infra_service, mock_key_repo, sample_outline_key
    ):
        mock_key_repo.get_all_keys.return_value = [sample_outline_key]

        result = await vpn_infra_service.list_server_keys(server_type="outline")

        assert len(result) == 1
        assert result[0]["id"] == str(sample_outline_key.id)
        assert result[0]["name"] == "Test Outline Key"
        assert result[0]["is_active"] is True
        assert result[0]["key_type"] == "outline"

    @pytest.mark.asyncio
    async def test_list_server_keys_filters_inactive_keys(
        self, vpn_infra_service, mock_key_repo, sample_outline_key
    ):
        """Test that inactive (soft-deleted) keys are not shown in admin list."""
        inactive_key = VpnKey(
            id=str(uuid.uuid4()),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Deleted Outline Key",
            key_data="ss://test@server:1234#DeletedKey",
            external_id="outline-key-deleted",
            is_active=False,  # Soft deleted
            used_bytes=1024,
            last_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        mock_key_repo.get_all_keys.return_value = [sample_outline_key, inactive_key]

        result = await vpn_infra_service.list_server_keys(server_type="outline")

        assert len(result) == 1
        assert result[0]["id"] == str(sample_outline_key.id)
        assert result[0]["is_active"] is True
        # Verify inactive key is not in results
        inactive_ids = [k["id"] for k in result if not k["is_active"]]
        assert len(inactive_ids) == 0


class TestIsGhostKey:
    def test_is_ghost_key_true(self, vpn_infra_service):
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        key = MagicMock(
            last_seen_at=old_date,
            is_active=True,
        )
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

        result = vpn_infra_service._is_ghost_key(key, cutoff_date)

        assert result is True

    def test_is_ghost_key_false_recent(self, vpn_infra_service):
        recent_date = datetime.now(timezone.utc) - timedelta(days=30)
        key = MagicMock(
            last_seen_at=recent_date,
            is_active=True,
        )
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

        result = vpn_infra_service._is_ghost_key(key, cutoff_date)

        assert result is False

    def test_is_ghost_key_false_inactive(self, vpn_infra_service):
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        key = MagicMock(
            last_seen_at=old_date,
            is_active=False,
        )
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

        result = vpn_infra_service._is_ghost_key(key, cutoff_date)

        assert result is False

    def test_is_ghost_key_no_last_seen(self, vpn_infra_service):
        key = MagicMock(
            last_seen_at=None,
            is_active=True,
        )
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

        result = vpn_infra_service._is_ghost_key(key, cutoff_date)

        assert result is False
