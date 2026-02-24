"""
Servicio de autenticación para Telegram Mini App.

Valida los datos de initData de Telegram para autenticar usuarios
de manera segura sin necesidad de login tradicional.

Author: uSipipo Team
Version: 1.0.0
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qs

from config import settings
from utils.logger import logger


@dataclass
class TelegramUser:
    """Datos del usuario de Telegram desde Mini App."""

    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    photo_url: Optional[str] = None


@dataclass
class MiniAppAuthResult:
    """Resultado de la autenticación de Mini App."""

    success: bool
    user: Optional[TelegramUser] = None
    error: Optional[str] = None
    query_id: Optional[str] = None
    auth_date: Optional[int] = None


class MiniAppAuthService:
    """
    Servicio para validar la autenticación de Telegram Mini Apps.

    Telegram envía datos firmados en initData que podemos verificar
    usando el token del bot como clave secreta.
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def validate_init_data(self, init_data: str) -> MiniAppAuthResult:
        """
        Valida los datos de initData de Telegram.

        Args:
            init_data: String raw de Telegram.WebApp.initData

        Returns:
            MiniAppAuthResult con el resultado de la validación
        """
        if not init_data:
            return MiniAppAuthResult(
                success=False, error="initData vacío"
            )

        try:
            parsed_data = parse_qs(init_data, keep_blank_values=True)

            hash_value = parsed_data.get("hash", [None])[0]
            if not hash_value:
                return MiniAppAuthResult(
                    success=False, error="Hash no encontrado en initData"
                )

            auth_date_str = parsed_data.get("auth_date", [None])[0]
            if not auth_date_str:
                return MiniAppAuthResult(
                    success=False, error="auth_date no encontrado"
                )

            auth_date = int(auth_date_str)

            if not self._is_auth_fresh(auth_date):
                return MiniAppAuthResult(
                    success=False, error="Sesión expirada"
                )

            if not self._verify_hash(parsed_data, hash_value):
                return MiniAppAuthResult(
                    success=False, error="Hash inválido - datos comprometidos"
                )

            user_data = parsed_data.get("user", [None])[0]
            if not user_data:
                return MiniAppAuthResult(
                    success=False, error="Datos de usuario no encontrados"
                )

            user_info = json.loads(user_data)
            user = TelegramUser(
                id=int(user_info.get("id", 0)),
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name"),
                username=user_info.get("username"),
                language_code=user_info.get("language_code"),
                is_premium=user_info.get("is_premium", False),
                photo_url=user_info.get("photo_url"),
            )

            query_id = parsed_data.get("query_id", [None])[0]

            logger.info(f"✅ Mini App auth exitosa para usuario {user.id}")

            return MiniAppAuthResult(
                success=True,
                user=user,
                query_id=query_id,
                auth_date=auth_date,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de usuario: {e}")
            return MiniAppAuthResult(
                success=False, error="Error parseando datos de usuario"
            )
        except Exception as e:
            logger.error(f"Error validando initData: {e}")
            return MiniAppAuthResult(
                success=False, error=f"Error de validación: {str(e)}"
            )

    def _is_auth_fresh(self, auth_date: int, max_age_hours: int = 24) -> bool:
        """
        Verifica que la autenticación no sea muy antigua.

        Args:
            auth_date: Timestamp de autenticación
            max_age_hours: Edad máxima en horas (default 24)

        Returns:
            True si la autenticación es fresca
        """
        current_time = int(time.time())
        max_age_seconds = max_age_hours * 3600
        return (current_time - auth_date) < max_age_seconds

    def _verify_hash(self, parsed_data: Dict[str, Any], hash_value: str) -> bool:
        """
        Verifica el hash HMAC de los datos.

        El hash se calcula sobre los datos ordenados alfabéticamente,
        usando una clave derivada del token del bot.

        Args:
            parsed_data: Datos parseados del query string
            hash_value: Hash recibido de Telegram

        Returns:
            True si el hash es válido
        """
        data_check_items = []
        for key, value in parsed_data.items():
            if key != "hash":
                data_check_items.append(f"{key}={value[0]}")

        data_check_items.sort()
        data_check_string = "\n".join(data_check_items)

        secret_key = hmac.new(
            b"WebAppData", self.bot_token.encode(), hashlib.sha256
        ).digest()

        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        return computed_hash == hash_value


def get_miniapp_auth_service() -> MiniAppAuthService:
    """Factory para crear el servicio de autenticación."""
    return MiniAppAuthService(settings.TELEGRAM_TOKEN)
