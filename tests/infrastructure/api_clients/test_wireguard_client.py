"""Tests for WireGuard client."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.api_clients.client_wireguard import WireGuardClient


@pytest.fixture
def wireguard_client():
    """Create WireGuard client for testing."""
    client = WireGuardClient()
    client.interface = "wg0"
    return client


@pytest.mark.asyncio
async def test_get_usage_returns_list(wireguard_client):
    """Test that get_usage returns a list of peer metrics."""
    mock_output = "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\t200\toff\npubkey2\tkey\tendpoint\tallowed\t0\t300\t400\toff"

    with patch.object(
        wireguard_client, "_run_cmd", new_callable=AsyncMock, return_value=mock_output
    ):
        result = await wireguard_client.get_usage()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["public_key"] == "pubkey1"
        assert result[0]["rx"] == 100
        assert result[0]["tx"] == 200
        assert result[0]["total"] == 300


@pytest.mark.asyncio
async def test_get_usage_caches_results(wireguard_client):
    """Test that get_usage caches results to prevent race conditions."""
    mock_output = (
        "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\t200\toff"
    )

    with patch.object(
        wireguard_client, "_run_cmd", new_callable=AsyncMock, return_value=mock_output
    ) as mock_cmd:
        # First call
        result1 = await wireguard_client.get_usage()
        # Second call within cache TTL
        result2 = await wireguard_client.get_usage()

        # Should only call _run_cmd once due to caching
        assert mock_cmd.call_count == 1
        assert result1 == result2


@pytest.mark.asyncio
async def test_get_usage_cache_expires(wireguard_client):
    """Test that cache expires after TTL."""
    mock_output1 = (
        "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\t200\toff"
    )
    mock_output2 = (
        "private\tkey\tport\t0\npubkey2\tkey\tendpoint\tallowed\t0\t300\t400\toff"
    )

    with patch.object(
        wireguard_client,
        "_run_cmd",
        new_callable=AsyncMock,
        side_effect=[mock_output1, mock_output2],
    ) as mock_cmd:
        # First call
        result1 = await wireguard_client.get_usage()

        # Simulate cache expiration by setting cache time to past
        wireguard_client._usage_cache = (
            wireguard_client._usage_cache[0],
            datetime.now() - timedelta(seconds=15),
        )

        # Second call after cache expired
        result2 = await wireguard_client.get_usage()

        # Should call _run_cmd twice due to cache expiration
        assert mock_cmd.call_count == 2
        assert result1 != result2


@pytest.mark.asyncio
async def test_get_usage_captures_error_message(wireguard_client):
    """Test that get_usage logs actual error messages."""
    with patch.object(
        wireguard_client,
        "_run_cmd",
        new_callable=AsyncMock,
        side_effect=Exception("Detailed error message"),
    ):
        with patch("infrastructure.api_clients.client_wireguard.logger") as mock_logger:
            result = await wireguard_client.get_usage()

            assert result == []
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Detailed error message" in call_args


@pytest.mark.asyncio
async def test_get_usage_handles_empty_exception(wireguard_client):
    """Test that get_usage handles exceptions with empty messages."""

    class EmptyException(Exception):
        def __str__(self):
            return ""

    with patch.object(
        wireguard_client,
        "_run_cmd",
        new_callable=AsyncMock,
        side_effect=EmptyException(),
    ):
        with patch("infrastructure.api_clients.client_wireguard.logger") as mock_logger:
            result = await wireguard_client.get_usage()

            assert result == []
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            # Should contain repr or fallback message
            assert "Error obteniendo métricas WG:" in call_args


@pytest.mark.asyncio
async def test_get_usage_handles_command_failure(wireguard_client):
    """Test that get_usage handles command execution failures."""
    with patch.object(
        wireguard_client,
        "_run_cmd",
        new_callable=AsyncMock,
        side_effect=Exception("Command failed"),
    ):
        result = await wireguard_client.get_usage()

        assert result == []


@pytest.mark.asyncio
async def test_get_usage_skips_invalid_lines(wireguard_client):
    """Test that get_usage skips lines with insufficient columns."""
    mock_output = "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\npubkey2\tkey\tendpoint\tallowed\t0\t300\t400\toff"

    with patch.object(
        wireguard_client, "_run_cmd", new_callable=AsyncMock, return_value=mock_output
    ):
        result = await wireguard_client.get_usage()

        # Should only parse line with 7+ columns
        assert len(result) == 1
        assert result[0]["public_key"] == "pubkey2"


class TestDisablePeer:
    """Tests for disable_peer method."""

    @pytest.fixture
    def wireguard_client(self):
        """Create WireGuard client for testing."""
        client = WireGuardClient()
        client.interface = "wg0"
        client.conf_path = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_disable_peer_success(self, wireguard_client):
        """Test successful peer disable - peer found and disabled."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24
