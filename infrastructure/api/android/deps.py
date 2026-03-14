from datetime import datetime, timezone
from typing import Optional

import jwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import text

from config import settings
from infrastructure.persistence.database import get_session_context

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validar JWT token y extraer información del usuario.

    Usar como dependencia en endpoints protegidos:

    @router.get("/protected")
    async def protected_endpoint(user: dict = Depends(get_current_user)):
        ...
    """
    token = credentials.credentials

    try:
        # Decodificar JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "sub", "jti"]},
        )

        # Verificar que es un token de Android
        if payload.get("client") != "android_apk":
            logger.warning(f"Token con client inválido: {payload.get('client')}")
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_client", "message": "Token no válido para este endpoint"},
            )

        # Verificar que no está en blacklist
        jti = payload["jti"]
        async with redis.from_url(settings.REDIS_URL) as r:
            is_blacklisted = await r.exists(f"jwt:blacklist:{jti}")
            if is_blacklisted:
                logger.warning(f"Intento de usar token revocado: {jti}")
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "token_revoked",
                        "message": "Sesión cerrada. Inicia sesión nuevamente.",
                    },
                )

        # Verificar que el usuario existe y está activo
        telegram_id = payload["sub"]

        async with get_session_context() as session:
            result = await session.execute(
                text("SELECT status FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": int(telegram_id)},
            )
            user = result.first()

            if not user:
                logger.warning(f"Usuario {telegram_id} no existe en DB")
                raise HTTPException(
                    status_code=404,
                    detail={"error": "user_not_found", "message": "Usuario no encontrado"},
                )

            if user.status != "active":
                logger.warning(f"Usuario {telegram_id} está inactivo")
                raise HTTPException(
                    status_code=403,
                    detail={"error": "user_inactive", "message": "Cuenta inactiva o suspendida"},
                )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "token_expired",
                "message": "Sesión expirada. Inicia sesión nuevamente.",
            },
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {e}")
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": f"Token inválido: {str(e)}"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[dict]:
    """
    Obtener usuario si hay token válido, None si no hay token o es inválido.

    Usar en endpoints que funcionan con o sin autenticación.
    """
    try:
        return await get_current_user(credentials)
    except HTTPException as e:
        if e.status_code in (401, 403, 404):
            return None
        raise  # Re-raise server errors (500, 503, etc.)
