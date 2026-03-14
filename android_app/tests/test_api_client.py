"""Tests for api_client module."""
import pytest
import pytest_asyncio
from src.services.api_client import ApiClient


class TestApiClient:
    """Test API client operations."""

    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """Test API client initializes correctly."""
        client = ApiClient(telegram_id="123456")
        assert client.base_url is not None
        assert client.telegram_id == "123456"
        assert client.timeout == 30
