import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy import text

from config import settings
from infrastructure.api.android.deps import get_current_user
from infrastructure.api.android.schemas import (
    LogoutResponse,
    OTPRequest,
    OTPResponse,
    OTPVerify,
    RefreshTokenResponse,
    TokenResponse,
    UserInToken,
    UserProfileResponse,
)
from infrastructure.persistence.database import get_session_context

router = APIRouter(prefix="/auth", tags=["Android Auth"])


@router.post("/request-otp", response_model=OTPResponse)
async def request_otp(request: OTPRequest, http_request: Request):
    """
    Solicitar código OTP para autenticación.

    El OTP se genera y se envía al chat de Telegram del usuario.
    El OTP es válido por 5 minutos.

    **Rate Limits:**
    - 5 solicitudes por IP por hora
    - 3 solicitudes por usuario por hora
    """
    async with redis.from_url(settings.REDIS_URL) as r:
        # Rate limiting por IP (5 por hora)
        client_ip = http_request.client.host if http_request.client else "unknown"
        ip_key = f"rate:otp:ip:{client_ip}"

        ip_count = await r.incr(ip_key)
        if ip_count == 1:
            await r.expire(ip_key, 3600)

        if ip_count > 5:
            ttl = await r.ttl(ip_key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Demasiadas solicitudes desde tu IP",
                    "retry_after": ttl,
                },
            )

        # Rate limiting por identifier (3 por hora)
        identifier_key = f"rate:otp:identifier:{request.identifier}"
        identifier_count = await r.incr(identifier_key)
        if identifier_count == 1:
            await r.expire(identifier_key, 3600)

        if identifier_count > 3:
            ttl = await r.ttl(identifier_key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Demasiadas solicitudes para este usuario",
                    "retry_after": ttl,
                },
            )

        # Buscar usuario en base de datos
        async with get_session_context() as session:
            if request.identifier.startswith("@"):
                # Buscar por username
                result = await session.execute(
                    text(
                        "SELECT telegram_id, username, status FROM users WHERE username = :username"
                    ),
                    {"username": request.identifier[1:]},
                )
            else:
                # Buscar por telegram_id
                result = await session.execute(
                    text(
                        "SELECT telegram_id, username, status FROM users WHERE telegram_id = :telegram_id"
                    ),
                    {"telegram_id": int(request.identifier)},
                )

            user = result.first()

            if not user:
                logger.warning(f"Usuario no encontrado: {request.identifier}")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "user_not_found",
                        "message": "Usuario no registrado en uSipipo. Primero debes usar el bot de Telegram.",
                    },
                )

            if user.status != "active":
                logger.warning(f"Usuario inactivo: {user.telegram_id}")
                raise HTTPException(
                    status_code=403,
                    detail={"error": "user_inactive", "message": "Cuenta inactiva o suspendida"},
                )

        # Generar OTP (6 dígitos)
        otp = f"{secrets.randbelow(1000000):06d}"

        # Guardar OTP en Redis con TTL de 5 minutos
        otp_key = f"otp:{user.telegram_id}"
        await r.setex(otp_key, 300, otp)  # 300 segundos = 5 minutos

    logger.info(f"OTP generado para usuario {user.telegram_id}")

    # Enviar OTP por Telegram
    try:
        from telegram import Bot

        bot = Bot(token=settings.TELEGRAM_TOKEN)

        await bot.send_message(
            chat_id=user.telegram_id,
            text=(
                f"🔐 *Tu código de verificación uSipipo*:\n\n"
                f"`{otp[:3]} {otp[3:]}`\n\n"
                f"Válido por *5 minutos*.\n\n"
                f"⚠️ *No compartas este código con nadie.*"
            ),
            parse_mode="Markdown",
        )

        logger.info(f"OTP enviado a Telegram: {user.telegram_id}")

    except Exception as e:
        logger.error(f"Error enviando OTP por Telegram: {e}")
        # No fallar el endpoint si Telegram falla, el OTP ya está en Redis

    return OTPResponse(message="Código enviado a tu chat de Telegram", expires_in_seconds=300)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: OTPVerify):
    """
    Verificar código OTP y obtener JWT token.

    Si el OTP es válido, se genera un JWT token con 24 horas de validez.
    El OTP se elimina de Redis después de un uso exitoso.

    **Intentos fallidos:**
    - Máximo 3 intentos fallidos
    - Al tercer fallo, el OTP se invalida
    """
    async with redis.from_url(settings.REDIS_URL) as r:
        # Buscar usuario en base de datos
        async with get_session_context() as session:
            if request.identifier.startswith("@"):
                # Buscar por username
                result = await session.execute(
                    text(
                        "SELECT telegram_id, username, full_name, status FROM users WHERE username = :username"
                    ),
                    {"username": request.identifier[1:]},
                )
            else:
                # Buscar por telegram_id
                result = await session.execute(
                    text(
                        "SELECT telegram_id, username, full_name, status FROM users WHERE telegram_id = :telegram_id"
                    ),
                    {"telegram_id": int(request.identifier)},
                )

            user = result.first()

            if not user:
                logger.warning(f"Usuario no encontrado: {request.identifier}")
                raise HTTPException(
                    status_code=404,
                    detail={"error": "user_not_found", "message": "Usuario no encontrado"},
                )

            if user.status != "active":
                logger.warning(f"Usuario inactivo: {user.telegram_id}")
                raise HTTPException(
                    status_code=403,
                    detail={"error": "user_inactive", "message": "Cuenta inactiva o suspendida"},
                )

        # Verificar OTP
        otp_key = f"otp:{user.telegram_id}"
        stored_otp = await r.get(otp_key)

        if not stored_otp:
            logger.warning(f"OTP no encontrado o expirado: {user.telegram_id}")
            raise HTTPException(
                status_code=401,
                detail={"error": "otp_expired", "message": "Código expirado. Solicita uno nuevo."},
            )

        # Verificar que el OTP coincide (timing-safe comparison)
        if not hmac.compare_digest(stored_otp.decode(), request.otp):
            # Incrementar contador de intentos fallidos
            fail_key = f"otp:fail:{user.telegram_id}"
            fail_count = await r.incr(fail_key)
            if fail_count == 1:
                await r.expire(fail_key, 900)  # 15 minutos de ventana

            attempts_remaining = 3 - fail_count

            logger.warning(
                f"OTP inválido para usuario {user.telegram_id}. "
                f"Intentos restantes: {attempts_remaining}"
            )

            if attempts_remaining <= 0:
                # Bloquear: eliminar OTP para forzar solicitud de uno nuevo
                await r.delete(otp_key)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "too_many_attempts",
                        "message": "Demasiados intentos fallidos. Solicita un nuevo código.",
                    },
                )

            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_otp",
                    "message": "Código incorrecto",
                    "attempts_remaining": attempts_remaining,
                },
            )

        # OTP válido: eliminar de Redis (un solo uso)
        await r.delete(otp_key)
    logger.info(f"OTP verificado exitosamente: {user.telegram_id}")

    # Generar JWT token
    now = datetime.now(timezone.utc)

    jwt_payload = {
        "sub": str(user.telegram_id),
        "client": "android_apk",
        "iat": now,
        "exp": now + timedelta(hours=24),
        "jti": str(uuid.uuid4()),
    }

    token = jwt.encode(jwt_payload, settings.SECRET_KEY, algorithm="HS256")

    logger.info(f"JWT generado para usuario {user.telegram_id}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400,  # 24 horas en segundos
        user=UserInToken(
            telegram_id=user.telegram_id,
            username=user.username,
            full_name=user.full_name,
        ),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(payload: dict = Depends(get_current_user)):
    """
    Renovar JWT token si aún no ha expirado.

    Requiere un token válido. Si el token está expirado,
    el usuario debe iniciar sesión nuevamente con OTP.

    Nota: Implementa token rotation - el token anterior se invalida.
    """
    telegram_id = payload["sub"]
    old_jti = payload["jti"]
    old_exp = payload.get("exp")

    # Invalidar token actual (token rotation)
    if old_exp:
        ttl = int(old_exp - datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            async with redis.from_url(settings.REDIS_URL) as r:
                await r.setex(f"jwt:blacklist:{old_jti}", ttl, "1")
            logger.info(f"Token anterior {old_jti} invalidado en refresh")

    # Generar nuevo token
    now = datetime.now(timezone.utc)

    new_payload = {
        "sub": telegram_id,
        "client": "android_apk",
        "iat": now,
        "exp": now + timedelta(hours=24),
        "jti": str(uuid.uuid4()),
    }

    new_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm="HS256")

    logger.info(f"Token renovado para usuario {telegram_id}")

    return RefreshTokenResponse(access_token=new_token, token_type="bearer", expires_in=86400)


@router.post("/logout", response_model=LogoutResponse)
async def logout(payload: dict = Depends(get_current_user)):
    """
    Invalidar JWT token (logout).

    El token se agrega a la blacklist en Redis.
    El TTL de la blacklist es igual al tiempo restante del token.
    """
    async with redis.from_url(settings.REDIS_URL) as r:
        # Obtener tiempo restante del token
        exp = payload.get("exp")
        jti = payload["jti"]
        telegram_id = payload["sub"]

        if exp:
            ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                # Agregar a blacklist con TTL restante
                blacklist_key = f"jwt:blacklist:{jti}"
                await r.setex(blacklist_key, ttl, "1")
                logger.info(f"Token {jti} agregado a blacklist (TTL: {ttl}s)")

    logger.info(f"Usuario {telegram_id} cerró sesión")

    return LogoutResponse(message="Sesión cerrada")


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(payload: dict = Depends(get_current_user)):
    """
    Obtener perfil del usuario autenticado.

    Endpoint protegido que requiere JWT válido.
    Devuelve información básica del usuario asociado al token.

    **Respuesta:**
    - `telegram_id`: ID único del usuario
    - `username`: Username de Telegram
    - `full_name`: Nombre completo
    - `status`: Estado de la cuenta (active, suspended, blocked)
    - `has_pending_debt`: True si tiene deuda pendiente
    - `consumption_mode_enabled`: True si tiene modo consumo activo
    """
    telegram_id = payload["sub"]

    async with get_session_context() as session:
        result = await session.execute(
            text(
                """
                SELECT telegram_id, username, full_name, status,
                       has_pending_debt, consumption_mode_enabled
                FROM users
                WHERE telegram_id = :telegram_id
                """
            ),
            {"telegram_id": int(telegram_id)},
        )
        user = result.first()

        if not user:
            logger.warning(f"Usuario {telegram_id} no encontrado en DB")
            raise HTTPException(
                status_code=404,
                detail={"error": "user_not_found", "message": "Usuario no encontrado"},
            )

        logger.debug(f"Perfil de usuario {telegram_id} consultado exitosamente")

        return UserProfileResponse(
            telegram_id=user.telegram_id,
            username=user.username,
            full_name=user.full_name,
            status=user.status,
            has_pending_debt=user.has_pending_debt or False,
            consumption_mode_enabled=user.consumption_mode_enabled or False,
        )
