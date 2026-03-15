# Plan de Integración Segura de APK Android

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Contexto:** Integración de APK Android al ecosistema existente (Bot + Mini App + VPN)
> **Objetivo:** Integración sin interrupciones con seguridad máxima

---

## 🎯 Principios de Integración

### Filosofía
> **"La APK es un cliente más, no un reemplazo. El backend es la única fuente de verdad."**

### Principios Clave
1. **Backend-First:** Toda la lógica de negocio permanece en el backend
2. **Compatibilidad:** La APK no rompe funcionalidad existente
3. **Seguridad:** Autenticación JWT + certificate pinning
4. **Progresivo:** Launch por fases para detectar issues temprano

---

## 🏗️ Fase 1: Preparación del Backend

### 1.1 Nuevos Endpoints para APK

**Estructura de rutas: `infrastructure/api/android/`**

```
infrastructure/api/android/
├── __init__.py
├── router.py              ← Router principal que incluye todos los sub-routers
├── deps.py                ← Dependencias: get_current_user, rate_limiter
├── auth.py                ← POST /auth/request-otp, /auth/verify-otp, /auth/refresh, /auth/logout
├── dashboard.py           ← GET /dashboard/summary
├── keys.py                ← GET/POST/DELETE /keys/*
├── payments.py            ← POST/GET /payments/stars/*, /payments/crypto/*
├── user.py                ← GET/PUT /user/profile, /user/wallet, /user/referrals
├── tickets.py             ← GET/POST /tickets/*
└── notifications.py       ← GET /notifications/pending, POST /notifications/ack
```

**Archivo: `infrastructure/api/android/router.py`**

```python
from fastapi import APIRouter
from infrastructure.api.android import (
    auth,
    dashboard,
    keys,
    payments,
    user,
    tickets,
    notifications,
)

android_router = APIRouter(prefix="/api/v1", tags=["Android APK"])

# Incluir todos los sub-routers
android_router.include_router(auth.router)
android_router.include_router(dashboard.router)
android_router.include_router(keys.router)
android_router.include_router(payments.router)
android_router.include_router(user.router)
android_router.include_router(tickets.router)
android_router.include_router(notifications.router)
```

**Registro en `infrastructure/api/server.py`:**

```python
from infrastructure.api.android.router import android_router

def create_app() -> FastAPI:
    app = FastAPI(...)

    # Rutas existentes
    app.include_router(miniapp_router, prefix="/miniapp")
    app.include_router(webhook_router, prefix="/webhooks")

    # NUEVO: Rutas para APK Android
    app.include_router(android_router)

    return app
```

---

### 1.2 Sistema de Autenticación OTP

**Archivo: `infrastructure/api/android/auth.py`**

