# 🔐 Auditoría de Seguridad y Estructura — Módulo Auth APK
> **uSipipo VPN Android** · Fase de Implementación: Auth (Fases 01.1–01.3)
> Fecha: 2026-03-14 · Estado: Listo para revisión pre-siguiente fase

---

## 📋 Resumen Ejecutivo

El módulo de autenticación está bien arquitecturado con Clean Architecture y cubre los casos de uso principales (OTP request/verify, JWT, refresh, logout, blacklist). Sin embargo, se identificaron **2 hallazgos críticos**, **5 hallazgos altos**, y **6 mejoras de calidad** que deben resolverse antes de continuar con la siguiente fase.

| Severidad | Cantidad | Estado requerido |
|-----------|----------|-----------------|
| 🔴 CRÍTICO | 2 | Bloquea siguiente fase |
| 🟠 ALTO | 5 | Resolver antes de siguiente fase |
| 🟡 MEDIO | 4 | Resolver antes de producción |
| 🟢 BAJO | 2 | Nice-to-have |

---

## 🔴 HALLAZGOS CRÍTICOS

### C-01 · CORS wildcard no bloqueado en producción
**Archivo:** `config.py` línea 464
**Descripción:** El validador `validate_environment` detecta `*` en `CORS_ORIGINS` cuando `is_production=True`, pero hace `pass` — no lanza error ni fuerza orígenes específicos. Cualquier origen puede llamar a la API en producción.

```python
# CÓDIGO ACTUAL (INSEGURO)
if self.is_production and "*" in self.CORS_ORIGINS:
    pass  # ← Bug: no hace nada

# CÓDIGO CORRECTO
if self.is_production and "*" in self.CORS_ORIGINS:
    raise ValueError(
        "CORS_ORIGINS no puede ser '*' en producción. "
        "Define los orígenes permitidos explícitamente."
    )
```

**Impacto:** Cross-Origin attacks desde cualquier dominio malicioso.

---

### C-02 · Redis connection leak — sin pool ni cierre de conexiones
**Archivo:** `infrastructure/api/android/auth.py` (líneas 32, 156, 319) y `deps.py` (línea 51)
**Descripción:** Se crea una nueva conexión Redis con `redis.from_url()` en cada request sin cerrarla con `await r.aclose()`. En un VPS con RAM limitada, esto genera connection leaks que pueden saturar Redis o agotar file descriptors.

```python
# CÓDIGO ACTUAL (PELIGROSO)
r = redis.from_url(settings.REDIS_URL)
ip_count = await r.incr(ip_key)
# ← r nunca se cierra

# CÓDIGO CORRECTO
async with redis.from_url(settings.REDIS_URL) as r:
    ip_count = await r.incr(ip_key)
```

**Afecta:** `request_otp`, `verify_otp`, `logout`, `get_current_user` (deps.py). Son 4 lugares distintos.
**Impacto:** Memory leak, degradación del servicio en el VPS, posible crash de Redis.

---

## 🟠 HALLAZGOS ALTOS

### A-01 · Timing attack en comparación de OTP
**Archivo:** `infrastructure/api/android/auth.py` línea 210
**Descripción:** La comparación `stored_otp.decode() != request.otp` es vulnerable a timing attacks. Un atacante puede medir tiempos de respuesta para inferir dígitos del OTP.

```python
# CÓDIGO ACTUAL (VULNERABLE)
if stored_otp.decode() != request.otp:

# CÓDIGO CORRECTO
import hmac
if not hmac.compare_digest(stored_otp.decode(), request.otp):
```

**Impacto:** Bajo en la práctica dado el rate limiting, pero es una vulnerabilidad conocida que debe cerrarse.

---

### A-02 · Rate limiting global en memoria — no persiste entre workers ni reinicios
**Archivo:** `infrastructure/api/middleware/rate_limit.py` líneas 14-15
**Descripción:** `RateLimitMiddleware` usa `defaultdict(list)` en memoria. Si el servidor tiene múltiples workers (uvicorn con `--workers N`) o se reinicia, el contador se resetea. El rate limiting del módulo auth ya usa Redis correctamente, pero el middleware global no.

