# uSipipo VPN Manager - Project Context

## Project Overview

**uSipipo VPN Manager** is a comprehensive VPN management solution combining a Telegram Bot with a Telegram Mini App web interface. It enables users to manage WireGuard and Outline VPN keys with integrated payment processing.

### Core Features
- **VPN Key Management**: Create, delete, renew WireGuard and Outline VPN keys
- **Payment Integration**: Telegram Stars and cryptocurrency (USDT/BSC via TronDealer)
- **Billing System**: Pay-as-you-go consumption model with 30-day cycles
- **Referral Program**: Bonus system with 5GB rewards for successful referrals
- **Mini App**: Cyberpunk-styled web dashboard for key management and purchases
- **Support System**: Integrated ticket system for user support
- **Admin Panel**: Statistics, user management, and automated key cleanup

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.11+ |
| **Bot Framework** | python-telegram-bot | 21.10 |
| **Database** | PostgreSQL + SQLAlchemy | 2.0 async |
| **API Server** | FastAPI + Uvicorn | 0.135.1 |
| **Validation** | Pydantic | v2 |
| **DI Container** | punq | latest |
| **HTTP Clients** | httpx, aiohttp | latest |
| **Security** | PyJWT, cryptography | latest |
| **Logging** | Loguru | latest |
| **Testing** | pytest + pytest-asyncio | latest |
| **Migrations** | Alembic | latest |

## Architecture

The project follows **Clean Architecture / Hexagonal Architecture** patterns:

```
usipipobot/
├── domain/                    # Domain entities and interfaces
│   ├── entities/              # @dataclass: User, VpnKey, DataPackage, Ticket, etc.
│   └── interfaces/            # Repository interfaces (IUserRepository, etc.)
├── application/               # Application services (use cases)
│   └── services/              # VpnService, WalletService, BillingService, etc.
├── infrastructure/            # Infrastructure implementations
│   ├── persistence/           # PostgreSQL + SQLAlchemy 2.0 async
│   ├── api/                   # FastAPI server (webhooks, Mini App)
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
├── tests/                     # Test suite (pytest)
├── migrations/                # Alembic database migrations
└── scripts/                   # Administration scripts
```

### Key Architectural Patterns

1. **Repository Pattern**: Domain interfaces implemented in infrastructure layer
2. **Dependency Injection**: Punq container for service resolution
3. **Async/Await**: All database operations use SQLAlchemy async
4. **Service Layer**: Business logic encapsulated in application services
5. **Entity Pattern**: Domain entities use `@dataclass` with business logic

## Building and Running

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Linux (Ubuntu 22.04+ recommended)

### Development Setup

```bash
# Clone repository
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp example.env .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start the bot
python main.py
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
# Run all tests
pytest -v

# With coverage
pytest --cov=. -v

# Single test
pytest tests/path/to/test.py::TestClass::test_method

# Async tests
pytest -v --asyncio-mode=auto
```

### Code Quality

```bash
flake8 .        # Style checking
black .         # Code formatting
mypy .          # Type checking
```

### Database Migrations

```bash
alembic upgrade head              # Run all migrations
alembic revision --autogenerate -m "Description"
alembic current                   # Current migration
alembic history                   # Migration history
```

## Configuration

### Required Environment Variables

```bash
# Application
PROJECT_NAME="uSipipo VPN Manager"
APP_ENV=production
SECRET_KEY=<openssl rand -hex 32>

# Telegram
TELEGRAM_TOKEN=<bot_token>
ADMIN_ID=<telegram_user_id>
BOT_USERNAME=usipipo_bot

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Server
SERVER_IP=<public_ip>
SERVER_IPV4=<ipv4_address>

# WireGuard (optional)
WG_SERVER_PUBKEY=<public_key>
WG_SERVER_PRIVKEY=<private_key>
WG_ENDPOINT=<ip>:51820

# Outline (optional)
OUTLINE_API_URL=https://outline-server:port

# Crypto Payments
TRON_DEALER_API_KEY=td_<api_key>
TRON_DEALER_WEBHOOK_SECRET=<openssl rand -hex 32>
TRON_DEALER_SWEEP_WALLET=<bsc_wallet>

# DuckDNS (optional)
DUCKDNS_DOMAIN=<domain>
DUCKDNS_TOKEN=<token>
PUBLIC_URL=https://<domain>.duckdns.org
```

## Development Conventions

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

## Background Jobs

| Job | Interval | Purpose |
|-----|----------|---------|
| `sync_vpn_usage_job` | 30 min | Sync VPN key usage statistics |
| `key_cleanup_job` | 1 hour | Clean up inactive keys |
| `expire_packages_job` | 24 hours | Expire data packages |
| `expire_crypto_orders_job` | 1 min | Expire pending crypto orders |
| `memory_cleanup_job` | 10 min | Auto cleanup RAM when threshold exceeded |

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
3. **Authentication**: Telegram user IDs for authentication
4. **JWT Tokens**: For API authentication with configurable expiration
5. **CORS**: Configurable origins for web endpoints
6. **Rate Limiting**: Per-user and API rate limits

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

## Additional Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Main project documentation |
| `AGENTS.md` | Development guidelines and conventions |
| `docs/PRD.md` | Product requirements |
| `docs/APPFLOW.md` | Application flow diagrams |
| `docs/database_schema_v3.md` | Detailed database schema |
| `CHANGELOG.md` | Version history |
| `tracks.md` | Active development tracks |

## Project Status

- **Version**: 3.4.0 (Bonus & Referral System)
- **Tests**: 385+ passing
- **Architecture**: Clean Architecture / Hexagonal
- **Status**: Production-ready
