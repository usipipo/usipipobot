# 11 — API Android Layer (Nuevos Endpoints del Backend)

## Objetivo
Definir exactamente qué endpoints nuevos necesita el backend FastAPI para soportar la APK Android, sin romper la funcionalidad existente del bot de Telegram ni del mini app web.

---

## Principio de Diseño

Se crea un nuevo módulo `/api/v1/` que es completamente separado del módulo `/miniapp/` existente. Toda la autenticación del módulo `/api/v1/` usa JWT Bearer token (en lugar del `initData` de Telegram que usa el miniapp).

El módulo se agrega al servidor FastAPI existente como un nuevo router:

```
infrastructure/api/
├── server.py              ← Existente (se modifica para incluir el nuevo router)
├── middleware/            ← Existente
├── webhooks/              ← Existente
└── android/               ← NUEVO
    ├── __init__.py
    ├── router.py          ← Registra todos los sub-routers Android
    ├── auth.py            ← Endpoints de autenticación OTP + JWT
    ├── dashboard.py       ← Endpoint de resumen del dashboard
    ├── keys.py            ← Endpoints de claves VPN
    ├── payments.py        ← Endpoints de pagos Stars + USDT
    ├── user.py            ← Endpoints de perfil y cuenta
    ├── tickets.py         ← Endpoints de soporte
    ├── notifications.py   ← Endpoints de notificaciones
    └── deps.py            ← Dependencias: get_current_user, rate_limiter
```

---

## Autenticación: Todos los Endpoints Protegidos

Excepto los endpoints de auth (`/auth/*`), todos los demás requieren:

```
Header: Authorization: Bearer <jwt_token>
```

El middleware de Android (`deps.py`) valida:
1. El JWT no está expirado
2. El `jti` del JWT no está en la blacklist de Redis
3. El `client` del JWT es `"android_apk"`
4. El usuario con ese `telegram_id` existe y está activo en la DB

---

## Endpoints de Autenticación

### POST /api/v1/auth/request-otp
Solicita el envío de un código OTP al chat del usuario en Telegram.

**Request:**
```json
{
  "identifier": "@username | 123456789"
}
```

**Response 200:**
```json
{
  "message": "Código enviado a tu chat de Telegram",
  "expires_in_seconds": 300
}
```

**Response 404:**
```json
{"error": "user_not_found", "message": "Usuario no registrado en uSipipo"}
```

**Rate limit:** 3 peticiones por `identifier` por hora, 5 por IP por hora.

---

### POST /api/v1/auth/verify-otp
Verifica el código OTP y emite un JWT.

**Request:**
```json
{
  "identifier": "@username | 123456789",
  "otp": "123456"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "telegram_id": 123456789,
    "username": "juanperez",
    "full_name": "Juan Pérez",
    "photo_url": "https://..."
  }
}
```

**Response 401:**
```json
{"error": "invalid_otp", "message": "Código incorrecto", "attempts_remaining": 2}
```

**Response 429:**
```json
{"error": "too_many_attempts", "message": "Demasiados intentos. Espera 5 minutos.", "retry_after": 300}
```

---

### POST /api/v1/auth/refresh
Renueva el JWT si aún no ha expirado.

**Headers:** `Authorization: Bearer <old_jwt>`

**Response 200:**
```json
{"access_token": "eyJ...", "expires_in": 86400}
```

---

### POST /api/v1/auth/logout
Invalida el JWT actual.

**Headers:** `Authorization: Bearer <jwt>`

**Response 200:**
```json
{"message": "Sesión cerrada"}
```

---

## Endpoints del Dashboard

### GET /api/v1/dashboard/summary
Retorna todos los datos necesarios para renderizar el dashboard en una sola llamada.

**Response 200:**
```json
{
  "user": {
    "telegram_id": 123456789,
    "username": "juanperez",
    "full_name": "Juan Pérez",
    "photo_url": "...",
    "status": "active",
    "role": "user",
    "referral_credits": 12,
    "has_pending_debt": false,
    "consumption_mode_enabled": false,
    "last_login": "2026-02-15T14:00:00Z"
  },
  "data_summary": {
    "total_used_bytes": 2361393152,
    "total_limit_bytes": 5368709120,
    "source": "free_tier | package"
  },
  "active_keys": [
    {
      "id": "uuid",
      "name": "Mi iPhone",
      "key_type": "outline",
      "is_active": true,
      "used_bytes": 1288490188,
      "data_limit_bytes": 5368709120,
      "expires_at": null,
      "last_seen_at": "2026-02-15T12:00:00Z"
    }
  ],
  "active_package": {
    "package_type": "estandar",
    "data_limit_bytes": 16106127360,
    "data_used_bytes": 1288490188,
    "expires_at": "2026-03-15T00:00:00Z",
    "days_remaining": 28
  }
}
```

