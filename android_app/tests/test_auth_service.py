"""Tests for auth_service module."""

import time
from unittest.mock import MagicMock, PropertyMock, patch

import jwt
import pytest
import pytest_asyncio
from src.services.auth_service import AuthService


class TestAuthService:
    """Test authentication service operations."""

    @patch("src.services.auth_service.PreferencesStorage")
    def test_auth_service_initialization(self, mock_prefs):
        """Test AuthService initializes correctly."""
        mock_prefs.get_last_user_id.return_value = None
        service = AuthService()
        assert service.api_client is not None
        assert service._current_telegram_id is None

    @patch("src.services.auth_service.PreferencesStorage")
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

    @patch("src.services.auth_service.PreferencesStorage")
    def test_get_current_user(self, mock_prefs):
        """Test get_current_user method."""
        mock_prefs.get_last_user_id.return_value = None
        service = AuthService()

        # Initially None
        assert service.get_current_user() is None

        # After setting
        service.current_telegram_id = "789012"
        assert service.get_current_user() == "789012"

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    @pytest.mark.asyncio
    async def test_is_authenticated_no_token(self, mock_secure, mock_prefs):
        """Test is_authenticated returns False when no token."""
        mock_prefs.get_last_user_id.return_value = None

        service = AuthService()
        result = await service.is_authenticated()
        assert result is False


class TestJwtExpiryValidation:
    """Test JWT expiry validation functionality."""

    def _create_test_jwt(self, exp_offset: int) -> str:
        """Helper to create test JWT tokens."""
        payload = {
            "sub": "test_user_123",
            "client": "android_apk",
            "exp": int(time.time()) + exp_offset,
            "jti": "test-jwt-id-123",
        }
        # Create unsigned token for testing
        return jwt.encode(payload, key="", algorithm="none")

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    def test_validate_jwt_expiry_valid_token(self, mock_secure, mock_prefs):
        """Test validation of non-expired JWT."""
        mock_prefs.get_last_user_id.return_value = "test_user_123"
        valid_token = self._create_test_jwt(exp_offset=3600)  # Expires in 1 hour
        mock_secure.get_jwt.return_value = valid_token

        service = AuthService()
        is_valid, error_msg = service._validate_jwt_expiry(valid_token)

        assert is_valid is True
        assert error_msg is None

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    def test_validate_jwt_expiry_expired_token(self, mock_secure, mock_prefs):
        """Test validation of expired JWT."""
        mock_prefs.get_last_user_id.return_value = "test_user_123"
        expired_token = self._create_test_jwt(exp_offset=-3600)  # Expired 1 hour ago
        mock_secure.get_jwt.return_value = expired_token

        service = AuthService()
        is_valid, error_msg = service._validate_jwt_expiry(expired_token)

        assert is_valid is False
        assert error_msg == "JWT expirado o próximo a expirar"

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    def test_validate_jwt_expiry_no_exp_field(self, mock_secure, mock_prefs):
        """Test validation of JWT without exp field."""
        mock_prefs.get_last_user_id.return_value = "test_user_123"
        # Create token without exp
        payload = {"sub": "test_user_123", "client": "android_apk", "jti": "test-jwt-id-123"}
        no_exp_token = jwt.encode(payload, key="", algorithm="none")
        mock_secure.get_jwt.return_value = no_exp_token

        service = AuthService()
        is_valid, error_msg = service._validate_jwt_expiry(no_exp_token)

        assert is_valid is False
        assert error_msg == "JWT sin expiración"

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    @pytest.mark.asyncio
    async def test_is_authenticated_with_valid_jwt(self, mock_secure, mock_prefs):
        """Test is_authenticated returns True with valid JWT."""
        mock_prefs.get_last_user_id.return_value = "test_user_123"
        valid_token = self._create_test_jwt(exp_offset=3600)
        mock_secure.get_jwt.return_value = valid_token

        service = AuthService()
        result = await service.is_authenticated()

        assert result is True

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    @pytest.mark.asyncio
    async def test_is_authenticated_with_expired_jwt(self, mock_secure, mock_prefs):
        """Test is_authenticated returns False with expired JWT."""
        mock_prefs.get_last_user_id.return_value = "test_user_123"
        expired_token = self._create_test_jwt(exp_offset=-3600)
        mock_secure.get_jwt.return_value = expired_token

        service = AuthService()
        result = await service.is_authenticated()

        assert result is False

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    def test_get_jwt_expiry_info(self, mock_secure, mock_prefs):
        """Test getting JWT expiry information."""
        mock_prefs.get_last_user_id.return_value = "test_user_123"
        expires_in = 3600  # 1 hour
        valid_token = self._create_test_jwt(exp_offset=expires_in)
        mock_secure.get_jwt.return_value = valid_token

        service = AuthService()
        expires_at, time_remaining = service.get_jwt_expiry_info()

        assert expires_at is not None
        assert time_remaining is not None
        assert time_remaining > 3500  # Should be close to 3600 (within 100s tolerance)
        assert time_remaining <= expires_in

    @patch("src.services.auth_service.PreferencesStorage")
    @patch("src.services.auth_service.SecureStorage")
    def test_get_jwt_expiry_info_no_token(self, mock_secure, mock_prefs):
        """Test getting expiry info when no token exists."""
        mock_prefs.get_last_user_id.return_value = None
        mock_secure.get_jwt.return_value = None

        service = AuthService()
        expires_at, time_remaining = service.get_jwt_expiry_info()

        assert expires_at is None
        assert time_remaining is None
