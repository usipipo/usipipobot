# uSipipo VPN Bot

Bot de Telegram para gestión de VPN (WireGuard + Outline) con sistema de pagos integrado.

## Características

- Creación de claves VPN (WireGuard y Outline)
- Sistema de planes (Gratis y VIP)
- Pagos con Telegram Stars
- Programa de referidos
- Panel de administración
- Juegos Play & Earn

## Tech Stack

- Python 3.9+
- python-telegram-bot 21+
- SQLAlchemy 2.0 + PostgreSQL
- FastAPI
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
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
```

## Comandos del Bot

- `/start` - Iniciar bot
- `/help` - Ayuda
- `/profile` - Ver perfil
- `/keys` - Mis claves VPN
- `/buy` - Comprar GB
- `/ref` - Programa referidos

## Licencia

MIT License - ver [LICENSE](LICENSE)
