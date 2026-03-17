# uSipipo VPN - Backend API Design Document

**Created:** 2026-03-17
**Status:** Approved
**Priority:** Critical
**Estimated Effort:** 24-30 horas
**Branch:** `feature/backend-api-v1`

---

## Overview

Implementar una API REST completa bajo el prefijo `/api/v1/` con dos sub-plataformas diferenciadas:

1. **Flutter App** (`/api/v1/app/`) - API para aplicación móvil Android
2. **Mini App Web** (`/api/v1/miniapp/`) - API para Telegram Mini App (migrado desde `/miniapp/`)

La implementación incluye autenticación JWT, rate limiting diferenciado, seguridad reforzada y documentación OpenAPI.

---

## Architecture

### API Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (Port 8000)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /api/v1/app/*              → Flutter App (21 endpoints)        │
│  │                                                                │
│  ├── /auth/*                  → Autenticación JWT (6 endpoints) │
│  ├── /user/*                  → Usuario y stats (4 endpoints)   │
│  ├── /keys/*                  → VPN keys (6 endpoints)          │
│  ├── /notifications/*         → FCM (2 endpoints)               │
│  └── /payments/*              → Pagos (3 endpoints)             │
│                                                                 │
│  /api/v1/miniapp/*            → Mini App Web (19 endpoints)     │
│  │                                                                │
│  ├── /dashboard               → Dashboard                       │
│  ├── /profile                 → Perfil                          │
│  ├── /settings                → Configuración                   │
│  ├── /keys/*                  → Claves VPN                      │
│  ├── /purchase                → Compras                         │
│  ├── /api/*                   → API endpoints                   │
│  └── /admin/*                 → Admin panel                     │
│                                                                 │
│  /api/v1/webhooks/*           → Webhooks (2 endpoints)          │
│  │                                                                │
│  ├── /tron-dealer             → Pagos crypto                    │
│  └── /telegram-stars        → Pagos Telegram Stars             │
│                                                                 │
│  /health                      → Health check                    │
│  /docs                        → Swagger UI (dev only)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow

### Flutter App - Telegram Login

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Flutter │     │ Telegram │     │  Backend │     │    DB    │
│   App    │     │   API    │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │  1. init()     │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │  2. initData   │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │  3. POST /auth/telegram (initData)               │
     │────────────────────────────────>│                │
     │                │                │                │
     │                │                │  4. Validate   │
     │                │                │  initData hash │
     │                │                │                │
     │                │                │  5. Get/Create │
     │                │                │  User in DB    │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │  6. User data  │
     │                │                │<───────────────│
     │                │                │                │
     │                │                │  7. Generate   │
     │                │                │  JWT (24h)     │
     │                │                │                │
     │  8. {access_token, refresh_token, user}          │
     │<────────────────────────────────│                │
     │                │                │                │
     │  9. Store in flutter_secure_storage              │
     │───────────────>│                │                │
     │                │                │                │
```

### Flutter App - Manual Login (OTP Fallback)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Flutter │     │ Telegram │     │  Backend │     │    DB    │
│   App    │     │   Bot    │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │  1. POST /auth/manual/request (@username)        │
     │────────────────────────────────>│                │
     │                │                │                │
     │                │                │  2. Generate   │
     │                │                │  temp_code     │
     │                │                │  + OTP (6 digits)
     │                │                │                │
     │                │                │  3. Store OTP  │
     │                │                │  (5 min TTL)   │
     │                │                │───────────────>│
     │                │                │                │
     │  4. {temp_code, message}       │                │
     │<────────────────────────────────│                │
     │                │                │                │
     │                │  5. Send OTP   │                │
     │                │  via Telegram  │                │
     │                │───────────────>│                │
     │                │                │                │
     │  6. User inputs OTP in app     │                │
     │<─────────────>│                │                │
     │                │                │                │
     │  7. POST /auth/manual/validate (temp_code, OTP)  │
     │────────────────────────────────>│                │
     │                │                │                │
     │                │                │  8. Verify OTP │
     │                │                │  & temp_code   │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │  9. Valid?     │
     │                │                │<───────────────│
     │                │                │                │
     │                │                │  10. Generate  │
     │                │                │  JWT (24h)     │
     │                │                │                │
     │  11. {access_token, refresh_token}               │
     │<────────────────────────────────│                │
     │                │                │                │
```

---

## API Endpoints Specification

### Flutter App - Authentication (`/api/v1/app/auth`)

#### POST `/auth/telegram`

Login con Telegram initData.

**Request:**
```json
{
  "init_data": "query_id=AAE...&user=%7B%22id%22..."
}
```

**Response 200:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "telegram_id": 123456789,
    "username": "@usuario",
    "full_name": "Nombre Usuario",
    "is_premium": false,
    "role": "user",
    "avatar_url": "https://..."
  }
}
```

**Response 401:**
```json
{
  "success": false,
  "error": "Invalid initData: hash verification failed"
}
```

---

#### POST `/auth/manual/request`

Solicitar código OTP para login manual.

**Request:**
```json
{
  "telegram_username": "@usuario"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Código OTP enviado a tu Telegram",
  "temp_code": "tmp_abc123xyz",
  "expires_in": 300
}
```

**Response 404:**
```json
{
  "success": false,
  "error": "Usuario no encontrado. Usa el bot primero."
}
```

---

#### POST `/auth/manual/validate`

Validar código OTP.

**Request:**
```json
{
  "temp_code": "tmp_abc123xyz",
  "otp": "123456"
}
```

**Response 200:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

**Response 400:**
```json
{
  "success": false,
  "error": "Código OTP inválido o expirado"
}
```

---

#### POST `/auth/refresh`

Refresh de token de acceso.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 86400
}
```

**Response 401:**
```json
{
  "success": false,
  "error": "Token expirado o inválido"
}
```

---

#### POST `/auth/logout`

Logout y revoke de tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "success": true,
  "message": "Logout exitoso"
}
```

---

#### GET `/auth/me`

Obtener usuario actual autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "success": true,
  "user": {
    "telegram_id": 123456789,
    "username": "@usuario",
    "full_name": "Nombre Usuario",
    "is_premium": false,
    "role": "user",
    "status": "active",
    "created_at": "2026-01-15T00:00:00Z"
  }
}
```

---

### Flutter App - User (`/api/v1/app/user`)

#### GET `/user/profile`

Perfil del usuario.

**Response 200:**
```json
{
  "success": true,
  "user": {
    "telegram_id": 123456789,
    "username": "@usuario",
    "full_name": "Nombre Usuario",
    "status": "active",
    "role": "user",
    "max_keys": 2,
    "plan_type": "free",
    "referral_credits": 5,
    "loyalty_bonus_percent": 10,
    "purchase_count": 3,
    "subscription_expires_at": "2026-04-17T00:00:00Z"
  }
}
```

---

#### GET `/user/stats`

Estadísticas de consumo.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "total_keys": 2,
    "active_keys": 1,
    "total_data_gb": 50,
    "used_data_gb": 12.5,
    "remaining_data_gb": 37.5,
    "usage_percent": 25.0,
    "subscription_days_remaining": 25,
    "referral_credits": 5,
    "loyalty_bonus_percent": 10,
    "purchase_count": 3,
    "total_traffic": {
      "rx_gb": 10.2,
      "tx_gb": 2.3,
      "total_gb": 12.5
    }
  }
}
```

---

#### GET `/user/subscription`

Estado de suscripción.

**Response 200:**
```json
{
  "success": true,
  "subscription": {
    "is_premium": true,
    "plan_type": "three_months",
    "plan_name": "Trimestral",
    "stars_paid": 500,
    "starts_at": "2026-01-17T00:00:00Z",
    "expires_at": "2026-04-17T00:00:00Z",
    "days_remaining": 25,
    "is_expiring_soon": false,
    "auto_renew": false
  }
}
```

---

#### PUT `/user/profile`

Actualizar perfil.

**Request:**
```json
{
  "full_name": "Nuevo Nombre",
  "notification_enabled": true
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Perfil actualizado exitosamente"
}
```

---

### Flutter App - Keys (`/api/v1/app/keys`)

#### GET `/keys`

Listar claves VPN del usuario.

**Response 200:**
```json
{
  "success": true,
  "keys": [
    {
      "id": "key_abc123",
      "name": "VPN Casa",
      "protocol": "wireguard",
      "is_active": true,
      "status": "active",
      "data_limit_gb": 50,
      "used_data_gb": 12.5,
      "remaining_data_gb": 37.5,
      "usage_percent": 25.0,
      "created_at": "2026-01-15T00:00:00Z",
      "expires_at": "2026-04-17T00:00:00Z",
      "last_connected_at": "2026-03-17T10:30:00Z"
    }
  ]
}
```

---

#### GET `/keys/{id}`

Obtener detalle de una clave.

**Response 200:**
```json
{
  "success": true,
  "key": {
    "id": "key_abc123",
    "name": "VPN Casa",
    "protocol": "wireguard",
    "config": "[Interface]\nPrivateKey = ...",
    "qr_code_url": "/api/v1/app/keys/key_abc123/qr",
    "is_active": true,
    "data_limit_gb": 50,
    "used_data_gb": 12.5,
    "remaining_data_gb": 37.5,
    "created_at": "2026-01-15T00:00:00Z",
    "expires_at": "2026-04-17T00:00:00Z"
  }
}
```

---

#### GET `/keys/{id}/metrics`

Métricas en tiempo real de una clave.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "key_id": "key_abc123",
    "key_name": "VPN Casa",
    "protocol": "wireguard",
    "status": "active",
    "is_connected": false,
    "data_limit_gb": 50,
    "used_data_gb": 12.5,
    "remaining_data_gb": 37.5,
    "usage_percent": 25.0,
    "traffic": {
      "rx_bytes": 13421772800,
      "tx_bytes": 2147483648,
      "rx_formatted": "12.5 GB",
      "tx_formatted": "2.0 GB",
      "total_formatted": "14.5 GB"
    },
    "connection": {
      "latency_ms": 45,
      "last_connected_at": "2026-03-17T10:30:00Z",
      "connection_duration_seconds": 3600,
      "server_location": "Miami, US"
    },
    "expires_at": "2026-04-17T00:00:00Z",
    "days_until_expiry": 31,
    "created_at": "2026-01-15T00:00:00Z"
  }
}
```

---

#### POST `/keys`

Crear nueva clave VPN.

**Request:**
```json
{
  "name": "VPN Casa",
  "protocol": "wireguard"
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Clave creada exitosamente",
  "data": {
    "key_id": "key_abc123",
    "name": "VPN Casa",
    "protocol": "wireguard",
    "config": "[Interface]\nPrivateKey = ...",
    "qr_code_url": "/api/v1/app/keys/key_abc123/qr"
  }
}
```

**Response 400:**
```json
{
  "success": false,
  "error": "Has alcanzado el máximo de claves permitidas (2)"
}
```

---

#### DELETE `/keys/{id}`

Eliminar clave VPN.

**Response 200:**
```json
{
  "success": true,
  "message": "Clave eliminada exitosamente"
}
```

**Response 404:**
```json
{
  "success": false,
  "error": "Clave no encontrada"
}
```

---

#### PUT `/keys/{id}/renew`

Renovar clave (extender expiración).

**Request:**
```json
{
  "package_type": "basic"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Clave renovada exitosamente",
  "new_expires_at": "2026-05-17T00:00:00Z",
  "added_data_gb": 10
}
```

---

### Flutter App - Notifications (`/api/v1/app/notifications`)

#### POST `/notifications/fcm-token`

Registrar token FCM.

**Request:**
```json
{
  "fcm_token": "eXwDa1l2...",
  "platform": "android",
  "app_version": "1.0.0"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Token FCM registrado exitosamente"
}
```

---

#### DELETE `/notifications/fcm-token`

Eliminar token FCM (logout).

**Response 200:**
```json
{
  "success": true,
  "message": "Token FCM eliminado"
}
```

---

### Flutter App - Payments (`/api/v1/app/payments`)

#### GET `/payments/packages`

Lista de paquetes disponibles.

**Response 200:**
```json
{
  "success": true,
  "packages": [
    {
      "id": "basic",
      "name": "Básico",
      "data_gb": 10,
      "price_stars": 100,
      "price_usdt": 1.00,
      "bonus_percent": 0
    },
    {
      "id": "standard",
      "name": "Estándar",
      "data_gb": 25,
      "price_stars": 225,
      "price_usdt": 2.25,
      "bonus_percent": 10
    }
  ]
}
```

---

#### POST `/payments/create-stars-invoice`

Crear factura Telegram Stars.

**Request:**
```json
{
  "product_type": "package",
  "product_id": "basic"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Factura enviada a tu Telegram",
  "transaction_id": "txn_abc123"
}
```

---

#### POST `/payments/create-crypto-order`

Crear orden de pago crypto.

**Request:**
```json
{
  "product_type": "package",
  "product_id": "basic"
}
```

**Response 200:**
```json
{
  "success": true,
  "order_id": "order_xyz789",
  "wallet_address": "0x1234567890abcdef...",
  "amount_usdt": 1.00,
  "qr_code_url": "https://api.duckdns.org/api/v1/app/payments/qr/order_xyz789",
  "expires_in": 900
}
```

---

## Rate Limiting Configuration

### Límites por Endpoint

| Endpoint | Límite | Ventana | Key |
|----------|--------|---------|-----|
| `/auth/*` | 5 | 1 minuto | IP |
| `/app/notifications/fcm-token` | 10 | 1 hora | User ID |
| `/app/keys` (POST) | 10 | 1 hora | User ID |
| `/app/*` (resto) | 30 | 1 minuto | User ID |
| `/miniapp/*` | 60 | 1 minuto | User ID |
| `/webhooks/*` | 100 | 1 minuto | IP |

### Implementación

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        "30/minute",  # Default para Flutter App
    ],
    storage_uri="memory://",
)

# En server.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# En endpoints específicos
@router.post("/auth/telegram")
@limiter.limit("5/minute")
async def login_telegram(request: Request, ...): ...
```

---

## JWT Token Configuration

### Claims

```python
{
  "sub": "123456789",              # Telegram ID
  "username": "@usuario",           # Telegram username
  "full_name": "Nombre Usuario",    # Full name
  "role": "user",                   # user | admin
  "is_premium": false,              # Subscription status
  "iat": 1710691200,                # Issued at (timestamp)
  "exp": 1710777600,                # Expiration (24h)
  "jti": "550e8400-e29b-41d4-a716-446655440000",  # Unique ID
  "type": "access"                  # access | refresh
}
```

### Configuración

```python
# .env
JWT_SECRET_KEY=<openssl rand -hex 32>
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256
```

### Token Blacklist (Logout)

```python
# Domain entity
@dataclass
class TokenBlacklist:
    jti: str
    blacklisted_at: datetime
    expires_at: datetime
    reason: str  # logout | revoked
```

---

## Security

### Middlewares

1. **SecurityHeadersMiddleware** - Headers de seguridad HTTP
2. **RateLimitMiddleware** - Rate limiting con slowapi
3. **CORSMiddleware** - CORS configurado

### CORS Configuration

```python
CORS_ORIGINS=[
    "https://usipipo.duckdns.org",      # Mini App Web
    "https://t.me/uSipipo_Bot",          # Telegram Bot
    "https://*.telegram.org",            # Telegram CDN
]
```

### Security Headers

```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

---

## Database Schema Changes

### Nueva Tabla: `token_blacklist`

```sql
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(255) UNIQUE NOT NULL,
    blacklisted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    reason VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_token_blacklist_jti ON token_blacklist(jti);
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);
```

### Nueva Tabla: `fcm_tokens`

```sql
CREATE TABLE fcm_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(telegram_id),
    fcm_token VARCHAR(500) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    app_version VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, fcm_token)
);

CREATE INDEX idx_fcm_tokens_user ON fcm_tokens(user_id);
CREATE INDEX idx_fcm_tokens_active ON fcm_tokens(is_active);
```

### Nueva Tabla: `otp_codes`

```sql
CREATE TABLE otp_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(telegram_id),
    temp_code VARCHAR(50) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_otp_codes_temp ON otp_codes(temp_code);
CREATE INDEX idx_otp_codes_expires ON otp_codes(expires_at);
```

---

## File Structure

```
usipipobot/
├── infrastructure/
│   ├── api/
│   │   ├── server.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── rate_limit.py
│   │   │   └── security.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── app_auth.py              # NEW
│   │   │   ├── app_user.py              # NEW
│   │   │   ├── app_keys.py              # NEW
│   │   │   ├── app_notifications.py     # NEW
│   │   │   ├── app_payments.py          # NEW
│   │   │   ├── miniapp_user.py          # MIGRATED
│   │   │   ├── miniapp_keys.py          # MIGRATED
│   │   │   ├── miniapp_payments.py      # MIGRATED
│   │   │   ├── miniapp_subscriptions.py # MIGRATED
│   │   │   ├── miniapp_admin.py         # MIGRATED
│   │   │   ├── miniapp_public.py        # MIGRATED
│   │   │   └── webhooks.py
│   │   └── dependencies/
│   │       ├── __init__.py
│   │       ├── auth.py                  # NEW
│   │       └── rate_limit.py            # UPDATED
│   └── persistence/
│       ├── database.py
│       └── postgresql/
│           ├── token_blacklist_repository.py  # NEW
│           ├── fcm_token_repository.py        # NEW
│           └── otp_repository.py              # NEW
├── application/
│   └── services/
│       ├── jwt_service.py               # NEW
│       ├── telegram_auth_service.py     # NEW
│       ├── otp_service.py               # NEW
│       └── fcm_notification_service.py  # NEW
├── domain/
│   ├── entities/
│   │   ├── token_blacklist.py           # NEW
│   │   ├── fcm_token.py                 # NEW
│   │   └── otp_code.py                  # NEW
│   └── interfaces/
│       ├── i_token_blacklist_repository.py
│       ├── i_fcm_token_repository.py
│       └── i_otp_repository.py
├── utils/
│   ├── jwt.py                           # NEW
│   └── otp_generator.py                 # NEW
├── migrations/
│   └── versions/
│       └── 20260317_add_api_tables.py   # NEW
└── tests/
    ├── api/
    │   ├── test_auth_flow.py            # NEW
    │   ├── test_keys_api.py             # NEW
    │   ├── test_rate_limit.py           # NEW
    │   └── test_jwt.py                  # NEW
    └── integration/
        └── test_app_api_integration.py  # NEW
```

---

## Implementation Plan

### Phase 1: Infrastructure Base (4 horas)

- [ ] Crear estructura de directorios `infrastructure/api/routes/`
- [ ] Crear `infrastructure/api/dependencies/`
- [ ] Implementar JWT Service (`application/services/jwt_service.py`)
- [ ] Implementar Token Blacklist (`domain/entities/token_blacklist.py`)
- [ ] Crear repositorios (TokenBlacklist, FCMToken, OTP)
- [ ] Configurar Rate Limiting (slowapi)
- [ ] Actualizar middlewares

### Phase 2: Autenticación Flutter App (6 horas)

- [ ] Endpoint POST `/auth/telegram`
- [ ] Endpoint POST `/auth/manual/request`
- [ ] Endpoint POST `/auth/manual/validate`
- [ ] Endpoint POST `/auth/refresh`
- [ ] Endpoint POST `/auth/logout`
- [ ] Endpoint GET `/auth/me`
- [ ] Tests de autenticación

### Phase 3: Usuario y Keys (8 horas)

- [ ] Endpoints `/user/*` (profile, stats, subscription)
- [ ] Endpoints `/keys/*` (list, get, metrics, create, delete, renew)
- [ ] Métricas en tiempo real (integración con WireGuard/Outline)
- [ ] Tests de usuario y keys

### Phase 4: Notificaciones y Pagos (4 horas)

- [ ] Endpoints FCM token
- [ ] Endpoints de pagos (packages, stars, crypto)
- [ ] Tests de notificaciones y pagos

### Phase 5: Migración Mini App (3 horas)

- [ ] Mover rutas desde `miniapp/` a `infrastructure/api/routes/`
- [ ] Actualizar imports y referencias
- [ ] Actualizar templates HTML
- [ ] Testing de migración

### Phase 6: Testing y Documentación (3 horas)

- [ ] Tests de integración
- [ ] Documentación OpenAPI (Swagger)
- [ ] Scripts de testing
- [ ] Actualizar QWEN.md y AGENTS.md

---

## Environment Variables

```bash
# ========================
# JWT Configuration
# ========================
JWT_SECRET_KEY=<openssl rand -hex 32>
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

# ========================
# Rate Limiting
# ========================
API_RATE_LIMIT=30
MINIAPP_RATE_LIMIT=60
AUTH_RATE_LIMIT=5
FCM_RATE_LIMIT_PER_HOUR=10

# ========================
# FCM Configuration
# ========================
FIREBASE_PROJECT_ID=usipipo-vpn-app
FIREBASE_CREDENTIALS_PATH=/app/serviceAccountKey.json
FCM_NOTIFICATION_CHANNEL_ID=usipipo_vpn_channel

# ========================
# OTP Configuration
# ========================
OTP_EXPIRE_MINUTES=5
OTP_LENGTH=6

# ========================
# CORS
# ========================
CORS_ORIGINS=["https://usipipo.duckdns.org","https://t.me/uSipipo_Bot"]
```

---

## Testing Strategy

### Unit Tests

- JWT token generation/validation
- OTP generation/validation
- Rate limiting
- Repository methods

### Integration Tests

- Auth flow (Telegram + OTP)
- CRUD de keys
- Payment flow
- FCM registration

### End-to-End Tests

- Login → Create key → View stats → Logout
- OTP request → OTP validate → Purchase package

---

## Success Metrics

- ✅ 21 endpoints Flutter App implementados
- ✅ 19 endpoints Mini App migrados
- ✅ JWT authentication funcionando
- ✅ Rate limiting activo
- ✅ Tests passing (90%+ coverage)
- ✅ Documentación OpenAPI completa
- ✅ 0 errores en producción post-deploy

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| JWT secret leak | Critical | Rotar secret, revoke todos los tokens |
| Rate limit too strict | High | Monitorear logs, ajustar límites |
| Mini App migration breaks frontend | High | Testing exhaustivo, rollback plan |
| FCM tokens not working | Medium | Verificar Firebase config, logs |
| OTP not delivered | Medium | Fallback a Telegram login directo |

---

**Document Owner:** uSipipo Team
**Last Updated:** 2026-03-17
**Next Review:** After implementation completion
**Related Docs:**
- `docs/plans/2026-03-17-miniapp-api-migration.md`
- `docs/plans/2026-03-17-usipipo-vpn-implementation-plan.md`