```python
# CÓDIGO ACTUAL (INEFICAZ EN MULTI-WORKER)
self.requests: Dict[str, List[float]] = defaultdict(list)

# SOLUCIÓN: Migrar a Redis o usar slowapi
# pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
```

**Impacto:** El rate limiting global es bypasseable con múltiples requests en paralelo a workers distintos.

---

### A-03 · `refresh_token` no invalida el token anterior (token rotation ausente)
**Archivo:** `infrastructure/api/android/auth.py` función `refresh_token`
**Descripción:** Al llamar `/auth/refresh`, se genera un nuevo JWT pero el token anterior sigue válido hasta su expiración. Si un token es robado, el atacante puede seguir usándolo aunque el usuario haga refresh.

```python
# AGREGAR al inicio de refresh_token:
# 1. Agregar token actual a blacklist
jti = payload["jti"]
exp = payload.get("exp")
if exp:
    ttl = int(exp - datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        async with redis.from_url(settings.REDIS_URL) as r:
            await r.setex(f"jwt:blacklist:{jti}", ttl, "1")
```

---

### A-04 · `get_current_user_optional` en `deps.py` ignora silenciosamente errores reales
**Archivo:** `infrastructure/api/android/deps.py` líneas finales
**Descripción:** La función captura `HTTPException` genéricamente y retorna `None`, incluyendo errores 500 (DB caída, Redis caído). Esto puede enmascarar fallos de infraestructura y hacer que endpoints opcionales funcionen sin autenticación cuando no deberían.

```python
# CÓDIGO ACTUAL
except HTTPException:
    return None  # ← Captura TODOS los HTTPException, incluyendo 500

# CÓDIGO CORRECTO
except HTTPException as e:
    if e.status_code in (401, 403, 404):
        return None  # Esperado: no autenticado
    raise  # Re-raise errores de infraestructura
```

---

### A-05 · APK Android: `ApiClient` no verifica certificado SSL en ningún contexto
**Archivo:** `android_app/src/services/api_client.py`
**Descripción:** `httpx.AsyncClient` usa `verify=True` por defecto, lo cual es correcto. Sin embargo, no hay ninguna validación de que `BASE_URL` use HTTPS, y no hay certificate pinning. Si el dominio DuckDNS cambia o hay un MITM, el cliente APK no lo detecta.

**Acciones requeridas:**
1. Validar en `config.py` que `BASE_URL` empiece con `https://` en producción.
2. Agregar un aviso en `ApiClient.__init__` si la URL no es HTTPS.

```python
# En android_app/src/config.py — agregar al final:
if IS_PRODUCTION and not BASE_URL.startswith("https://"):
    raise ValueError(f"BASE_URL debe usar HTTPS en producción: {BASE_URL}")
```

---

## 🟡 HALLAZGOS MEDIOS

### M-01 · `example.env` expone dominio interno real (`usipipo.duckdns.org`)
**Archivo:** `example.env` y `android_app/src/config.py` línea 16
**Descripción:** El fallback hardcodeado `https://usipipo.duckdns.org/api/v1` en `config.py` expone el dominio real del servidor en el código fuente del APK. Cualquier APK descompilado (`.apk` → `jadx`) revela el endpoint.

**Acción:** Cambiar el default a una URL genérica de ejemplo o vacía, y documentar que debe configurarse antes de compilar.

```python
# CAMBIAR:
BASE_URL = os.getenv("USIPIPO_API_URL", "https://usipipo.duckdns.org/api/v1")
# POR:
BASE_URL = os.getenv("USIPIPO_API_URL", "")
if not BASE_URL:
    raise ValueError("USIPIPO_API_URL no configurada. Ver android_app/README.md")
```

