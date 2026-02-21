# AGENTS.md - Development Guidelines for uSipipo VPN Bot

This document contains essential information for agentic coding agents working on the uSipipo VPN Bot project.

## Project Overview

uSipipo is a Telegram bot for VPN management (WireGuard + Outline) with integrated payment system using Telegram Stars. The project follows Clean Architecture / Hexagonal Architecture patterns.

## Build & Development Commands

### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install with development dependencies (if available)
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=.

# Run specific test file
pytest tests/application/services/test_data_package_service.py

# Run specific test class
pytest tests/application/services/test_data_package_service.py::TestPurchasePackage

# Run specific test method
pytest tests/application/services/test_data_package_service.py::TestPurchasePackage::test_purchase_creates_package

# Run with verbose output
pytest -v

# Run with asyncio support
pytest -v --asyncio-mode=auto
```

### Database Migrations
```bash
# Run all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Check current version
alembic current

# Show migration history
alembic history

# Run specific migration
alembic upgrade +1
```

### Linting & Formatting
```bash
# Check code style (if available)
flake8 .

# Format code (if available)
black .

# Type checking (if available)
mypy .
```

### Running the Bot
```bash
# Development mode
python main.py

# Production with systemd
sudo systemctl start usipipo

# Check status
sudo systemctl status usipipo

# View logs
sudo journalctl -u usipipipo -f
```

## Code Style Guidelines

### Import Organization
```python
# Standard library imports first
import sys
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# Third-party imports
import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports (grouped by layer)
from domain.entities.user import User
from application.services.data_package_service import DataPackageService
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
```

### Naming Conventions

#### Files & Directories
- Use `snake_case` for files and directories
- Domain layer: `entities/`, `interfaces/`
- Application layer: `services/`, `ports/`
- Infrastructure layer: `persistence/`, `api_clients/`
- Interface files: prefix with `i` (e.g., `idata_package_repository.py`)

#### Classes & Types
- Use `PascalCase` for classes and types
- Use `StrEnum` for string-based enums
- Use `@dataclass` for entities and value objects

```python
class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"

@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
```

#### Functions & Variables
- Use `snake_case` for functions and variables
- Use descriptive names that indicate purpose
- Prefix private methods with `_`

```python
def get_user_by_id(self, user_id: int) -> Optional[User]:
    """Retrieve user by Telegram ID."""
    pass

def _validate_user_status(self, user: User) -> bool:
    """Internal validation helper."""
    pass
```

### Type Hints
- Always use type hints for function signatures
- Use `Optional[T]` for nullable values
- Use `List[T]`, `Dict[K, V]` for collections
- Use `Union[T, U]` for multiple types

```python
def purchase_package(
    self,
    user_id: int,
    package_type: str,
    telegram_payment_id: str,
    current_user_id: int
) -> DataPackage:
    pass
```

### Error Handling

#### Exception Types
- Use specific exceptions (`ValueError`, `TypeError`, `KeyError`)
- Create custom exceptions in domain layer when needed
- Always include meaningful error messages

```python
try:
    user = await self.user_repo.get_by_id(user_id, current_user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
except Exception as e:
    logger.error(f"Error processing purchase: {e}")
    raise
```

#### Validation
- Validate inputs at function boundaries
- Use Pydantic for data validation
- Provide clear error messages

```python
@validator('telegram_id')
@classmethod
def validate_telegram_id(cls, v):
    if not isinstance(v, int) or v <= 0:
        raise ValueError('telegram_id must be positive integer')
    return v
```

### Logging

#### Log Levels
- `DEBUG`: Detailed debug information
- `INFO`: General application flow
- `WARNING`: Unusual but not error conditions
- `ERROR`: Application errors that can be recovered
- `CRITICAL`: System failures

#### Log Format
```python
logger.info(f"📦 Package {option.name} purchased for user {user_id}")
logger.error(f"❌ Error creating VPN key: {str(e)}", exc_info=True)
logger.warning(f"⚠️  User {user_id} exceeded data limit")
```

### Database Patterns

#### Repository Pattern
- Implement repository interfaces in infrastructure layer
- Use async database operations
- Handle transactions properly

```python
class PostgresDataPackageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, package: DataPackage, current_user_id: int) -> DataPackage:
        try:
            model = DataPackageModel.from_entity(package)
            self.session.add(model)
            await self.session.commit()
            return package.copy(id=model.id)
        except Exception as e:
            await self.session.rollback()
            raise
