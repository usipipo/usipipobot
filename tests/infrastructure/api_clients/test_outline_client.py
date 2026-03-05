from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.api_clients.client_outline import OutlineClient


class TestDisableKey:
    @pytest.fixture
    def client(self):
        with patch.object(OutlineClient, "__init__", lambda x: None):
            outline_client = OutlineClient.__new__(OutlineClient)
            outline_client.api_url = "https://example.com/api"
            outline_client.brand = "uSipipo VPN"
            outline_client.client = MagicMock()
            return outline_client

    @pytest.mark.asyncio
    async def test_disable_key_success(self, client):
        """Test disable_key returns True on 204 status code"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        client.client.put = AsyncMock(return_value=mock_response)

        result = await client.disable_key("test-key-id")

        assert result is True
        client.client.put.assert_called_once_with(
            "https://example.com/api/access-keys/test-key-id/data-limit",
            json={"limit": {"bytes": 1}},
        )

    @pytest.mark.asyncio
    async def test_disable_key_failure(self, client):
        """Test disable_key returns False on error"""
        client.client.put = AsyncMock(side_effect=Exception("Connection error"))

        result = await client.disable_key("test-key-id")

        assert result is False


class TestEnableKey:
    @pytest.fixture
    def client(self):
        with patch.object(OutlineClient, "__init__", lambda x: None):
            outline_client = OutlineClient.__new__(OutlineClient)
            outline_client.api_url = "https://example.com/api"
            outline_client.brand = "uSipipo VPN"
            outline_client.client = MagicMock()
            return outline_client

    @pytest.mark.asyncio
    async def test_enable_key_success(self, client):
        """Test enable_key returns True on 204 status code"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        client.client.delete = AsyncMock(return_value=mock_response)

        result = await client.enable_key("test-key-id")

        assert result is True
        client.client.delete.assert_called_once_with(
            "https://example.com/api/access-keys/test-key-id/data-limit"
        )

    @pytest.mark.asyncio
    async def test_enable_key_failure(self, client):
        """Test enable_key returns False on error"""
        client.client.delete = AsyncMock(side_effect=Exception("Connection error"))

        result = await client.enable_key("test-key-id")

        assert result is False