---

### M-02 · OTP enviado como texto plano en logs de Telegram Bot
**Archivo:** `infrastructure/api/android/auth.py` línea ~100
**Descripción:** El bloque `except Exception as e` al enviar el OTP por Telegram hace `logger.error(f"Error enviando OTP por Telegram: {e}")`. Si el error incluye el chat_id y el OTP en el traceback, quedaría en logs. Además, el OTP generado se loguea con nivel INFO (`OTP generado para usuario {telegram_id}`), lo cual es aceptable, pero el OTP en sí nunca debe aparecer en logs.

**Verificar:** Que `otp` nunca sea incluido en ningún `logger.*` call.

---

### M-03 · `user` en `TokenResponse` es `dict` sin schema tipado
**Archivo:** `infrastructure/api/android/schemas.py` clase `TokenResponse`
**Descripción:** El campo `user: dict` no tiene validación. Si el backend cambia los campos del usuario, la respuesta no falla con un error claro sino que pasa silenciosamente. Debe ser un schema `UserInToken` explícito.

```python
# AGREGAR antes de TokenResponse:
class UserInToken(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInToken  # ← tipado
```

---

### M-04 · Test coverage insuficiente para endpoints del servidor
**Archivos:** `tests/` directorio
**Descripción:** Solo existe un script bash de prueba manual (`test_auth_flow.sh`). No hay tests de integración con pytest para los endpoints FastAPI (`/auth/request-otp`, `/auth/verify-otp`, `/auth/refresh`, `/auth/logout`, `/auth/me`). Los tests del cliente Android son buenos pero no cubren el lado servidor.

**Mínimo requerido antes de siguiente fase:**
- Test de `request_otp` con usuario no existente → 404
- Test de `verify_otp` con OTP incorrecto → contador de intentos
- Test de `verify_otp` con OTP expirado → 401
- Test de `logout` → blacklist en Redis
- Test de uso de token blacklisteado → 401

---

## 🟢 MEJORAS DE CALIDAD (BAJO)

### B-01 · `SecureStorage.clear_all()` no implementado
**Archivo:** `android_app/src/storage/secure_storage.py` línea 50
**Descripción:** El método existe pero hace `pass`. Si hay múltiples usuarios o se requiere un factory reset de la app, no hay forma de limpiar todos los tokens.

**Acción:** Documentar la limitación de `keyring` o implementar un índice de `telegram_id` guardados en `PreferencesStorage` para poder iterar y eliminar.

---

### B-02 · `JWT_EXPIRY_BUFFER_SECONDS` definido pero no usado en `auth_service.py`
**Archivo:** `android_app/src/config.py` línea 9, `android_app/src/services/auth_service.py`
**Descripción:** `JWT_EXPIRY_BUFFER_SECONDS = 30` está en config pero `_validate_jwt_expiry` no lo utiliza. El cliente debería considerar el token como "a punto de expirar" 30 segundos antes y hacer refresh proactivo.

---

## ✅ LO QUE ESTÁ BIEN IMPLEMENTADO

Antes de las acciones, es importante reconocer lo que ya funciona correctamente:

- ✅ **OTP de un solo uso**: se elimina de Redis tras verificación exitosa
- ✅ **Blacklist JWT con TTL**: el logout agrega el `jti` a Redis con TTL igual al tiempo restante del token
- ✅ **Rate limiting OTP en Redis**: tanto por IP (5/hora) como por identifier (3/hora), correctamente persistido
- ✅ **Contador de intentos fallidos**: máximo 3 intentos, invalida el OTP en el tercer fallo
- ✅ **Validación de `client: android_apk`** en el JWT para separar contextos de uso
- ✅ **`jti` (JWT ID)** único por token, habilitando revocación granular
- ✅ **Validación de inputs** con Pydantic en schemas (OTPRequest, OTPVerify)
- ✅ **`SecureStorage` usando Keyring** (Android Keystore) para el JWT en el cliente
- ✅ **Security headers** en middleware (HSTS, X-Frame-Options, etc.)
- ✅ **Docs deshabilitados en producción** (`docs_url=None` cuando `is_production`)
- ✅ **Estructura Clean Architecture** bien separada: domain/application/infrastructure/android_app

