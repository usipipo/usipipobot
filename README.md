# uSipipo VPN Manager

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat&logo=postgresql&logoColor=white)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python Telegram Bot](https://img.shields.io/badge/python--telegram--bot-21+-2CA5E0?style=flat&logo=telegram&logoColor=white)
[![CodeQL](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml)
[![Docker Build](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml)
[![Tests](https://img.shields.io/badge/Tests-42%20passing-success?style=flat)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-purple?style=flat)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat&logo=fastapi&logoColor=white)

> Telegram Bot + Mini App para gestión de claves VPN (WireGuard & Outline) con pagos integrados.

[Español](#español) · [English](#english) · [Características](#características) · [Arquitectura](#arquitectura) · [Instalación](#instalación) · [Configuración](#configuración)

---

</div>

## 🌐 Español

### Descripción

**uSipipo VPN Manager** es una solución completa para la gestión de servidores VPN personales. Combina un bot de Telegram con una Mini App web para ofrecer una experiencia de usuario moderna e intuitiva.

**Tecnologías soportadas:**
- 🔐 **WireGuard** - Protocolo VPN moderno y rápido
- 📊 **Outline** - VPN basada en Shadowsocks

**Métodos de pago:**
- ⭐ **Telegram Stars** - Pagos directos en Telegram
- ₿ **Criptomonedas** - USDT/BSC vía TronDealer

---

### Características

| Categoría | Funcionalidades |
|-----------|-----------------|
| **Gestión de Claves** | Crear, eliminar, renovar claves VPN (WireGuard + Outline) |
| **Planes** | Plan gratuito (5GB/2 claves), compra de slots adicionales |
| **Pagos** | Telegram Stars, USDT (TRC20/BSC), código QR (EIP-681) |
| **Facturación** | Sistema por consumo (pay-as-you-go), ciclos de 30 días |
| **Bonos & Referidos** | Bono de bienvenida, bonos de lealtad, 5GB por referido |
| **Mini App** | Panel web con diseño cyberpunk, compra de GB, gestión de perfil |
| **Soporte** | Sistema de tickets integrado |
| **Administración** | Panel admin, estadísticas, limpieza automática de claves |

---

### Arquitectura

```
usipipobot/
├── domain/                    # Entidades y contratos del dominio
│   ├── entities/              # @dataclass: User, VPNKey, Ticket, etc.
│   └── interfaces/            # Repository interfaces (IUserRepository, etc.)
├── application/               # Servicios de aplicación (casos de uso)
│   └── services/              # VPN, Wallet, Billing, Referral, etc.
├── infrastructure/            # Implementaciones
│   ├── persistence/           # PostgreSQL + SQLAlchemy 2.0 async
│   ├── api/                   # FastAPI server (webhooks)
│   └── api_clients/           # Outline, WireGuard, TronDealer clients
├── telegram_bot/              # Interfaz de Telegram
│   ├── handlers/              # Handlers de comandos y callbacks
│   ├── keyboards/             # Inline keyboards
│   └── messages/              # Plantillas de mensajes
├── miniapp/                   # Telegram Mini App Web
│   ├── routes_*.py            # Endpoints FastAPI
│   ├── templates/             # Jinja2 templates
│   └── services/              # Servicios Mini App
├── utils/                     # Utilidades compartidas
├── jobs/                      # Background jobs (cleanup, sync)
├── tests/                     # Tests (pytest + pytest-asyncio)
└── scripts/                   # Scripts de administración
```

**Patrones utilizados:**
- ✅ Clean Architecture / Hexagonal Architecture
- ✅ Repository Pattern
- ✅ Dependency Injection (punq)
- ✅ Async/Await (todas las operaciones de BD)
- ✅ Pydantic v2 para validación

---

### Tech Stack

| Componente | Tecnología | Versión |
|------------|------------|---------|
| **Lenguaje** | Python | 3.11+ |
| **Bot Framework** | python-telegram-bot | 21+ |
| **Database** | PostgreSQL + SQLAlchemy | 2.0 async |
| **API Server** | FastAPI + Uvicorn | 0.109+ |
| **Validación** | Pydantic | v2 |
| **DI Container** | punq | latest |
| **HTTP Clients** | httpx, aiohttp | latest |
| **Auth** | PyJWT + cryptography | latest |
| **Logging** | Loguru | latest |
| **Testing** | pytest + pytest-asyncio | latest |
| **Migrations** | Alembic | latest |

---

### Instalación

#### Requisitos Previos

- Python 3.11+
- PostgreSQL 15+
- Linux (Ubuntu 22.04+ recomendado)

#### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp example.env .env
# Editar .env con tus credenciales

# 5. Ejecutar migraciones
alembic upgrade head

# 6. Iniciar el bot
python main.py
```

#### Instalación con Docker

```bash
# Variables necesarias en .env
# TELEGRAM_TOKEN, ADMIN_ID, DATABASE_URL, SERVER_IP, SECRET_KEY

# Build y ejecución
docker build -t usipipo-bot .
docker run -d --name usipipo \
  --env-file .env \
  -v ./data:/app/data \
  usipipo-bot
```

---

### Configuración

#### Variables de Entorno Requeridas

```bash
# ========================
# APLICACIÓN
# ========================
PROJECT_NAME="uSipipo VPN Manager"
APP_ENV=production              # development | production
SECRET_KEY=your_secret_key      # openssl rand -hex 32

# ========================
# TELEGRAM
# ========================
TELEGRAM_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
BOT_USERNAME=usipipo_bot

# ========================
# DATABASE
# ========================
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# ========================
# SERVIDOR VPN
# ========================
SERVER_IP=your_server_ip
SERVER_IPV4=your_ipv4

# ========================
# WIREGUARD (opcional)
# ========================
WG_INTERFACE=wg0
WG_SERVER_PORT=51820
WG_SERVER_PUBKEY=your_public_key
WG_SERVER_PRIVKEY=your_private_key
WG_ENDPOINT=your_server_ip:51820

# ========================
# OUTLINE (opcional)
# ========================
OUTLINE_API_URL=https://outline-server:port

# ========================
# CRYPTO PAYMENTS
# ========================
TRON_DEALER_API_KEY=td_xxx
TRON_DEALER_WEBHOOK_SECRET=your_webhook_secret  # openssl rand -hex 32
TRON_DEALER_SWEEP_WALLET=your_bsc_wallet

# ========================
# DUCKDNS (opcional)
# ========================
DUCKDNS_DOMAIN=your_domain
DUCKDNS_TOKEN=your_duckdns_token
```

---

### Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar bot y mostrar menú principal |
| `/keys` | Ver mis claves VPN activas |
| `/newkey` | Crear nueva clave (WireGuard u Outline) |
| `/buy` | Comprar GB adicionales o slots |
| `/data` | Ver consumo de datos |
| `/referir` | Invitar amigos y ganar GB gratis |
| `/profile` | Ver perfil y estadísticas |
| `/tickets` | Ver mis tickets de soporte |
| `/admin` | Panel de administración (solo admins) |

---

### Mini App Web

Accede a la Mini App desde el botón en el menú del bot para:

- 🖥️ **Dashboard** - Resumen de claves y consumo
- 📊 **Estadísticas** - Gráficos de uso de datos
- 💳 **Comprar** - Comprar GB o slots adicionales
- 👤 **Perfil** - Historial de transacciones
- ⚙️ **Configuración** - Preferencias y soporte

---

### Documentación Adicional

| Documento | Descripción |
|-----------|-------------|
| [PRD](./docs/PRD.md) | Requisitos del producto |
| [APPFLOW](./docs/APPFLOW.md) | Flujo de la aplicación |
| [TECHNOLOGY](./docs/TECHNOLOGY.md) | Stack tecnológico detallado |
| [Database Schema](./docs/database_schema_v3.md) | Esquema de base de datos |
| [AGENTS.md](./AGENTS.md) | Guía para desarrollo agéntico |

---

### Testing

```bash
# Ejecutar todos los tests
pytest -v

# Con cobertura
pytest --cov=. -v

# Test específico
pytest tests/path/to/test.py::TestClass::test_method
```

---

### Scripts de Administración

```bash
./scripts/setup.sh              # Setup completo del servidor
./scripts/run_migrations.sh     # Ejecutar migraciones de BD
./scripts/wg_server.sh          # Gestión de servidor WireGuard
./scripts/ol_server.sh          # Gestión de servidor Outline
./scripts/check_ram_cleanup.sh  # Verificar limpieza de RAM
```

---

### Contribuir

1. Fork el repositorio
2. Crear una rama (`git checkout -b feature/amazing-feature`)
3. Commit los cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abrir un Pull Request

---

### Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

<div align="center">

## 🇺🇸 English

</div>

### Overview

**uSipipo VPN Manager** is a complete VPN key management solution combining a Telegram bot with a modern web Mini App.

**Supported Technologies:**
- 🔐 **WireGuard** - Modern, fast VPN protocol
- 📊 **Outline** - Shadowsocks-based VPN

**Payment Methods:**
- ⭐ **Telegram Stars** - Direct payments in Telegram
- ₿ **Cryptocurrencies** - USDT/BSC via TronDealer

### Quick Start

```bash
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp example.env .env  # Configure your .env
alembic upgrade head
python main.py
```

### Tech Stack

- Python 3.11+ • PostgreSQL 15+ • FastAPI • SQLAlchemy 2.0 (async)
- python-telegram-bot 21+ • Pydantic v2 • Clean Architecture

---

<div align="center">

**⭐ Star este repositorio si te fue útil**

Made with ❤️ by [uSipipo](https://github.com/usipipo)

</div>