```python
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field, validator
import secrets
import redis.asyncio as redis
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from infrastructure.persistence.database import get_session
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Android Auth"])

# =============================================================================
# SCHEMAS
# =============================================================================

class OTPRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=50)

    @validator("identifier")
    def validate_identifier(cls, v):
        v = v.strip()
        if v.startswith("@"):
            if not re.match(r"^[a-zA-Z0-9_]{5,32}$", v[1:]):
                raise ValueError("Username inválido")
        else:
            if not v.isdigit():
                raise ValueError("Debe ser username o telegram_id")
        return v


class OTPVerify(BaseModel):
    identifier: str
    otp: str = Field(..., min_length=6, max_length=6)

    @validator("otp")
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError("OTP debe ser numérico")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/request-otp")
async def request_otp(request: OTPRequest, http_request: Request):
    """
    Solicitar código OTP para autenticación.
    El OTP se envía al chat de Telegram del usuario.
    """
    # Rate limiting por IP
    client_ip = http_request.client.host
    redis_key_ip = f"rate:otp:ip:{client_ip}"

    r = redis.from_url(settings.redis_url)

    # Verificar rate limit por IP (5 por hora)
    ip_count = await r.incr(redis_key_ip)
    if ip_count == 1:
        await r.expire(redis_key_ip, 3600)
    if ip_count > 5:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded", "message": "Demasiadas solicitudes desde tu IP"}
        )

    # Rate limiting por identifier (3 por hora)
    redis_key_identifier = f"rate:otp:identifier:{request.identifier}"
    identifier_count = await r.incr(redis_key_identifier)
    if identifier_count == 1:
        await r.expire(redis_key_identifier, 3600)
    if identifier_count > 3:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded", "message": "Demasiadas solicitudes para este usuario"}
        )

    # Buscar usuario en DB
    async with get_session() as session:
        if request.identifier.startswith("@"):
            # Buscar por username (asumiendo que hay columna username)
            result = await session.execute(
                text("SELECT telegram_id, username, full_name FROM users WHERE username = :username"),
                {"username": request.identifier[1:]}
            )
        else:
            # Buscar por telegram_id
            result = await session.execute(
                text("SELECT telegram_id, username, full_name FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": int(request.identifier)}
            )

        user = result.first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": "user_not_found", "message": "Usuario no registrado en uSipipo"}
            )

    # Generar OTP (6 dígitos)
    otp = f"{secrets.randbelow(1000000):06d}"

    # Guardar OTP en Redis con TTL de 5 minutos
    otp_key = f"otp:{user.telegram_id}"
    await r.setex(otp_key, 300, otp)  # 5 minutos

    # Enviar OTP por Telegram
    from telegram import Bot
    bot = Bot(token=settings.telegram_token)

    await bot.send_message(
        chat_id=user.telegram_id,
        text=f"🔐 *Tu código de verificación uSipipo*:\n\n`{otp[:3]} {otp[3:]}`\n\nVálido por 5 minutos.\n\n⚠️ No compartas este código con nadie.",
        parse_mode="Markdown"
    )

    logger.info(f"OTP enviado a usuario {user.telegram_id}")

    return {
        "message": "Código enviado a tu chat de Telegram",
        "expires_in_seconds": 300
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: OTPVerify):
    """
    Verificar código OTP y obtener JWT token.
    """
    r = redis.from_url(settings.redis_url)

    # Buscar usuario
    async with get_session() as session:
        if request.identifier.startswith("@"):
            result = await session.execute(
                text("SELECT telegram_id, username, full_name, status FROM users WHERE username = :username"),
                {"username": request.identifier[1:]}
            )
        else:
            result = await session.execute(
                text("SELECT telegram_id, username, full_name, status FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": int(request.identifier)}
            )

        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if user.status != "active":
            raise HTTPException(
                status_code=403,
                detail={"error": "user_inactive", "message": "Cuenta inactiva o suspendida"}
            )

    # Verificar OTP
    otp_key = f"otp:{user.telegram_id}"
    stored_otp = await r.get(otp_key)

    if not stored_otp:
        raise HTTPException(
            status_code=401,
            detail={"error": "otp_expired", "message": "Código expirado. Solicita uno nuevo."}
        )

    if stored_otp.decode() != request.otp:
        # Incrementar contador de intentos fallidos
        fail_key = f"otp:fail:{user.telegram_id}"
        fail_count = await r.incr(fail_key)
        if fail_count == 1:
            await r.expire(fail_key, 900)  # 15 minutos

        attempts_remaining = 3 - fail_count

        if attempts_remaining <= 0:
            # Bloquear por 5 minutos
            await r.delete(otp_key)
            raise HTTPException(
                status_code=429,
                detail={"error": "too_many_attempts", "message": "Demasiados intentos. Espera 5 minutos."}
            )

        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_otp",
                "message": "Código incorrecto",
                "attempts_remaining": attempts_remaining
            }
        )

    # OTP válido, eliminar de Redis
    await r.delete(otp_key)

    # Generar JWT token
    import jwt
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    jwt_payload = {
        "sub": str(user.telegram_id),
        "client": "android_apk",
        "iat": now,
        "exp": now + timedelta(hours=24),
        "jti": secrets.token_uuid(),
    }

    token = jwt.encode(
        jwt_payload,
        settings.secret_key,
        algorithm="HS256"
    )

    logger.info(f"Usuario {user.telegram_id} autenticado exitosamente desde APK")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=86400,  # 24 horas
        user={
            "telegram_id": user.telegram_id,
            "username": user.username,
            "full_name": user.full_name,
        }
    )


@router.post("/refresh")
async def refresh_token(payload: dict = Depends(get_current_user)):
    """
    Renovar JWT token si aún no ha expirado.
    """
    import jwt
    from datetime import datetime, timezone, timedelta

    telegram_id = payload["sub"]

    now = datetime.now(timezone.utc)

    new_payload = {
        "sub": telegram_id,
        "client": "android_apk",
        "iat": now,
        "exp": now + timedelta(hours=24),
        "jti": secrets.token_uuid(),
    }

    new_token = jwt.encode(new_payload, settings.secret_key, algorithm="HS256")

    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": 86400
    }


@router.post("/logout")
async def logout(payload: dict = Depends(get_current_user), jti: str = None):
    """
    Invalidar JWT token (logout).
    El token se agrega a la blacklist en Redis.
    """
    r = redis.from_url(settings.redis_url)

    # Obtener tiempo restante del token
    exp = payload.get("exp")
    if exp:
        ttl = int(exp - datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            # Agregar a blacklist
            blacklist_key = f"jwt:blacklist:{jti}"
            await r.setex(blacklist_key, ttl, "1")

    logger.info(f"Usuario {payload['sub']} cerró sesión")

    return {"message": "Sesión cerrada"}
```