---

## 🚀 PLAN DE ACCIONES PARA EL AGENTE

A continuación el plan detallado en orden de prioridad. El agente debe ejecutar todas las tareas de **Bloque 1 y Bloque 2** antes de continuar con la siguiente fase del APK.

---

### BLOQUE 1 — CRÍTICOS (ejecutar primero)

#### Tarea 1.1 · Cerrar CORS wildcard en producción
**Archivo a modificar:** `config.py`
**Acción exacta:** En el método `validate_environment`, reemplazar el bloque `pass` por un `raise ValueError`.

```python
# BUSCAR (línea ~464):
if self.is_production and "*" in self.CORS_ORIGINS:
    pass

# REEMPLAZAR POR:
if self.is_production and "*" in self.CORS_ORIGINS:
    raise ValueError(
        "CORS_ORIGINS no puede contener '*' en producción. "
        "Define los orígenes permitidos. Ejemplo: "
        "CORS_ORIGINS=[\"https://usipipo.duckdns.org\"]"
    )
```

**Verificación:** Ejecutar `APP_ENV=production python -c "from config import settings"` con `CORS_ORIGINS=["*"]` debe lanzar error.

---

#### Tarea 1.2 · Cerrar Redis connection leaks en auth.py
**Archivo a modificar:** `infrastructure/api/android/auth.py`
**Acción:** Reemplazar todos los `r = redis.from_url(...)` sueltos por `async with redis.from_url(...) as r:`.

**Hay exactamente 3 ocurrencias en auth.py:**

1. En `request_otp` (línea ~32): Envolver TODO el bloque de Redis (desde rate limiting hasta `r.setex(otp_key, ...)`) en un único `async with`.

2. En `verify_otp` (línea ~156): Envolver desde `stored_otp = await r.get(otp_key)` hasta `await r.delete(otp_key)` en `async with`.

3. En `logout` (línea ~319): Envolver el bloque de blacklist.

**Archivo a modificar también:** `infrastructure/api/android/deps.py`
**Acción:** En `get_current_user`, reemplazar:
```python
r = redis.from_url(settings.REDIS_URL)
is_blacklisted = await r.exists(f"jwt:blacklist:{jti}")
```
por:
```python
async with redis.from_url(settings.REDIS_URL) as r:
    is_blacklisted = await r.exists(f"jwt:blacklist:{jti}")
```

**Verificación:** Revisar con `redis-cli info clients` que `connected_clients` no crece indefinidamente bajo carga.

---

### BLOQUE 2 — ALTOS (ejecutar antes de siguiente fase)

#### Tarea 2.1 · Aplicar comparación segura en OTP (anti-timing attack)
**Archivo:** `infrastructure/api/android/auth.py`
**Acción:** Agregar import y cambiar comparación.

```python
# AGREGAR al inicio del archivo (junto a los otros imports):
import hmac

# BUSCAR (en verify_otp):
if stored_otp.decode() != request.otp:

# REEMPLAZAR POR:
if not hmac.compare_digest(stored_otp.decode(), request.otp):
```

---

#### Tarea 2.2 · Agregar token rotation en refresh
**Archivo:** `infrastructure/api/android/auth.py`
**Acción:** Al inicio de `refresh_token`, antes de generar el nuevo token, agregar el token actual a la blacklist.

```python
@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(payload: dict = Depends(get_current_user)):
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

    # ... resto del código (generar nuevo token) sin cambios ...
```

---

#### Tarea 2.3 · Ajustar `get_current_user_optional` para no silenciar errores 5xx
**Archivo:** `infrastructure/api/android/deps.py`
**Acción:** Reemplazar el `except HTTPException` genérico.

