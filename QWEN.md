# uSipipo VPN Manager - Project Context

## Project Overview

**uSipipo VPN Manager** is a comprehensive VPN management ecosystem with two integrated platforms:

1. **Telegram Bot** - Primary interface for commands and notifications
2. **Telegram Mini App** - Cyberpunk-styled web dashboard

Both platforms share the same backend infrastructure for managing WireGuard and Outline VPN keys with integrated payment processing.

### Core Features

| Platform | Features |
|----------|----------|
| **Telegram Bot** | Commands, notifications, quick actions, support tickets |
| **Mini App Web** | Dashboard, profile, settings, payment flows, statistics |

### Unified Features
- **VPN Key Management**: Create, delete, renew WireGuard and Outline VPN keys
- **Payment Integration**: Telegram Stars and cryptocurrency (USDT/BSC via TronDealer)
- **Billing System**: Pay-as-you-go consumption model with 30-day cycles
- **Referral Program**: Bonus system with 5GB rewards for successful referrals
- **Support System**: Integrated ticket system across all platforms
- **Admin Panel**: Statistics, user management, and automated key cleanup

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.13+ |
| **Package Manager** | uv | latest |
| **Bot Framework** | python-telegram-bot | 21.10 |
| **Database** | PostgreSQL + SQLAlchemy | 2.0 async |
| **API Server** | FastAPI + Uvicorn | 0.135.1 |
| **Validation** | Pydantic | v2.12 |
| **DI Container** | punq | 0.7.0 |
| **HTTP Clients** | httpx, aiohttp | latest |
| **Security** | PyJWT, cryptography | latest |
| **Logging** | Loguru | latest |
| **Testing** | pytest + pytest-asyncio | latest |
| **Migrations** | Alembic | latest |

## Architecture

The project follows **Clean Architecture / Hexagonal Architecture** patterns:

```
usipipobot/
├── domain/                    # Domain entities and interfaces (shared)
│   ├── entities/              # @dataclass: User, VpnKey, DataPackage, Ticket, etc.
│   └── interfaces/            # Repository interfaces (IUserRepository, etc.)
├── application/               # Application services (use cases, shared)
│   └── services/              # VpnService, WalletService, BillingService, etc.
├── infrastructure/            # Infrastructure implementations
│   ├── persistence/           # PostgreSQL + SQLAlchemy 2.0 async
│   ├── api/                   # FastAPI server (webhooks, Mini App API)
│   ├── api_clients/           # Outline, WireGuard, TronDealer clients
│   ├── jobs/                  # Background jobs (cleanup, sync)
│   └── dns/                   # DuckDNS service
├── telegram_bot/              # Telegram bot interface
│   ├── handlers/              # Command and callback handlers
│   ├── keyboards/             # Inline keyboards
│   └── features/              # Feature-specific operations
├── miniapp/                   # Telegram Mini App Web
│   ├── routes_*.py            # FastAPI endpoints
│   ├── templates/             # Jinja2 templates
│   └── services/              # Mini App services
├── utils/                     # Shared utilities
├── tests/                     # Backend test suite (pytest)
├── migrations/                # Alembic database migrations
└── scripts/                   # Administration scripts
```

### Key Architectural Patterns

1. **Repository Pattern**: Domain interfaces implemented in infrastructure layer
2. **Dependency Injection**: Punq container for service resolution
3. **Async/Await**: All database operations use SQLAlchemy async
4. **Service Layer**: Business logic encapsulated in application services
5. **Entity Pattern**: Domain entities use `@dataclass` with business logic
6. **Multi-Platform API**: RESTful API serving Bot and Mini App

## Building and Running

### Prerequisites
- Python 3.13+
- PostgreSQL 15+
- Linux (Ubuntu 22.04+ recommended)
- uv package manager

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### Backend Setup (All Platforms)

```bash
# Clone repository
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot

# Create virtual environment and install dependencies with uv
uv sync --dev

# Configure environment
cp example.env .env
# Edit .env with your credentials

# Run database migrations
uv run alembic upgrade head

# Start the bot (includes API server for Mini App)
uv run python main.py
```

### Docker Deployment

```bash
# Required .env variables:
# TELEGRAM_TOKEN, ADMIN_ID, DATABASE_URL, SERVER_IP, SECRET_KEY

# Build and run
docker build -t usipipo-bot .
docker run -d --name usipipo \
  --env-file .env \
  -v ./data:/app/data \
  usipipo-bot
```

### Testing

```bash
# Backend tests (406+ passing)
uv run pytest

# With coverage
uv run pytest --cov=. -v

# Single test
uv run pytest tests/path/to/test.py::TestClass::test_method

# Async tests
uv run pytest -v --asyncio-mode=auto
```

### CI/CD Workflows

```bash
# View workflow runs
gh run list

# Watch a specific run
gh run watch <run-id>
```

### Code Quality