ListenPort = 51820

### CLIENT tg_123_abc123
[Peer]
PublicKey = test_pub_key_123
PresharedKey = test_psk
AllowedIPs = 10.0.0.2/32

### CLIENT tg_456_def456
[Peer]
PublicKey = other_pub_key
PresharedKey = other_psk
AllowedIPs = 10.0.0.3/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ) as mock_run_cmd:
            result = await wireguard_client.disable_peer("tg_123_abc123")

            assert result is True
            mock_run_cmd.assert_called_once_with(
                "wg set wg0 peer test_pub_key_123 allowed-ips 0.0.0.0/32"
            )
            wireguard_client.conf_path.write_text.assert_called_once()

            # Verify the config was updated with [DISABLED] marker
            written_content = wireguard_client.conf_path.write_text.call_args[0][0]
            assert "[DISABLED]" in written_content
            assert "### CLIENT tg_123_abc123" in written_content

    @pytest.mark.asyncio
    async def test_disable_peer_not_found(self, wireguard_client):
        """Test disable returns False when peer not found."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24

### CLIENT tg_999_other
[Peer]
PublicKey = other_pub_key
AllowedIPs = 10.0.0.5/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch("infrastructure.api_clients.client_wireguard.logger") as mock_logger:
            result = await wireguard_client.disable_peer("tg_123_notfound")

            assert result is False
            mock_logger.error.assert_called_once()
            error_msg = mock_logger.error.call_args[0][0]
            assert "tg_123_notfound" in error_msg

    @pytest.mark.asyncio
    async def test_disable_peer_config_not_found(self, wireguard_client):
        """Test disable returns False when config file doesn't exist."""
        wireguard_client.conf_path.exists.return_value = False

        with patch("infrastructure.api_clients.client_wireguard.logger") as mock_logger:
            result = await wireguard_client.disable_peer("tg_123_abc")

            assert result is False
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_peer_wg_command_fails(self, wireguard_client):
        """Test disable returns False when wg command fails."""
        config_content = """### CLIENT tg_123_abc
[Peer]
PublicKey = test_pub_key
AllowedIPs = 10.0.0.2/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client,
            "_run_cmd",
            new_callable=AsyncMock,
            side_effect=Exception("wg command failed"),
        ):
            with patch(
                "infrastructure.api_clients.client_wireguard.logger"
            ) as mock_logger:
                result = await wireguard_client.disable_peer("tg_123_abc")

                assert result is False
                mock_logger.error.assert_called_once()


class TestEnablePeer:
    """Tests for enable_peer method."""

    @pytest.fixture
    def wireguard_client(self):
        """Create WireGuard client for testing."""
        client = WireGuardClient()
        client.interface = "wg0"
        client.conf_path = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_enable_peer_success(self, wireguard_client):
        """Test successful peer enable - peer found with [DISABLED] marker."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24
ListenPort = 51820

### CLIENT tg_123_abc123 [DISABLED]
[Peer]
PublicKey = test_pub_key_123
PresharedKey = test_psk
AllowedIPs = 10.0.0.2/32