```

#### Entity Patterns
- Use dataclasses for domain entities
- Include business logic methods in entities
- Keep entities pure (no database dependencies)

```python
@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
    
    def can_create_more_keys(self) -> bool:
        if self.role == UserRole.ADMIN:
            return True
        active_keys = [k for k in self.keys if k.is_active]
        return len(active_keys) < self.max_keys
```

### Testing Patterns

#### Test Structure
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

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
        mock_package_repo.save.return_value = DataPackage(
            user_id=123,
            package_type=PackageType.BASIC,
            data_limit_bytes=10 * 1024**3,
            stars_paid=50,
            expires_at=datetime.now(timezone.utc) + timedelta(days=35)
        )
        
        # Act
        result = await service.purchase_package(
            user_id=123,
            package_type="basic",
            telegram_payment_id="pay_123",
            current_user_id=123
        )
        
        # Assert
        assert result is not None
        mock_package_repo.save.assert_called_once()
```

#### Fixtures
- Use `@pytest.fixture` for test setup
- Use `AsyncMock` for async dependencies
- Use `MagicMock` for simple mocks

### Configuration Management

#### Settings Pattern
- Use Pydantic Settings for configuration
- Store sensitive data in `.env` file
- Use `SECRET_KEY` for encryption

```python
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str = Field(..., min_length=30)
    DATABASE_URL: PostgresDsn = Field(...)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

#### Environment Variables
- Use `.env` file for local development
- Never commit `.env` to version control
- Use `example.env` as template

### Dependency Injection

#### Punq Container
- Use Punq for dependency injection
- Register services in container
- Resolve dependencies in handlers

```python
from punq import Container
from application.services.vpn_service import VpnService

container = Container()
container.register(VpnService)

# Resolve
vpn_service = container.resolve(VpnService)
```

### API Design

#### FastAPI Patterns
- Use Pydantic models for request/response
- Include proper HTTP status codes
- Use dependency injection for authentication

```python
@app.post("/api/packages/purchase")
async def purchase_package(
    request: PurchasePackageRequest,
    current_user: User = Depends(get_current_user)
) -> PurchasePackageResponse:
    """Purchase data package."""
    package = await data_package_service.purchase_package(
        user_id=current_user.telegram_id,
        package_type=request.package_type,
        telegram_payment_id=request.payment_id,
        current_user_id=current_user.telegram_id
    )
    return PurchasePackageResponse.from_entity(package)
```

## Project Structure

```
usipipobot/
├── domain/                    # Domain layer
│   ├── entities/             # Domain entities
│   └── interfaces/           # Repository interfaces
├── application/              # Application layer
│   ├── services/            # Business logic
│   └── ports/               # Interface adapters
├── infrastructure/           # Infrastructure layer
│   ├── persistence/         # Database repositories
│   ├── api_clients/         # External APIs
│   └── jobs/               # Background jobs
├── telegram_bot/            # Telegram interface
│   ├── handlers/            # Command handlers
│   └── features/           # Feature modules
├── tests/                   # Test files
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

## Security Guidelines

### Authentication & Authorization
- Use Telegram user IDs for authentication
- Implement role-based access control
- Never expose sensitive data in logs

### Input Validation
- Validate all user inputs
- Use Pydantic validators
- Sanitize Markdown/HTML content

### Secrets Management
- Store secrets in environment variables
- Use `.env` for local development
- Never commit secrets to version control

## Performance Considerations

### Database Optimization
- Use connection pooling
- Implement proper indexing
- Use async database operations

### Caching
- Implement caching for frequently accessed data
- Use appropriate cache invalidation strategies
- Consider Redis for distributed caching