```bash
flake8 .        # Style checking
black .         # Code formatting
mypy .          # Type checking
```

### Database Migrations

```bash
uv run alembic upgrade head              # Run all migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic current                   # Current migration
uv run alembic history                   # Migration history
```

## Configuration

### Required Environment Variables

```bash
# ========================
# APPLICATION
# ========================
PROJECT_NAME="uSipipo VPN Manager"
APP_ENV=production              # development | production
SECRET_KEY=<openssl rand -hex 32>

# ========================
# TELEGRAM
# ========================
TELEGRAM_TOKEN=<bot_token>
ADMIN_ID=<telegram_user_id>
BOT_USERNAME=usipipo_bot

# ========================
# DATABASE
# ========================
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# ========================
# SERVER
# ========================
SERVER_IP=<public_ip>
SERVER_IPV4=<ipv4_address>

# ========================
# WIREGUARD (optional)
# ========================
WG_INTERFACE=wg0
WG_SERVER_PORT=51820
WG_SERVER_PUBKEY=<public_key>
WG_SERVER_PRIVKEY=<private_key>
WG_ENDPOINT=<ip>:51820
WG_PATH=/etc/wireguard
WG_CLIENT_DNS_1=1.1.1.1

# ========================
# OUTLINE (optional)
# ========================
OUTLINE_API_URL=https://outline-server:port

# ========================
# CRYPTO PAYMENTS
# ========================
TRON_DEALER_API_KEY=td_<api_key>
TRON_DEALER_WEBHOOK_SECRET=<openssl rand -hex 32>
TRON_DEALER_SWEEP_WALLET=<bsc_wallet>

# ========================
# DUCKDNS (optional)
# ========================
DUCKDNS_DOMAIN=<domain>
DUCKDNS_TOKEN=<token>
PUBLIC_URL=https://<domain>.duckdns.org

# ========================
# MINI APP
# ========================
MINIAPP_ENABLED=true
MINIAPP_URL=https://your-domain.com
```

### Import Organization

```python
# 1. Standard library
import sys
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# 2. Third-party
import pytest
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local imports (by layer: domain → application → infrastructure)
from domain.entities.user import User
from application.services.data_package_service import DataPackageService
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files/directories | `snake_case` | `user_repository.py` |
| Classes/types | `PascalCase` | `UserService` |
| Functions/variables | `snake_case` | `get_user_by_id` |
| Private methods | `_` prefix | `_validate_user` |
| Interfaces | `I` prefix | `IDataPackageRepository` |

### Type Hints

Always use type hints with `Optional[T]`, `List[T]`, `Dict[K, V]`, `Union[T, ...]`:

```python
def purchase_package(
    self,
    user_id: int,
    package_type: str,
    telegram_payment_id: str,
    current_user_id: int
) -> DataPackage: ...
```

### Error Handling

```python
try:
    user = await self.user_repo.get_by_id(user_id, current_user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
except Exception as e:
    logger.error(f"Error processing purchase: {e}")
    raise
```

### Logging Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General application flow
- `WARNING`: Unusual conditions
- `ERROR`: Recoverable errors
- `CRITICAL`: System failures

### Testing Patterns

```python
class TestPurchasePackage:
    @pytest.fixture
    def service(self, mock_package_repo, mock_user_repo):
        return DataPackageService(
            package_repo=mock_package_repo,
            user_repo=mock_user_repo
        )

    @pytest.mark.asyncio
    async def test_purchase_creates_package(self, service, mock_package_repo, mock_user_repo):
        # Arrange
        mock_user_repo.get_by_id.return_value = MagicMock(telegram_id=123)
        mock_package_repo.save.return_value = DataPackage(...)

        # Act
        result = await service.purchase_package(
            user_id=123, package_type="basic",
            telegram_payment_id="pay_123", current_user_id=123
        )

        # Assert
        assert result is not None
        mock_package_repo.save.assert_called_once()
```

- Use `AsyncMock` for async dependencies
- Use `MagicMock` for synchronous mocks
- Follow Arrange-Act-Assert pattern

## Database Schema

### Core Entities

| Entity | Description |
|--------|-------------|
| `User` | Telegram users with referral tracking and bonus credits |
| `VpnKey` | WireGuard/Outline keys with usage tracking |
| `DataPackage` | Purchased data packages (10GB-100GB tiers) |
| `CryptoOrder` | Cryptocurrency payment orders |
| `Ticket` | Support tickets |
| `TicketMessage` | Ticket conversation messages |
| `ConsumptionInvoice` | Pay-as-you-go consumption invoices |
| `Balance` | User balance tracking |

### Key Enums

- `UserStatus`: active, suspended, blocked
- `UserRole`: user, admin
- `KeyType`: wireguard, outline
- `PackageType`: basic (10GB), standard (25GB), advanced (50GB), premium (100GB)
- `CryptoOrderStatus`: pending, completed, expired, failed

## Key Services

| Service | Responsibility |
|---------|----------------|
| `VpnService` | VPN key lifecycle management |
| `DataPackageService` | Package purchase and activation |
| `ReferralService` | Referral tracking and bonuses |
| `CryptoPaymentService` | Cryptocurrency payment processing |
| `ConsumptionBillingService` | Pay-as-you-go billing |
| `TicketService` | Support ticket management |
| `AdminService` | Administrative operations |
| `WalletManagementService` | User wallet management |
| `UserBonusService` | Bonus and loyalty rewards |

## Background Jobs

| Job | Interval | Purpose |
|-----|----------|---------|
| `sync_vpn_usage_job` | 30 min | Sync VPN key usage statistics |
| `key_cleanup_job` | 1 hour | Clean up inactive keys |
| `expire_packages_job` | 24 hours | Expire data packages |
| `expire_crypto_orders_job` | 1 min | Expire pending crypto orders |
| `memory_cleanup_job` | 10 min | Auto cleanup RAM when threshold exceeded |
| `ghost_key_cleanup_job` | Weekly | Clean up ghost keys |

## API Endpoints

### Webhooks
- `POST /api/v1/webhooks/tron-dealer` - TronDealer payment notifications

### Mini App
- `GET /miniapp/` - Mini App entry point
- `GET /miniapp/dashboard` - User dashboard
- `GET /miniapp/profile` - User profile
- `GET /miniapp/settings` - Settings page

## Common Operations

### Dependency Injection

```python
from application.services.common.container import get_service
from application.services.vpn_service import VpnService

vpn_service = get_service(VpnService)
```

### Database Session Management

```python
from infrastructure.persistence.database import get_session_factory

session_factory = get_session_factory()
async with session_factory() as session:
    # Use session for database operations
    repo = PostgresUserRepository(session)
    user = await repo.get_by_id(123)
```

## UI/UX Message Patterns

The project uses a consistent visual styling system for Telegram messages via `utils/message_separators.py`:

```python
from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
)