### CLIENT tg_456_def456
[Peer]
PublicKey = other_pub_key
PresharedKey = other_psk
AllowedIPs = 10.0.0.3/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ) as mock_run_cmd:
            result = await wireguard_client.enable_peer("tg_123_abc123")

            assert result is True
            mock_run_cmd.assert_called_once_with(
                "wg set wg0 peer test_pub_key_123 allowed-ips 10.0.0.2/32"
            )
            wireguard_client.conf_path.write_text.assert_called_once()

            # Verify the [DISABLED] marker was removed
            written_content = wireguard_client.conf_path.write_text.call_args[0][0]
            assert "[DISABLED]" not in written_content
            assert "### CLIENT tg_123_abc123" in written_content

    @pytest.mark.asyncio
    async def test_enable_peer_not_disabled(self, wireguard_client):
        """Test enable works on peer that wasn't disabled (no [DISABLED] marker)."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24

### CLIENT tg_123_abc123
[Peer]
PublicKey = test_pub_key_123
PresharedKey = test_psk
AllowedIPs = 10.0.0.2/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ) as mock_run_cmd:
            result = await wireguard_client.enable_peer("tg_123_abc123")

            assert result is True
            mock_run_cmd.assert_called_once_with(
                "wg set wg0 peer test_pub_key_123 allowed-ips 10.0.0.2/32"
            )
            wireguard_client.conf_path.write_text.assert_called_once()

            # Content should remain unchanged (no [DISABLED] to remove)
            written_content = wireguard_client.conf_path.write_text.call_args[0][0]
            assert "### CLIENT tg_123_abc123" in written_content

    @pytest.mark.asyncio
    async def test_enable_peer_not_found(self, wireguard_client):
        """Test enable returns False when peer not found."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24

### CLIENT tg_999_other
[Peer]
PublicKey = other_pub_key
AllowedIPs = 10.0.0.5/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch("infrastructure.api_clients.client_wireguard.logger") as mock_logger:
            result = await wireguard_client.enable_peer("tg_123_notfound")

            assert result is False
            mock_logger.error.assert_called_once()
            error_msg = mock_logger.error.call_args[0][0]
            assert "tg_123_notfound" in error_msg

    @pytest.mark.asyncio
    async def test_enable_peer_config_not_found(self, wireguard_client):
        """Test enable returns False when config file doesn't exist."""
        wireguard_client.conf_path.exists.return_value = False

        with patch("infrastructure.api_clients.client_wireguard.logger") as mock_logger:
            result = await wireguard_client.enable_peer("tg_123_abc")

            assert result is False
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_peer_wg_command_fails(self, wireguard_client):
        """Test enable returns False when wg command fails."""
        config_content = """### CLIENT tg_123_abc [DISABLED]
[Peer]
PublicKey = test_pub_key
AllowedIPs = 10.0.0.2/32
"""

        wireguard_client.conf_path.exists.return_value = True
        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client,
            "_run_cmd",
            new_callable=AsyncMock,
            side_effect=Exception("wg command failed"),
        ):
            with patch(
                "infrastructure.api_clients.client_wireguard.logger"
            ) as mock_logger:
                result = await wireguard_client.enable_peer("tg_123_abc")

                assert result is False
                mock_logger.error.assert_called_once()


