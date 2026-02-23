# uSipipo VPN Bot

[![CI](https://github.com/usipipo/usipipobot/actions/workflows/ci.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/ci.yml)
[![Docker Build](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml)
[![CodeQL](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml)

Bot de Telegram para gestión de VPN (WireGuard + Outline) con sistema de pagos integrado usando Telegram Stars.

## Características

- Creación de claves VPN (WireGuard y Outline)
- Sistema de planes con datos gratuitos (10GB)
- Pagos con Telegram Stars
- Paquetes de datos (10/25/50/100 GB)
- Compra de slots de claves adicionales
- Sistema de referidos con créditos canjeables
- Panel de administración
- Sistema de tickets de soporte

## Arquitectura

```
usipipobot/
├── domain/           # Entidades y contratos del dominio
├── application/      # Servicios de aplicación (casos de uso)
├── infrastructure/   # Implementaciones (DB, APIs, Jobs)
├── telegram_bot/     # Interfaz de Telegram (handlers, keyboards)
├── utils/            # Utilidades compartidas
└── tests/            # Tests unitarios e integración
```

**Patrones utilizados:**
- Clean Architecture / Hexagonal Architecture
- Repository Pattern
- Dependency Injection (punq)

## Tech Stack

| Componente | Tecnología |
|------------|------------|
| Lenguaje | Python 3.11+ |
| Bot Framework | python-telegram-bot 21+ |
| Database | PostgreSQL + SQLAlchemy 2.0 (async) |
| Migraciones | Alembic |
| Validación | Pydantic v2 |
| DI Container | punq |
| Logging | Loguru |

## Instalación Rápida

```bash
# 1. Clonar
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot

# 2. Setup automatizado
./scripts/setup.sh

# 3. Configurar variables de entorno
cp example.env .env
# Editar .env con tus credenciales

# 4. Iniciar
python main.py
```

### Instalación Manual

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar
cp example.env .env

# Migraciones
alembic upgrade head

# Iniciar
python main.py
```

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [PRD](./docs/PRD.md) | Requisitos del producto |
| [APPFLOW](./docs/APPFLOW.md) | Flujo de la aplicación |
| [TECHNOLOGY](./docs/TECHNOLOGY.md) | Stack tecnológico |
| [AGENTS.md](./AGENTS.md) | Guía para desarrollo agéntico |
| [Database Schema](./docs/database_schema_v3.md) | Esquema de base de datos |

## Variables de Entorno

```bash
# Requeridas
TELEGRAM_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SERVER_IP=your_server_ip
SECRET_KEY=your_secret_key

# VPN Servers
OUTLINE_API_URL=https://outline-server:port
OUTLINE_CERT=cert_sha256
WIREGUARD_INTERFACE=wg0
```

## Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar bot |
| `/help` | Ayuda y soporte |
| `/keys` | Ver mis claves VPN |
| `/buy` | Comprar GB o slots |
| `/data` | Ver consumo de datos |
| `/newkey` | Crear nueva clave |
| `/referir` | Sistema de referidos |
| `/admin` | Panel de administración |

## Testing

```bash
# Ejecutar todos los tests
pytest -v

# Con cobertura
pytest --cov=. -v
```

## Scripts de Administración

```bash
./scripts/setup.sh              # Setup completo
./scripts/run_migrations.sh     # Ejecutar migraciones
./scripts/wg_server.sh          # Gestión WireGuard
./scripts/ol_server.sh          # Gestión Outline
```

## Licencia

MIT License - ver [LICENSE](LICENSE)