---

### 1.3 Dependencias de Autenticación

**Archivo: `infrastructure/api/android/deps.py`**

```python
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from config import settings
import redis.asyncio as redis
from sqlalchemy import text
from infrastructure.persistence.database import get_session

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validar JWT token y extraer información del usuario.
    Usar como dependencia en endpoints protegidos.
    """
    token = credentials.credentials

    try:
        # Decodificar JWT
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            options={"require": ["exp", "sub", "jti"]}
        )

        # Verificar que es un token de Android
        if payload.get("client") != "android_apk":
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_client", "message": "Token no válido para este endpoint"}
            )

        # Verificar que no está en blacklist
        jti = payload["jti"]
        r = redis.from_url(settings.redis_url)

        is_blacklisted = await r.exists(f"jwt:blacklist:{jti}")
        if is_blacklisted:
            raise HTTPException(
                status_code=401,
                detail={"error": "token_revoked", "message": "Sesión cerrada. Inicia sesión nuevamente."}
            )

        # Verificar que el usuario existe y está activo
        telegram_id = payload["sub"]

        async with get_session() as session:
            result = await session.execute(
                text("SELECT status FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": int(telegram_id)}
            )
            user = result.first()

            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            if user.status != "active":
                raise HTTPException(
                    status_code=403,
                    detail={"error": "user_inactive", "message": "Cuenta inactiva"}
                )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": "token_expired", "message": "Sesión expirada. Inicia sesión nuevamente."}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": f"Token inválido: {str(e)}"}
        )


def rate_limiter(limit: int, window: int):
    """
    Decorador para rate limiting personalizado.

    Usage:
        @router.post("/endpoint")
        @rate_limiter(limit=5, window=3600)
        async def endpoint(...):
            ...
    """
    async def rate_limit_checker(
        request: Request,
        payload: dict = Depends(get_current_user)
    ):
        r = redis.from_url(settings.redis_url)
        telegram_id = payload["sub"]

        key = f"rate:{request.url.path}:{telegram_id}"
        count = await r.incr(key)

        if count == 1:
            await r.expire(key, window)

        if count > limit:
            ttl = await r.ttl(key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Demasiadas peticiones",
                    "retry_after": ttl
                }
            )

    return Depends(rate_limit_checker)
```

---

## 📱 Fase 2: Integración con el Bot de Telegram

### 2.1 Notificaciones Cruzadas

Cuando un usuario se autentica en la APK, el bot debe notificar:

**Archivo: `infrastructure/api/android/auth.py` (agregar al final de verify_otp)**

```python
# Notificar al usuario por Telegram
await bot.send_message(
    chat_id=user.telegram_id,
    text=f"✅ *Inicio de sesión exitoso*\n\n"
         f"Has iniciado sesión en la APK de uSipipo desde un dispositivo Android.\n\n"
         f"🕐 Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
         f"📱 Dispositivo: Android\n\n"
         f"Si no fuiste tú, contacta soporte inmediatamente.",
    parse_mode="Markdown"
)
```

### 2.2 Sincronización de Estado

Cuando un usuario elimina una clave en la APK, el bot debe actualizar su estado:

**En `infrastructure/api/android/keys.py` (DELETE endpoint):**

```python
# Después de eliminar la clave exitosamente
from telegram_bot.features.operations.messages_operations import send_key_deleted_message

# Notificar por Telegram
try:
    await bot.send_message(
        chat_id=telegram_id,
        text=f"🗑️ *Clave eliminada*\n\n"
             f"La clave *{key_name}* fue eliminada desde la APK Android.\n\n"
             f"Si no fuiste tú, contacta soporte.",
        parse_mode="Markdown"
    )
except Exception as e:
    logger.error(f"No se pudo enviar notificación de eliminación: {e}")
```

---

## 🔐 Fase 3: Seguridad Específica para APK

### 3.1 Certificate Pinning en el Backend

**Archivo: `infrastructure/api/middleware/certificate_pin.py`**

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import ssl
from typing import List

