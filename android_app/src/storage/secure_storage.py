"""
Secure storage for JWT tokens using Android Keystore via keyring.
"""
import keyring
from loguru import logger
from typing import Optional

from src.config import JWT_STORAGE_SERVICE


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