class TestDeletePeerComplete:
    """Tests for delete_peer method - verifying IP release behavior."""

    @pytest.fixture
    def wireguard_client(self):
        """Create WireGuard client for testing."""
        client = WireGuardClient()
        client.interface = "wg0"
        client.conf_path = MagicMock()
        client.clients_dir = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_delete_peer_releases_ip(self, wireguard_client):
        """Test that deleted peer's IP becomes reusable via get_next_available_ip."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24
ListenPort = 51820

### CLIENT tg_123_abc123
[Peer]
PublicKey = test_pub_key_123
PresharedKey = test_psk
AllowedIPs = 10.0.0.2/32

### CLIENT tg_456_def456
[Peer]
PublicKey = other_pub_key
PresharedKey = other_psk
AllowedIPs = 10.0.0.3/32
"""

        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ) as mock_run_cmd:
            result = await wireguard_client.delete_peer(
                pub_key="test_pub_key_123", client_name="tg_123_abc123"
            )

            assert result is True
            mock_run_cmd.assert_called_once_with(
                "wg set wg0 peer test_pub_key_123 remove"
            )

        # Verify config was updated to remove the peer block
        written_content = wireguard_client.conf_path.write_text.call_args[0][0]
        assert "tg_123_abc123" not in written_content
        assert "10.0.0.2/32" not in written_content
        assert "tg_456_def456" in written_content
        assert "10.0.0.3/32" in written_content

        # Verify the IP 10.0.0.2 is now available
        # (simulating what get_next_available_ip would find)
        wireguard_client.conf_path.read_text.return_value = written_content
        next_ip = await wireguard_client.get_next_available_ip()
        assert next_ip == "10.0.0.2"

    @pytest.mark.asyncio
    async def test_delete_peer_removes_from_config(self, wireguard_client):
        """Test that delete_peer completely removes peer from wg0.conf."""
        config_content = """[Interface]
PrivateKey = server_priv_key
Address = 10.0.0.1/24
ListenPort = 51820

### CLIENT tg_delete_me
[Peer]
PublicKey = delete_pub_key
PresharedKey = delete_psk
AllowedIPs = 10.0.0.5/32

### CLIENT tg_keep_me
[Peer]
PublicKey = keep_pub_key
PresharedKey = keep_psk
AllowedIPs = 10.0.0.6/32
"""

        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ):
            result = await wireguard_client.delete_peer(
                pub_key="delete_pub_key", client_name="tg_delete_me"
            )

            assert result is True

        # Verify write_text was called with content that excludes deleted peer
        written_content = wireguard_client.conf_path.write_text.call_args[0][0]
        assert "tg_delete_me" not in written_content
        assert "delete_pub_key" not in written_content
        assert "10.0.0.5/32" not in written_content
        # Verify other peer is preserved
        assert "tg_keep_me" in written_content
        assert "keep_pub_key" in written_content
        assert "10.0.0.6/32" in written_content

    @pytest.mark.asyncio
    async def test_delete_peer_deletes_client_file(self, wireguard_client):
        """Test that delete_peer removes the client config file."""
        config_content = """[Interface]
Address = 10.0.0.1/24

### CLIENT tg_789_xyz789
[Peer]
PublicKey = pub_key_789
AllowedIPs = 10.0.0.7/32
"""

        wireguard_client.conf_path.read_text.return_value = config_content

        # Mock the client file
        mock_client_file = MagicMock()
        mock_client_file.exists.return_value = True
        wireguard_client.clients_dir.__truediv__.return_value = mock_client_file

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ):
            result = await wireguard_client.delete_peer(
                pub_key="pub_key_789", client_name="tg_789_xyz789"
            )

            assert result is True

        # Verify client file was checked and deleted
        wireguard_client.clients_dir.__truediv__.assert_called_once_with(
            "wg0-tg_789_xyz789.conf"
        )
        mock_client_file.exists.assert_called_once()
        mock_client_file.unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_peer_file_not_exist(self, wireguard_client):
        """Test delete_peer succeeds even if client file doesn't exist."""
        config_content = """[Interface]
Address = 10.0.0.1/24

### CLIENT tg_abc_def
[Peer]
PublicKey = pub_key_abc
AllowedIPs = 10.0.0.8/32
"""

        wireguard_client.conf_path.read_text.return_value = config_content

        # Mock client file that doesn't exist
        mock_client_file = MagicMock()
        mock_client_file.exists.return_value = False
        wireguard_client.clients_dir.__truediv__.return_value = mock_client_file

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ):
            result = await wireguard_client.delete_peer(
                pub_key="pub_key_abc", client_name="tg_abc_def"
            )

            assert result is True

        # Verify exists was checked but unlink was not called
        mock_client_file.exists.assert_called_once()
        mock_client_file.unlink.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_peer_fallback_pub_key(self, wireguard_client):
        """Test delete_peer uses provided pub_key when not found in config."""
        config_content = """[Interface]
Address = 10.0.0.1/24

### CLIENT tg_other
[Peer]
PublicKey = other_key
AllowedIPs = 10.0.0.9/32
"""

        wireguard_client.conf_path.read_text.return_value = config_content

        with patch.object(
            wireguard_client, "_run_cmd", new_callable=AsyncMock
        ) as mock_run_cmd:
            # Trying to delete a client not in config, but with explicit pub_key
            result = await wireguard_client.delete_peer(
                pub_key="fallback_pub_key", client_name="tg_not_in_config"
            )

            assert result is True
            # Should use the provided pub_key for wg command
            mock_run_cmd.assert_called_once_with(
                "wg set wg0 peer fallback_pub_key remove"
            )

    @pytest.mark.asyncio
    async def test_delete_peer_handles_exception(self, wireguard_client):
        """Test delete_peer returns False on exception."""
        wireguard_client.conf_path.read_text.side_effect = Exception("IO error")

        with patch(
            "infrastructure.api_clients.client_wireguard.logger"
        ) as mock_logger:
            result = await wireguard_client.delete_peer(
                pub_key="any_key", client_name="tg_any"
            )

            assert result is False
            mock_logger.error.assert_called_once()
            error_msg = mock_logger.error.call_args[0][0]
            assert "tg_any" in error_msg
