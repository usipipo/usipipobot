"""Tests for secure_storage module."""
import pytest
from unittest.mock import patch, MagicMock
from src.storage.secure_storage import SecureStorage


class TestSecureStorage:
    """Test secure storage operations."""

    @patch('src.storage.secure_storage.keyring')
    def test_save_and_get_jwt(self, mock_keyring):
        """Test saving and retrieving JWT."""
        telegram_id = "test_user_123"
        jwt_token = "test.jwt.token.here"
        
        # Mock get_jwt to return token
        mock_keyring.get_password.return_value = jwt_token

        # Save
        SecureStorage.save_jwt(telegram_id, jwt_token)
        mock_keyring.set_password.assert_called_once_with(
            SecureStorage.SERVICE_NAME, telegram_id, jwt_token
        )

        # Get
        retrieved = SecureStorage.get_jwt(telegram_id)
        assert retrieved == jwt_token
        mock_keyring.get_password.assert_called_once_with(
            SecureStorage.SERVICE_NAME, telegram_id
        )

    @patch('src.storage.secure_storage.keyring')
    def test_get_nonexistent_jwt(self, mock_keyring):
        """Test retrieving non-existent JWT."""
        mock_keyring.get_password.return_value = None
        
        token = SecureStorage.get_jwt("nonexistent_user")
        assert token is None

    @patch('src.storage.secure_storage.keyring')
    def test_delete_jwt(self, mock_keyring):
        """Test deleting JWT."""
        telegram_id = "test_user_456"

        # Delete
        SecureStorage.delete_jwt(telegram_id)
        mock_keyring.delete_password.assert_called_once_with(
            SecureStorage.SERVICE_NAME, telegram_id
        )