class CertificatePinMiddleware(BaseHTTPMiddleware):
    """
    Verificar que las peticiones de la APK usan el certificado correcto.
    Esto previene ataques MITM donde un atacante podría interceptar el tráfico.
    """

    def __init__(self, app, expected_pins: List[str]):
        super().__init__(app)
        self.expected_pins = expected_pins

    async def dispatch(self, request: Request, call_next):
        # Solo aplicar a rutas de Android
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        # Obtener certificado SSL de la conexión
        # Nota: Esto requiere acceso al certificado del cliente,
        # lo cual es complejo en HTTP normal.
        # Una alternativa es verificar el User-Agent y aplicar
        # validaciones adicionales para peticiones de la APK.

        user_agent = request.headers.get("User-Agent", "")

        if "uSipipo-Android" in user_agent:
            # Peticiones de la APK - aplicar validaciones extra
            # Por ejemplo, verificar headers específicos que solo la APK conoce

            apk_secret = request.headers.get("X-APK-Secret")
            if not apk_secret or apk_secret != settings.apk_secret_header:
                # No es una petición legítima de la APK
                logger.warning(f"Peticiones sospechosa de APK: {request.client.host}")

        return await call_next(request)
```

### 3.2 Rate Limiting Específico para APK

**En `infrastructure/api/android/deps.py`:**

```python
# Rate limits específicos para endpoints de APK
ANDROID_RATE_LIMITS = {
    "/auth/request-otp": (3, 3600),      # 3 por hora
    "/auth/verify-otp": (5, 900),         # 5 por 15 min
    "/keys/create": (5, 3600),            # 5 por hora
    "/payments/stars/create": (10, 3600), # 10 por hora
    "/payments/crypto/create": (10, 3600),# 10 por hora
    "/dashboard/summary": (60, 60),       # 60 por minuto
    "/notifications/pending": (120, 60),  # 120 por minuto
}
```

---

## 🚀 Fase 4: Launch Progresivo

### 4.1 Estrategia de Rollout

```
Semana 1:  Alpha (10 usuarios)
           └── Equipo interno + beta testers de confianza

Semana 2:  Beta Cerrado (50 usuarios)
           └── Usuarios seleccionados por referidos

Semana 3:  Beta Abierto (200 usuarios)
           └── Cualquiera puede descargar, pero con invite code

Semana 4:  Launch Público (ilimitado)
           └── Disponible en GitHub Releases
```

### 4.2 Feature Flags

**Archivo: `config.py`**

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Feature flags para APK Android
    apk_enabled: bool = True
    apk_alpha_mode: bool = False
    apk_allowed_users: list = []  # Telegram IDs de usuarios permitidos en alpha/beta

    class Config:
        env_file = ".env"
```

**En `infrastructure/api/android/deps.py`:**

```python
async def check_apk_access(payload: dict = Depends(get_current_user)):
    """
    Verificar si el usuario tiene acceso a la APK.
    Usar durante alpha/beta testing.
    """
    telegram_id = int(payload["sub"])

    if settings.apk_alpha_mode:
        if telegram_id not in settings.apk_allowed_users:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "access_denied",
                    "message": "La APK está en alpha testing. Acceso solo para beta testers."
                }
            )
```

---

## 📊 Fase 5: Monitoreo Específico de APK

### 5.1 Métricas de Uso de APK

**Archivo: `infrastructure/api/android/metrics.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text, func
from infrastructure.persistence.database import get_session

router = APIRouter(prefix="/metrics", tags=["Android Metrics"])


@router.get("/apk/usage")
async def apk_usage_metrics():
    """
    Métricas de uso de la APK Android.
    Solo accesible para admins.
    """
    async with get_session() as session:
        # Usuarios activos en APK (últimas 24h)
        # Esto requeriría una tabla de sesiones o logs de acceso

        # Por ahora, contar autenticaciones exitosas
        result = await session.execute(text("""
            -- Placeholder: implementar tabla de audit_log
            SELECT COUNT(*) FROM audit_log
            WHERE action = 'android_login'
            AND created_at > NOW() - INTERVAL '24 hours'
        """))

        apk_logins_24h = result.scalar() or 0

        return {
            "apk_logins_24h": apk_logins_24h,
            # ... más métricas
        }
```

### 5.2 Logs de Auditoría

**Agregar a `infrastructure/api/android/auth.py`:**

