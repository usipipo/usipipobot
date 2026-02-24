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
    
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, return_value=mock_output):
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
    mock_output = "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\t200\toff"
    
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, return_value=mock_output) as mock_cmd:
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
    mock_output1 = "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\t200\toff"
    mock_output2 = "private\tkey\tport\t0\npubkey2\tkey\tendpoint\tallowed\t0\t300\t400\toff"
    
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, side_effect=[mock_output1, mock_output2]) as mock_cmd:
        # First call
        result1 = await wireguard_client.get_usage()
        
        # Simulate cache expiration by setting cache time to past
        wireguard_client._usage_cache = (wireguard_client._usage_cache[0], datetime.now() - timedelta(seconds=15))
        
        # Second call after cache expired
        result2 = await wireguard_client.get_usage()
        
        # Should call _run_cmd twice due to cache expiration
        assert mock_cmd.call_count == 2
        assert result1 != result2


@pytest.mark.asyncio
async def test_get_usage_captures_error_message(wireguard_client):
    """Test that get_usage logs actual error messages."""
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, side_effect=Exception("Detailed error message")):
        with patch('infrastructure.api_clients.client_wireguard.logger') as mock_logger:
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
    
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, side_effect=EmptyException()):
        with patch('infrastructure.api_clients.client_wireguard.logger') as mock_logger:
            result = await wireguard_client.get_usage()
            
            assert result == []
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            # Should contain repr or fallback message
            assert "Error obteniendo métricas WG:" in call_args


@pytest.mark.asyncio
async def test_get_usage_handles_command_failure(wireguard_client):
    """Test that get_usage handles command execution failures."""
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, side_effect=Exception("Command failed")):
        result = await wireguard_client.get_usage()
        
        assert result == []


@pytest.mark.asyncio
async def test_get_usage_skips_invalid_lines(wireguard_client):
    """Test that get_usage skips lines with insufficient columns."""
    mock_output = "private\tkey\tport\t0\npubkey1\tkey\tendpoint\tallowed\t0\t100\npubkey2\tkey\tendpoint\tallowed\t0\t300\t400\toff"
    
    with patch.object(wireguard_client, '_run_cmd', new_callable=AsyncMock, return_value=mock_output):
        result = await wireguard_client.get_usage()
        
        # Should only parse line with 7+ columns
        assert len(result) == 1
        assert result[0]["public_key"] == "pubkey2"