### Rate Limiting
- Implement rate limiting for API endpoints
- Use Telegram's built-in rate limits
- Monitor and adjust limits as needed

## Deployment Guidelines

### Production Setup
- Use systemd for service management
- Configure proper logging
- Implement health checks
- Use reverse proxy (Nginx)

### Environment Configuration
- Use different configurations for dev/staging/prod
- Implement proper error handling
- Monitor application metrics

## Common Patterns

### Service Layer Pattern
```python
class DataPackageService:
    def __init__(self, package_repo: IDataPackageRepository, user_repo: IUserRepository):
        self.package_repo = package_repo
        self.user_repo = user_repo
    
    async def purchase_package(self, user_id: int, package_type: str, telegram_payment_id: str, current_user_id: int) -> DataPackage:
        # Business logic here
        pass
```

### Repository Pattern
```python
class IDataPackageRepository:
    async def save(self, package: DataPackage, current_user_id: int) -> DataPackage
    async def get_by_user(self, user_id: int, current_user_id: int) -> List[DataPackage]
    async def update_usage(self, package_id: uuid.UUID, bytes_used: int, current_user_id: int) -> bool
```

### Handler Pattern
```python
class BaseHandler:
    def __init__(self, vpn_service: VpnService, payment_service: PaymentService):
        self.vpn_service = vpn_service
        self.payment_service = payment_service
    
    async def handle(self, update: Update, context: Context) -> None:
        # Command handling logic
        pass
```

## Troubleshooting

### Common Issues
- Database connection errors: Check PostgreSQL service and credentials
- Telegram API errors: Verify bot token and permissions
- VPN service errors: Check WireGuard/Outline configuration
- Payment errors: Verify Telegram Stars integration

### Debugging
- Use `logger.debug()` for detailed information
- Check logs in `logs/vpn_manager.log`
- Use `pytest -v` for detailed test output
- Monitor systemd service status

## Notes

- This project uses Clean Architecture with strict separation of concerns
- Always follow the established patterns and conventions
- Write tests for new functionality
- Keep the codebase maintainable and readable
- Follow security best practices at all times
## Setup Script

The project includes a comprehensive setup script for automated installation:

```bash
# Run the setup manager
./scripts/setup.sh
```

### Setup Options

| Option | Description |
|--------|-------------|
| 1 | 🐳 Install Docker (required for Outline) |
| 2 | ⚙️ Install Outline VPN Server |
| 3 | ⚙️ Install WireGuard VPN Server |
| 4 | 🗄️ Install/Configure PostgreSQL |
| 5 | 🐍 Setup Python Environment (venv + deps) |
| 6 | 🔄 Run Database Migrations (Alembic) |
| 7 | 🚀 Create Systemd Service |
| 8 | ▶️ Start Bot (main.py) |
| 9 | 🔁 Full Setup (automated 1-7) |
| 10 | 📊 System Status |

### Module Structure

```
scripts/
├── setup.sh              # Main orchestrator
├── install.sh            # Legacy VPN installer
└── modules/
    ├── common.sh         # Shared functions
    ├── database.sh       # PostgreSQL setup
    ├── python.sh         # venv + requirements
    ├── systemd.sh        # Service management
    ├── bot.sh            # Bot validation/start
    └── vpn.sh            # VPN installation
```

### Manual Installation

If you prefer manual installation:

```bash
# 1. Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# 2. Create database and user
sudo -u postgres psql -c "CREATE DATABASE usipipo;"
sudo -u postgres psql -c "CREATE USER usipipo WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE usipipo TO usipipo;"

# 3. Create virtual environment
python3 -m venv venv

# 4. Install dependencies
./venv/bin/pip install -r requirements.txt

# 5. Configure .env
cp example.env .env
# Edit .env with your settings

# 6. Run migrations
./venv/bin/alembic upgrade head

# 7. Start bot
./venv/bin/python main.py
```

### Quick Start

```bash
# Clone and setup
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot
./scripts/setup.sh

# Select option 9 for full automated setup
# Then configure TELEGRAM_TOKEN in .env
# Start: sudo systemctl start usipipo
```
