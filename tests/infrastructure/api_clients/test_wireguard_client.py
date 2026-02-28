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
