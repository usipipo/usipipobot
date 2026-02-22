# uSipipo VPN Bot

[![CI](https://github.com/usipipo/usipipobot/actions/workflows/ci.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/ci.yml)
[![Docker Build](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml)
[![CodeQL](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/usipipo/usipipobot/branch/main/graph/badge.svg)](https://codecov.io/gh/usipipo/usipipobot)

Bot de Telegram para gestión de VPN (WireGuard + Outline) con sistema de pagos integrado.

## Características

- Creación de claves VPN (WireGuard y Outline)
- Sistema de planes con datos gratuitos (10GB)
- Pagos con Telegram Stars
- Paquetes de datos (10/25/50/100 GB)
- Compra de slots de claves adicionales
- Sistema de referidos con créditos canjeables
- Panel de administración

## Tech Stack

- Python 3.11+
- python-telegram-bot 21+
- SQLAlchemy 2.0 + PostgreSQL
- Clean Architecture

## Instalación Rápida

```bash
# 1. Clonar
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot

# 2. Instalar
pip install -r requirements.txt

# 3. Configurar
cp example.env .env
# Editar .env con tus credenciales

# 4. Migraciones
alembic upgrade head

# 5. Iniciar
python main.py
```

## Documentación

- [Product Requirements](./docs/PRD.md)
- [Application Flow](./docs/APPFLOW.md)
- [Technology Stack](./docs/TECHNOLOGY.md)

## Variables de Entorno Esenciales

```bash
TELEGRAM_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
DATABASE_URL=postgresql+asyncpg://...
SERVER_IP=your_server_ip
SECRET_KEY=your_secret_key
```

## Comandos del Bot

- `/start` - Iniciar bot
- `/help` - Ayuda
- `/keys` - Mis claves VPN
- `/buy` - Comprar GB o slots
- `/data` - Ver consumo de datos
- `/newkey` - Crear nueva clave
- `/referir` - Sistema de referidos y créditos
- `/admin` - Panel de administración (admins)

## Licencia

MIT License - ver [LICENSE](LICENSE)