```python
# BUSCAR:
except HTTPException:
    return None

# REEMPLAZAR POR:
except HTTPException as e:
    if e.status_code in (401, 403, 404):
        return None
    raise  # Re-raise server errors (500, 503, etc.)
```

---

#### Tarea 2.4 · Validar HTTPS en `ApiClient` del APK
**Archivo:** `android_app/src/config.py`
**Acción:** Agregar validación al final del archivo.

```python
# AGREGAR al final de android_app/src/config.py:
if IS_PRODUCTION:
    if not BASE_URL:
        raise ValueError(
            "USIPIPO_API_URL o PUBLIC_URL debe estar configurada en producción."
        )
    if not BASE_URL.startswith("https://"):
        raise ValueError(
            f"BASE_URL debe usar HTTPS en producción. Actual: {BASE_URL}"
        )
```

**Archivo:** `android_app/src/services/api_client.py`
**Acción:** Agregar advertencia en `__init__` para desarrollo:

```python
def __init__(self, telegram_id: Optional[str] = None):
    self.base_url = BASE_URL
    self.telegram_id = telegram_id
    self.timeout = REQUEST_TIMEOUT
    # Advertir si no es HTTPS (solo en desarrollo)
    if self.base_url and not self.base_url.startswith("https://"):
        logger.warning(f"⚠️ BASE_URL no usa HTTPS: {self.base_url}")
```

---

#### Tarea 2.5 · Remover dominio real hardcodeado del APK
**Archivo:** `android_app/src/config.py`
**Acción:** Cambiar el fallback de `BASE_URL`.

```python
# BUSCAR:
BASE_URL = os.getenv("USIPIPO_API_URL", "https://usipipo.duckdns.org/api/v1")

# REEMPLAZAR POR:
_fallback_url = os.getenv("USIPIPO_API_URL", "")
if not _fallback_url and _public_url:
    BASE_URL = f"{_public_url.rstrip('/')}/api/v1"
elif _fallback_url:
    BASE_URL = _fallback_url
else:
    BASE_URL = ""  # Será validado en runtime
    logger.warning("BASE_URL no configurada. Configura USIPIPO_API_URL o PUBLIC_URL.")
```

---

### BLOQUE 3 — MEDIOS (resolver antes de producción)

#### Tarea 3.1 · Agregar schema `UserInToken` tipado
**Archivo:** `infrastructure/api/android/schemas.py`
**Acción:** Agregar clase y actualizar `TokenResponse`.

```python
# AGREGAR antes de class TokenResponse:
class UserInToken(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None

# MODIFICAR TokenResponse:
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInToken  # Cambiar de dict a UserInToken
```

**Nota:** Asegurarse de agregar `from typing import Optional` si no está presente.

---

#### Tarea 3.2 · Agregar tests de integración para endpoints de auth (servidor)
**Archivos a crear:**
- `tests/infrastructure/api/android/test_auth_endpoints.py`

**Contenido mínimo requerido:**

```python
"""
Tests de integración para endpoints /api/v1/auth
Requiere: Redis corriendo, DB de test configurada
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

# Tests requeridos:
# test_request_otp_user_not_found → 404
# test_request_otp_user_inactive → 403
# test_request_otp_rate_limit_ip → 429 (mock Redis incr > 5)
# test_request_otp_rate_limit_identifier → 429 (mock Redis incr > 3)
# test_verify_otp_invalid → 401 + attempts_remaining
# test_verify_otp_expired → 401 otp_expired
# test_verify_otp_too_many_attempts → 429
# test_verify_otp_success → 200 + access_token
# test_refresh_invalidates_old_token → nuevo jti, viejo en blacklist
# test_logout_blacklists_token → 401 en siguiente uso
# test_me_with_valid_token → 200 + user data
# test_me_with_revoked_token → 401
```

---

