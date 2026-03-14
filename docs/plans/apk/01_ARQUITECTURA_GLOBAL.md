# 01 — Arquitectura Global del Ecosistema uSipipo

## Visión General

uSipipo es un ecosistema de tres clientes que comparten un único backend. La APK Android es el tercer cliente, diseñado para usuarios que prefieren una experiencia nativa sobre Telegram.

---

## Diagrama del Ecosistema Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTES EXTERNOS                            │
│                                                                     │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────────┐ │
│  │ Telegram Bot │   │  Mini App Web    │   │   APK Android       │ │
│  │  (aiogram)   │   │ (Flask + Jinja2) │   │  (Kivy + KivyMD)   │ │
│  │              │   │                  │   │                     │ │
│  │  Comandos    │   │  HTML/CSS/JS     │   │  Python nativo      │ │
│  │  Callbacks   │   │  cyberpunk.css   │   │  Tema cyberpunk     │ │
│  └──────┬───────┘   └────────┬─────────┘   └──────────┬──────────┘ │
│         │                   │                          │            │
└─────────┼───────────────────┼──────────────────────────┼────────────┘
          │                   │                          │
          │  Telegram API     │  HTTP/REST + JWT         │  HTTP/REST + JWT
          │  (webhooks)       │  + initData Telegram     │  + OTP Telegram
          │                   │                          │
┌─────────▼───────────────────▼──────────────────────────▼────────────┐
│                     BACKEND CENTRAL                                  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              FastAPI (infrastructure/api/server.py)             │ │
│  │                                                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │ │
│  │  │   /miniapp   │  │  /webhooks   │  │    /api/v1 ← NUEVO   │ │ │
│  │  │   (existente)│  │  (TronDealer)│  │    (para APK Android) │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              APPLICATION LAYER (Services)                       │ │
│  │  vpn_service · data_package_service · crypto_payment_service   │ │
│  │  user_profile_service · referral_service · ticket_service      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              DOMAIN LAYER (Entities)                            │ │
│  │  User · VpnKey · DataPackage · CryptoOrder · Ticket            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              INFRASTRUCTURE LAYER                               │ │
│  │  PostgreSQL · Outline API · WireGuard API · TronDealer API     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Diagrama de Flujo de Autenticación APK

```
 Usuario APK                 Backend /api/v1              Bot Telegram
     │                            │                            │
     │── Ingresa telegram_id ────►│                            │
     │                            │── Genera OTP (6 dígitos)  │
     │                            │── Guarda OTP en Redis ───►│
     │                            │   (TTL: 5 min)             │
     │                            │                            │── Envía OTP al
     │                            │                            │   chat del usuario
     │◄─ "Código enviado" ────────│                            │
     │                            │                            │
     │── Ingresa código OTP ─────►│                            │
     │                            │── Valida OTP vs Redis      │
     │                            │── Si válido: genera JWT    │
     │◄─ JWT Token (24h) ─────────│                            │
     │                            │                            │
     │ [Almacena JWT en           │                            │
     │  EncryptedStorage local]   │                            │
     │                            │                            │
     │── Peticiones con JWT ─────►│                            │
     │   Authorization: Bearer    │── Valida JWT en cada req.  │
     │                            │── Extrae telegram_id       │
     │◄─ Datos del usuario ───────│                            │
```

---

## Diagrama de Flujo de Compra con Telegram Stars

```
 Usuario APK              Backend /api/v1         Bot Telegram      Telegram API
     │                        │                       │                  │
     │── Selecciona paquete ─►│                       │                  │
     │◄─ Deep Link generado ──│                       │                  │
     │   tg://resolve?...     │                       │                  │
     │                        │                       │                  │
     │── Abre Telegram ──────────────────────────────►│                  │
     │   (Deep Link al bot)   │                       │── Muestra invoice│
     │                        │                       │   con Stars ────►│
     │                        │                       │◄─ Pago exitoso ──│
     │                        │◄─ Webhook de pago ────│                  │
     │                        │── Activa paquete       │                  │
     │                        │── Marca orden pagada   │                  │
     │── Polling cada 3s ────►│                       │                  │
     │◄─ Estado: "PAGADO" ────│                       │                  │
     │                        │                       │                  │
     │ [Muestra confirmación] │                       │                  │
```

---

## Diagrama de Flujo de Compra con USDT (TronDealer)

```
 Usuario APK           Backend /api/v1         TronDealer API      Blockchain TRON
     │                      │                       │                    │
     │── Pago USDT ────────►│                       │                    │
     │                      │── Crea crypto_order    │                    │
     │                      │── Asigna wallet ──────►│                    │
     │◄─ Dirección wallet ──│◄─ wallet_address ──────│                    │
     │   + monto exacto     │                       │                    │
     │   + QR code          │                       │                    │
     │                      │                       │                    │
     │ [Usuario envía USDT  │                       │                    │
     │  desde su billetera] │                       │◄── TX detectada ───│
     │                      │◄── Webhook TronDealer──│                    │
     │                      │── Valida firma webhook │                    │
     │                      │── Confirma pago        │                    │
     │                      │── Activa paquete       │                    │
     │── Polling cada 5s ──►│                       │                    │
     │◄─ Estado: "PAGADO" ──│                       │                    │
```

---

## Diagrama de Flujo de Creación de Clave VPN

```
 Usuario APK              Backend /api/v1        Outline/WireGuard Server
     │                        │                          │
     │── POST /keys/create ──►│                          │
     │   {type: "outline"}    │── Valida saldo usuario   │
     │                        │── Valida max_keys        │
     │                        │── Llama VpnService ─────►│
     │                        │                          │── Crea clave
     │                        │◄─ {key_data, extern_id} ─│
     │                        │── Guarda en PostgreSQL   │
     │◄─ {key_data, qr_url} ──│                          │
     │                        │                          │
     │ [Muestra pantalla con  │                          │
     │  key string + QR code] │                          │
```

---

## Principios de Diseño del Ecosistema

### 1. Backend como Única Fuente de Verdad
Ningún cliente almacena datos de negocio de forma permanente. La APK solo guarda el JWT en almacenamiento encriptado local. Todo lo demás se consulta al backend en tiempo real.

### 2. Stateless por Diseño
Cada petición de la APK al backend es independiente. El JWT lleva toda la información de identidad necesaria. No existen sesiones del lado del servidor.

### 3. Compatibilidad Total con Infraestructura Existente
La APK no requiere cambios en la lógica de negocio existente. Solo requiere un nuevo módulo de rutas REST (`/api/v1`) en el servidor FastAPI y un módulo de autenticación OTP.

### 4. Seguridad por Capas
- **Capa APK:** Almacenamiento encriptado, certificate pinning, ofuscación de código
- **Capa Transporte:** HTTPS obligatorio, JWT con expiración corta
- **Capa Backend:** Rate limiting, validación estricta, firma de webhooks
- **Capa Base de Datos:** Consultas parametrizadas, sin SQL dinámico

---

## Dependencias entre Módulos APK

```
[Auth] ──────────────────────────────────────────┐
   │                                              │
   ├──► [Dashboard] ──► [Claves VPN]             │
   │         │              │                    │
   │         │              ├──► [Crear Clave]   │  Todos requieren
   │         │              └──► [Detalle Clave] │  JWT válido del
   │         │                                   │  módulo Auth
   │         ├──► [Compras] ──► [Stars]          │
   │         │              └──► [USDT]          │
   │         │                                   │
   │         ├──► [Perfil/Cuenta]                │
   │         │                                   │
   │         └──► [Tickets/Soporte]              │
   │                                             │
   └─────────────────────────────────────────────┘
```