```python
# Log de autenticación exitosa
async with get_session() as session:
    await session.execute(text("""
        INSERT INTO audit_log (telegram_id, action, details, ip_address, created_at)
        VALUES (:telegram_id, 'android_login', :details, :ip, NOW())
    """), {
        "telegram_id": user.telegram_id,
        "details": f"Android APK login from {request.client.host}",
        "ip": request.client.host
    })
    await session.commit()
```

---

## ✅ Checklist de Implementación

### Semana 1: Backend para APK
- [ ] Crear estructura de carpetas `infrastructure/api/android/`
- [ ] Implementar endpoints de autenticación OTP
- [ ] Implementar endpoints de dashboard
- [ ] Implementar endpoints de claves VPN
- [ ] Implementar endpoints de pagos
- [ ] Implementar endpoints de usuario
- [ ] Implementar endpoints de tickets
- [ ] Implementar endpoints de notificaciones
- [ ] Agregar middleware de autenticación JWT
- [ ] Configurar rate limiting específico

### Semana 2: Integración y Testing
- [ ] Integrar con bot de Telegram para notificaciones OTP
- [ ] Integrar con sistema de notificaciones existente
- [ ] Probar flujo completo de autenticación
- [ ] Probar creación de claves desde APK
- [ ] Probar pagos desde APK
- [ ] Configurar feature flags para alpha testing
- [ ] Seleccionar 10 beta testers

### Semana 3: Alpha Testing
- [ ] Lanzar APK a 10 usuarios alpha
- [ ] Monitorear errores y reportes
- [ ] Ajustar rate limits según uso real
- [ ] Corregir bugs críticos
- [ ] Preparar para beta cerrado (50 usuarios)

### Semana 4: Beta y Launch
- [ ] Lanzar beta cerrado a 50 usuarios
- [ ] Recoger feedback
- [ ] Ajustar UX según feedback
- [ ] Preparar launch público
- [ ] Documentar proceso de instalación para usuarios
- [ ] Launch público en GitHub Releases

---

## 🎯 Métricas de Éxito de Integración

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Autenticaciones exitosas | >95% | Logs de auth |
| Latencia de autenticación | <500ms | Timing de endpoint |
| Errores de rate limiting | <1% | Logs de rate limit |
| Usuarios activos en APK (semana 1) | 10 | Métricas de uso |
| Usuarios activos en APK (mes 1) | 200 | Métricas de uso |
| Crash rate de APK | <2% | Reportes de usuarios |
| Rating en usuarios | >4.5/5 | Feedback |

---

## 📚 Documentación para Usuarios

### Guía de Instalación de APK

**Archivo: `android_app/README.md`**

```markdown
# uSipipo VPN - APK Android

## Requisitos
- Android 8.0 o superior
- Tener cuenta activa en @uSipipoBot de Telegram
- Haber creado al menos una clave VPN desde el bot

## Instalación

### Paso 1: Habilitar fuentes desconocidas
1. Ve a **Ajustes** → **Seguridad**
2. Activa **Fuentes desconocidas** o **Instalar apps desconocidas**

### Paso 2: Descargar APK
1. Ve a [GitHub Releases](https://github.com/usipipo/usipipobot/releases)
2. Descarga el archivo `usipipo-1.0.0-release.apk`

### Paso 3: Instalar
1. Abre el archivo descargado
2. Toca **Instalar**
3. Espera a que termine la instalación

### Paso 4: Iniciar sesión
1. Abre la app uSipipo
2. Ingresa tu `@username` de Telegram
3. Revisa tu chat con @uSipipoBot para el código OTP
4. Ingresa el código en la app
5. ¡Listo!

## Primeros Pasos

### Ver mis claves VPN
- Toca la pestaña **Claves** en la parte inferior
- Verás todas tus claves activas
- Toca una clave para ver detalles

### Crear nueva clave
1. Toca el botón **+** en la pantalla de Claves
2. Elige el tipo de VPN (Outline o WireGuard)
3. Ponle un nombre a tu clave
4. Confirma la creación
5. Escanea el QR o copia el código de configuración

### Comprar más datos
1. Toca la pestaña **Comprar**
2. Elige tu paquete
3. Selecciona método de pago (Stars o USDT)
4. Sigue las instrucciones

## Soporte

Si tienes problemas:
1. Abre la app y ve a **Perfil** → **Soporte**
2. Crea un ticket describiendo tu problema
3. El equipo te responderá en menos de 24 horas

## Seguridad

- La app usa certificate pinning para proteger tu conexión
- Tu token de sesión se guarda en el keystore de Android
- Nunca compartas tu código OTP con nadie
```

---

*Documento versión 1.0 - Fecha: Marzo 2026*
