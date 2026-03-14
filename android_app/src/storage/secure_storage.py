"""
Secure storage for JWT tokens using Android Keystore via keyring.
Includes encryption for sensitive data like cache.
"""
import keyring
import base64
from loguru import logger
from typing import Optional

from src.config import JWT_STORAGE_SERVICE

# Simple XOR encryption for cache data (not for security, just obfuscation)
# For production, consider using cryptography library
ENCRYPTION_KEY = b"usipipo_cache_key_2026"


class SecureStorage:
    """Secure storage using Android Keystore."""

    SERVICE_NAME = JWT_STORAGE_SERVICE

    @staticmethod
    def save_jwt(telegram_id: str, jwt_token: str) -> None:
        """Save JWT token securely."""
        try:
            keyring.set_password(SecureStorage.SERVICE_NAME, telegram_id, jwt_token)
            logger.info(f"JWT guardado para usuario {telegram_id}")
        except Exception as e:
            logger.error(f"Error guardando JWT: {e}")
            raise

    @staticmethod
    def get_jwt(telegram_id: str) -> Optional[str]:
        """Retrieve JWT token securely."""
        try:
            token = keyring.get_password(SecureStorage.SERVICE_NAME, telegram_id)
            if token:
                logger.debug(f"JWT recuperado para usuario {telegram_id}")
            return token
        except Exception as e:
            logger.error(f"Error recuperando JWT: {e}")
            return None

    @staticmethod
    def delete_jwt(telegram_id: str) -> None:
        """Delete JWT token securely."""
        try:
            keyring.delete_password(SecureStorage.SERVICE_NAME, telegram_id)
            logger.info(f"JWT eliminado para usuario {telegram_id}")
        except Exception as e:
            logger.error(f"Error eliminando JWT: {e}")
            raise

    @staticmethod
    def clear_all() -> None:
        """
        Limpia todos los tokens almacenados.

        NOTA: keyring no soporta listar todas las claves por SERVICE_NAME.
        Usa PreferencesStorage para obtener el telegram_id y llamar delete_jwt(telegram_id).

        Ejemplo:
            telegram_id = PreferencesStorage.get_last_user_id()
            if telegram_id:
                SecureStorage.delete_jwt(telegram_id)
        """
        pass  # Intencional: ver docstring

    @staticmethod
    def encrypt(data: str) -> str:
        """
        Encrypt string data using simple XOR cipher.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        try:
            data_bytes = data.encode('utf-8')
            key_bytes = ENCRYPTION_KEY * (len(data_bytes) // len(ENCRYPTION_KEY) + 1)
            encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_bytes))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """
        Decrypt base64-encoded XOR-encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted plain text data
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            key_bytes = ENCRYPTION_KEY * (len(encrypted_bytes) // len(ENCRYPTION_KEY) + 1)
            decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_bytes))
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

    @staticmethod
    def set_secret(key: str, value: str) -> None:
        """
        Store an encrypted secret.
        
        Args:
            key: Secret key name
            value: Secret value to store
        """
        try:
            keyring.set_password(SecureStorage.SERVICE_NAME, key, value)
            logger.debug(f"Secret stored: {key}")
        except Exception as e:
            logger.error(f"Error storing secret {key}: {e}")
            raise

    @staticmethod
    def get_secret(key: str) -> Optional[str]:
        """
        Retrieve a stored secret.
        
        Args:
            key: Secret key name
            
        Returns:
            Secret value or None if not found
        """
        try:
            value = keyring.get_password(SecureStorage.SERVICE_NAME, key)
            if value:
                logger.debug(f"Secret retrieved: {key}")
            return value
        except Exception as e:
            logger.error(f"Error retrieving secret {key}: {e}")
            return None

    @staticmethod
    def delete_secret(key: str) -> None:
        """
        Delete a stored secret.
        
        Args:
            key: Secret key name
        """
        try:
            keyring.delete_password(SecureStorage.SERVICE_NAME, key)
            logger.debug(f"Secret deleted: {key}")
        except Exception as e:
            logger.error(f"Error deleting secret {key}: {e}")
            raise