---

## Endpoints de Claves VPN

### GET /api/v1/keys
Lista todas las claves del usuario.

### GET /api/v1/keys/{key_id}
Detalle completo de una clave incluyendo `key_data` (string de conexión).

### GET /api/v1/keys/can-create
Verifica si el usuario puede crear más claves.

**Response:**
```json
{
  "can_create": true,
  "can_create_outline": true,
  "can_create_wireguard": false,
  "current_count": 1,
  "max_keys": 2,
  "reason": null
}
```

### POST /api/v1/keys/create
Crea una nueva clave VPN. Reutiliza `vpn_service.py` existente.

**Request:** `{"key_type": "outline", "name": "Mi iPhone"}`

### PATCH /api/v1/keys/{key_id}
Renombra una clave. `{"name": "Mi iPhone Pro"}`

### DELETE /api/v1/keys/{key_id}
Elimina una clave. Valida `can_delete_keys()` del dominio.

---

## Endpoints de Pagos

### GET /api/v1/payments/packages
Lista los paquetes disponibles con precios en Stars y USDT.

### POST /api/v1/payments/stars/create
Crea una orden de pago con Stars. Retorna el deep link para abrir Telegram.

### GET /api/v1/payments/stars/status/{order_id}
Consulta el estado de una orden Stars. Usado para polling.

### POST /api/v1/payments/crypto/create
Crea una orden USDT. Reutiliza `crypto_payment_service.py` existente.

### GET /api/v1/payments/crypto/status/{order_id}
Estado de una orden USDT. Reutiliza lógica existente.

### POST /api/v1/payments/cancel/{order_id}
Cancela una orden pendiente.

### GET /api/v1/payments/history
Historial paginado de compras. `?page=1&limit=20`

---

## Endpoints de Usuario

### GET /api/v1/user/profile
Perfil completo del usuario.

### PUT /api/v1/user/wallet
Actualiza la dirección de billetera USDT. `{"wallet_address": "TX..."}`

### GET /api/v1/user/referrals
Estadísticas del programa de referidos.

---

## Endpoints de Tickets

### GET /api/v1/tickets
Lista tickets del usuario. `?status=open|resolved|closed`

### POST /api/v1/tickets/create
Crea nuevo ticket. Reutiliza `ticket_service.py` existente.

### GET /api/v1/tickets/{ticket_id}
Conversación completa del ticket.

### POST /api/v1/tickets/{ticket_id}/reply
Responde a un ticket.

### PUT /api/v1/tickets/{ticket_id}/resolve
Marca el ticket como resuelto por el usuario.

### GET /api/v1/tickets/unread-count
Retorna el número de tickets con respuestas no leídas. Usado para badges.

---

## Endpoints de Notificaciones

### GET /api/v1/notifications/pending
Retorna notificaciones no leídas del usuario.

### POST /api/v1/notifications/ack
Marca notificaciones como leídas. `{"ids": ["uuid1", "uuid2"]}`

---

## Tabla de Rate Limits por Endpoint

| Endpoint | Límite | Ventana |
|---|---|---|
| POST /auth/request-otp | 3 por identifier | 1 hora |
| POST /auth/verify-otp | 5 por identifier | 15 min |
| POST /keys/create | 5 | 1 hora |
| POST /payments/*/create | 10 | 1 hora |
| GET /dashboard/summary | 60 | 1 min |
| GET /notifications/pending | 120 | 1 min |

---

## Nuevo Modelo de Notificaciones en la DB

Para soportar el sistema de notificaciones de la APK, se necesita una nueva tabla:

```sql
CREATE TABLE android_notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    type        VARCHAR(50) NOT NULL,
    level       VARCHAR(20) NOT NULL,
    title       VARCHAR(200) NOT NULL,
    body        TEXT NOT NULL,
    data        JSONB,
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    read_at     TIMESTAMPTZ
);

CREATE INDEX idx_android_notif_user_unread 
ON android_notifications(telegram_id, is_read) 
WHERE is_read = FALSE;
```

Un nuevo job en `infrastructure/jobs/` se encarga de generar estas notificaciones basándose en eventos del sistema (consumo de datos, vencimiento de paquetes, etc.).