_SEP_HEADER = (
    MessageSeparatorBuilder()
    .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
```

Message structure follows a hierarchy with headers, dividers, tree structures, and footers. See `AGENTS.md` for detailed patterns.

## Security Considerations

1. **Secrets Management**: All secrets in `.env` (never commit)
2. **Input Validation**: Pydantic validators on all user inputs
3. **Authentication**: Telegram: User IDs for bot/miniapp
4. **JWT Tokens**: Configurable expiration
5. **CORS**: Configurable origins for web endpoints
6. **Rate Limiting**: Per-user and API rate limits
7. **Webhook Security**: HMAC signature verification for TronDealer webhooks

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Database connection errors | Verify `DATABASE_URL` format and PostgreSQL is running |
| Bot not responding | Check `TELEGRAM_TOKEN` and bot is not blocked |
| WireGuard keys fail | Verify `WG_SERVER_PUBKEY` and `WG_SERVER_PRIVKEY` |
| Crypto payments fail | Check TronDealer webhook secret and API key |
| Memory cleanup fails | Ensure sudo permissions for `/proc/sys/vm/drop_caches` |

### Logs

```bash
# View application logs
tail -f logs/vpn_manager.log

# Production (systemd)
sudo journalctl -u usipipo -f
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot and show main menu |
| `/keys` | View active VPN keys |
| `/newkey` | Create new VPN key |
| `/buy` | Purchase GB or slots |
| `/data` | View data consumption |
| `/referir` | Invite friends and earn GB |
| `/profile` | View profile and stats |
| `/tickets` | View support tickets |
| `/admin` | Admin panel (admins only) |

## Additional Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Main project documentation |
| `AGENTS.md` | Development guidelines and conventions |
| `docs/PRD.md` | Product requirements |
| `docs/APPFLOW.md` | Application flow diagrams |
| `docs/TECHNOLOGY.md` | Technology stack details |
| `docs/database_schema_v3.md` | Detailed database schema |
| `CHANGELOG.md` | Version history |

## Project Status

| Component | Version | Status |
|-----------|---------|--------|
| **Backend** | 3.9.0 | Production-ready |
| **Mini App** | 3.9.0 | Production-ready |

- **Tests**: 406+ passing (backend)
- **Architecture**: Clean Architecture / Hexagonal
- **Ecosystem**: Bot + Mini App integrated
- **CI/CD**: GitHub Actions con workflows separados por componente

### CI/CD Workflows Configurados

| Workflow | Trigger | Paths Filter | Tiempo Est. |
|----------|---------|--------------|-------------|
| `ci.yml` | push/PR a main | `domain/**`, `application/**`, etc. | ~5 min |
| `codeql.yml` | push/PR a main, weekly | `domain/**`, `application/**`, etc. | ~3 min |
| `docker.yml` | push/PR a main, tags | `Dockerfile`, backend paths | ~3 min |
