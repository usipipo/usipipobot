"""Tests for auth_service module."""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from src.services.auth_service import AuthService


class TestAuthService:
    """Test authentication service operations."""

    @patch('src.services.auth_service.PreferencesStorage')
    def test_auth_service_initialization(self, mock_prefs):
        """Test AuthService initializes correctly."""
        mock_prefs.get_last_user_id.return_value = None
        service = AuthService()
        assert service.api_client is not None
        assert service._current_telegram_id is None

    @patch('src.services.auth_service.PreferencesStorage')
    def test_current_telegram_id_property(self, mock_prefs):
        """Test telegram_id property getter/setter."""
        mock_prefs.get_last_user_id.return_value = None
        service = AuthService()
        
        # Initially should be None
        assert service.current_telegram_id is None
        
        # Set value
        service.current_telegram_id = "123456"
        
        # Should return set value
        assert service.current_telegram_id == "123456"
        assert service._current_telegram_id == "123456"

    @patch('src.services.auth_service.PreferencesStorage')
    def test_get_current_user(self, mock_prefs):
        """Test get_current_user method."""
        mock_prefs.get_last_user_id.return_value = None
        service = AuthService()
        
        # Initially None
        assert service.get_current_user() is None
        
        # After setting
        service.current_telegram_id = "789012"
        assert service.get_current_user() == "789012"

    @patch('src.services.auth_service.PreferencesStorage')
    @patch('src.services.auth_service.SecureStorage')
    @pytest.mark.asyncio
    async def test_is_authenticated_no_token(self, mock_secure, mock_prefs):
        """Test is_authenticated returns False when no token."""
        mock_prefs.get_last_user_id.return_value = None
        
        service = AuthService()
        result = await service.is_authenticated()
        assert result is False
