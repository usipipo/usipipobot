"""
Authentication service for OTP and JWT management.
"""
from loguru import logger
from typing import Optional, Dict, Any

from src.services.api_client import ApiClient
from src.storage.secure_storage import SecureStorage
from src.storage.preferences_storage import PreferencesStorage
from src.config import OTP_LENGTH


class AuthService:
    """Service for handling authentication flow."""

    def __init__(self):
        self.api_client = ApiClient()
        # NO usar class attribute - cada instancia tiene su propio estado
        self._current_telegram_id: Optional[str] = None

    @property
    def current_telegram_id(self) -> Optional[str]:
        """Get current telegram_id from memory or preferences."""
        if self._current_telegram_id:
            return self._current_telegram_id
        # Fallback a preferences si no está en memoria
        return PreferencesStorage.get_last_user_id()

    @current_telegram_id.setter
    def current_telegram_id(self, value: str) -> None:
        """Set current telegram_id and persist to preferences."""
        self._current_telegram_id = value
        PreferencesStorage.set_last_user_id(value)

    async def request_otp(self, identifier: str) -> Dict[str, Any]:
        """
        Request OTP code for authentication.

        Args:
            identifier: Telegram username (@user) or telegram_id

        Returns:
            Response with message and expires_in_seconds
        """
        logger.info(f"Solicitando OTP para {identifier}")

        response = await self.api_client.post(
            "/auth/request-otp",
            data={"identifier": identifier}
        )

        logger.info("OTP solicitado exitosamente")
        return response

    async def verify_otp(
        self,
        identifier: str,
        otp_code: str
    ) -> Dict[str, Any]:
        """
        Verify OTP code and receive JWT token.

        Args:
            identifier: Telegram username or telegram_id
            otp_code: 6-digit OTP code

        Returns:
            Response with access_token and user info
        """
        logger.info(f"Verificando OTP para {identifier}")

        response = await self.api_client.post(
            "/auth/verify-otp",
            data={
                "identifier": identifier,
                "otp": otp_code
            }
        )

        # Guardar JWT si la verificación es exitosa
        if "access_token" in response:
            telegram_id = str(response["user"]["telegram_id"])
            self.current_telegram_id = telegram_id
            SecureStorage.save_jwt(
                telegram_id,
                response["access_token"]
            )
            logger.info(f"JWT guardado para usuario {telegram_id}")

        return response

    async def logout(self) -> None:
        """Logout and clear JWT token."""
        telegram_id = self.current_telegram_id
        if telegram_id:
            # Llamar al endpoint de logout
            try:
                self.api_client.telegram_id = telegram_id
                await self.api_client.post(
                    "/auth/logout",
                    data={},
                    use_auth=True
                )
            except Exception as e:
                logger.warning(f"Error en logout del backend: {e}")

            # Limpiar JWT local y preferences
            SecureStorage.delete_jwt(telegram_id)
            PreferencesStorage.clear()
            self._current_telegram_id = None
            logger.info("Logout completado")

    async def is_authenticated(self) -> bool:
        """Check if user has valid JWT token."""
        telegram_id = self.current_telegram_id
        if not telegram_id:
            return False

        token = SecureStorage.get_jwt(telegram_id)
        if not token:
            return False

        # TODO: Validar expiración del JWT decodificando el payload
        # Por ahora, solo verificamos que existe el token
        return True

    def get_current_user(self) -> Optional[str]:
        """Get current authenticated user telegram_id."""
        return self.current_telegram_id
