"""
Authentication service for OTP and JWT management.
"""
import time
import jwt
from jwt.exceptions import PyJWTError
from loguru import logger
from typing import Optional, Dict, Any, Tuple

from src.services.api_client import ApiClient
from src.storage.secure_storage import SecureStorage
from src.storage.preferences_storage import PreferencesStorage
from src.config import OTP_LENGTH, JWT_EXPIRY_BUFFER_SECONDS


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

        # Validar expiración del JWT decodificando el payload
        is_valid, _ = self._validate_jwt_expiry(token)
        return is_valid

    def _validate_jwt_expiry(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate JWT token expiry.

        Args:
            token: JWT token string

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if token is valid and not expired
            - error_message: None if valid, error description if invalid
        """
        try:
            # Decode without verification (signature already verified by backend)
            # We only care about expiry
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")

            if exp is None:
                logger.warning("JWT no tiene campo 'exp'")
                return False, "JWT sin expiración"

            current_time = int(time.time())
            # Considerar expirado si queda menos de JWT_EXPIRY_BUFFER_SECONDS segundos
            if exp < (current_time + JWT_EXPIRY_BUFFER_SECONDS):
                logger.debug(f"JWT próximo a expirar o expirado: exp={exp}, current={current_time}")
                return False, "JWT expirado o próximo a expirar"

            # Token válido y no expirado
            logger.debug(f"JWT válido, expira en {exp - current_time} segundos")
            return True, None

        except PyJWTError as e:
            logger.error(f"Error decodificando JWT: {e}")
            return False, f"Error JWT: {str(e)}"
        except Exception as e:
            logger.error(f"Error validando JWT: {e}")
            return False, f"Error inesperado: {str(e)}"

    def get_jwt_expiry_info(self) -> Tuple[Optional[int], Optional[int]]:
        """
        Get JWT expiry information.

        Returns:
            Tuple of (expires_at, time_remaining)
            - expires_at: Unix timestamp when token expires (None if no token)
            - time_remaining: Seconds until expiration (None if no token or expired)
        """
        telegram_id = self.current_telegram_id
        if not telegram_id:
            return None, None

        token = SecureStorage.get_jwt(telegram_id)
        if not token:
            return None, None

        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")
            if exp:
                current_time = int(time.time())
                time_remaining = max(0, exp - current_time)
                return exp, time_remaining
            return None, None
        except Exception as e:
            logger.error(f"Error obteniendo información de expiración JWT: {e}")
            return None, None

    def get_current_user(self) -> Optional[str]:
        """Get current authenticated user telegram_id."""
        return self.current_telegram_id