#### Tarea 3.3 · Migrar `RateLimitMiddleware` global a Redis/slowapi
**Archivo:** `infrastructure/api/middleware/rate_limit.py`
**Acción:** Reemplazar la implementación in-memory con `slowapi`.

```bash
# Agregar a requirements.txt:
slowapi>=0.1.9
```

```python
# infrastructure/api/middleware/rate_limit.py — nueva implementación:
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["60/minute"]
)
```

**Nota:** Si `slowapi` agrega demasiada complejidad por ahora, como mínimo documentar la limitación multi-worker en un comentario y asegurar que el servidor corra con un solo worker (`--workers 1`) hasta resolver esto.

---

### BLOQUE 4 — BAJOS (nice-to-have)

#### Tarea 4.1 · Implementar `SecureStorage.clear_all()` o documentar limitación
**Archivo:** `android_app/src/storage/secure_storage.py`
**Acción A (simple):** Documentar la limitación y delegar al caller.

```python
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
```

**Acción B (completa):** Mantener un índice en `PreferencesStorage` de todos los `telegram_id` usados y limpiarlos en `clear_all`.

---

#### Tarea 4.2 · Usar `JWT_EXPIRY_BUFFER_SECONDS` en `auth_service.py`
**Archivo:** `android_app/src/services/auth_service.py`
**Acción:** En `_validate_jwt_expiry`, usar el buffer de la config.

```python
# AGREGAR import al inicio:
from src.config import JWT_EXPIRY_BUFFER_SECONDS

# MODIFICAR en _validate_jwt_expiry:
current_time = int(time.time())
# Considerar expirado si queda menos de JWT_EXPIRY_BUFFER_SECONDS segundos
if exp < (current_time + JWT_EXPIRY_BUFFER_SECONDS):
    logger.debug(f"JWT próximo a expirar o expirado: exp={exp}, current={current_time}")
    return False, "JWT expirado o próximo a expirar"
```

---

## 📊 Checklist de Verificación Pre-Siguiente Fase

Antes de continuar con el módulo Dashboard u otros módulos del APK, verificar:

- [ ] **C-01**: CORS wildcard lanza error en producción
- [ ] **C-02**: Todos los `redis.from_url()` usan `async with`
- [ ] **A-01**: Comparación OTP usa `hmac.compare_digest`
- [ ] **A-02**: `RateLimitMiddleware` documentado como single-worker o migrado a Redis
- [ ] **A-03**: `refresh_token` invalida el token anterior
- [ ] **A-04**: `get_current_user_optional` re-raise errores 5xx
- [ ] **A-05**: `ApiClient` valida HTTPS en producción
- [ ] **M-01**: Dominio real removido del fallback en `config.py`
- [ ] **M-03**: `TokenResponse.user` usa schema tipado `UserInToken`
- [ ] **M-04**: Tests de integración para endpoints de auth existen y pasan

**Comando de verificación rápida:**
```bash
# Desde la raíz del proyecto
cd android_app && python -m pytest tests/ -v
cd .. && python -m pytest tests/ -k "auth" -v
```

---

## 🗂️ Resumen de Archivos Afectados

| Archivo | Tareas |
|---------|--------|
| `config.py` | 1.1 (CORS crítico) |
| `infrastructure/api/android/auth.py` | 1.2, 2.1, 2.2 |
| `infrastructure/api/android/deps.py` | 1.2, 2.3 |
| `infrastructure/api/android/schemas.py` | 3.1 |
| `infrastructure/api/middleware/rate_limit.py` | 3.3 |
| `android_app/src/config.py` | 2.4, 2.5 |
| `android_app/src/services/api_client.py` | 2.4 |
| `android_app/src/services/auth_service.py` | 4.2 |
| `android_app/src/storage/secure_storage.py` | 4.1 |
| `tests/infrastructure/api/android/` (nuevo) | 3.2 |

---

*Plan generado por auditoría de código estático — uSipipo VPN · 2026-03-14*
