from fastapi import APIRouter, HTTPException, status, Request
from infrastructure.api.android.schemas import OTPRequest, OTPResponse, OTPVerify, TokenResponse
from sqlalchemy import text
from infrastructure.persistence.database import get_session_context
from config import settings
import secrets
import redis.asyncio as redis
from loguru import logger
import jwt
import uuid
from datetime import datetime, timezone, timedelta

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
    r = redis.from_url(settings.REDIS_URL)

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
                "retry_after": ttl
            }
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
                "retry_after": ttl
            }
        )

    # Buscar usuario en base de datos
    async with get_session_context() as session:
        if request.identifier.startswith("@"):
            # Buscar por username
            result = await session.execute(
                text("SELECT telegram_id, username, status FROM users WHERE username = :username"),
                {"username": request.identifier[1:]}
            )
        else:
            # Buscar por telegram_id
            result = await session.execute(
                text("SELECT telegram_id, username, status FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": int(request.identifier)}
            )

        user = result.first()

        if not user:
            logger.warning(f"Usuario no encontrado: {request.identifier}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "user_not_found",
                    "message": "Usuario no registrado en uSipipo. Primero debes usar el bot de Telegram."
                }
            )

        if user.status != "active":
            logger.warning(f"Usuario inactivo: {user.telegram_id}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "user_inactive",
                    "message": "Cuenta inactiva o suspendida"
                }
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
            parse_mode="Markdown"
        )

        logger.info(f"OTP enviado a Telegram: {user.telegram_id}")

    except Exception as e:
        logger.error(f"Error enviando OTP por Telegram: {e}")
        # No fallar el endpoint si Telegram falla, el OTP ya está en Redis

    return OTPResponse(
        message="Código enviado a tu chat de Telegram",
        expires_in_seconds=300
    )


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
    r = redis.from_url(settings.REDIS_URL)

    # Buscar usuario en base de datos
    async with get_session_context() as session:
        if request.identifier.startswith("@"):
            # Buscar por username
            result = await session.execute(
                text("SELECT telegram_id, username, full_name, status FROM users WHERE username = :username"),
                {"username": request.identifier[1:]}
            )
        else:
            # Buscar por telegram_id
            result = await session.execute(
                text("SELECT telegram_id, username, full_name, status FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": int(request.identifier)}
            )

        user = result.first()

        if not user:
            logger.warning(f"Usuario no encontrado: {request.identifier}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "user_not_found",
                    "message": "Usuario no encontrado"
                }
            )

        if user.status != "active":
            logger.warning(f"Usuario inactivo: {user.telegram_id}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "user_inactive",
                    "message": "Cuenta inactiva o suspendida"
                }
            )

    # Verificar OTP
    otp_key = f"otp:{user.telegram_id}"
    stored_otp = await r.get(otp_key)

    if not stored_otp:
        logger.warning(f"OTP no encontrado o expirado: {user.telegram_id}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "otp_expired",
                "message": "Código expirado. Solicita uno nuevo."
            }
        )

    # Verificar que el OTP coincide
    if stored_otp.decode() != request.otp:
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
                    "message": "Demasiados intentos fallidos. Solicita un nuevo código."
                }
            )

        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_otp",
                "message": "Código incorrecto",
                "attempts_remaining": attempts_remaining
            }
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

    token = jwt.encode(
        jwt_payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    logger.info(f"JWT generado para usuario {user.telegram_id}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400,  # 24 horas en segundos
        user={
            "telegram_id": user.telegram_id,
            "username": user.username,
            "full_name": user.full_name,
        }
    )
