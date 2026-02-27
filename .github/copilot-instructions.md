# Copilot Instructions for uSipipo VPN Bot

## Project Overview

uSipipo is a Telegram bot for VPN management (WireGuard + Outline) with integrated payment system using Telegram Stars and Tron Dealer (crypto payments). Built with Clean Architecture / Hexagonal Architecture patterns.

## Tech Stack

- **Language**: Python 3.11+
- **Bot Framework**: python-telegram-bot
- **API Framework**: FastAPI
- **Database**: PostgreSQL (async with asyncpg + SQLAlchemy)
- **Migrations**: Alembic
- **DI Container**: Punq
- **Configuration**: Pydantic Settings

## Architecture

```
usipipobot/
├── domain/              # Entities, interfaces (repository contracts)
├── application/         # Services (business logic)
├── infrastructure/     # Persistence, API clients, jobs
├── telegram_bot/      # Handlers, keyboards
├── miniapp/           # Web Mini App endpoints
├── tests/             # Unit and integration tests
└── scripts/           # Setup utilities
```

## Code Style Guidelines

### Import Order (strict)
1. Standard library (`sys`, `asyncio`, `datetime`, `typing`)
2. Third-party (`pytest`, `pydantic`, `sqlalchemy`, `telegram`)
3. Local imports (domain → application → infrastructure)

```python
import sys
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from application.services.vpn_service import VpnService
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
```

### Naming Conventions
- **Files/directories**: `snake_case` (e.g., `user_repository.py`)
- **Classes/types**: `PascalCase` (e.g., `VpnService`)
- **Functions/variables**: `snake_case` (e.g., `get_user_by_id`)
- **Private methods**: prefix with `_` (e.g., `_validate_user`)
- **Interfaces**: prefix with `i` (e.g., `ikey_repository.py`)

### Type Hints (mandatory)
Use `Optional[T]`, `List[T]`, `Dict[K, V]` for collections.

```python
async def create_key(
    self, 
    telegram_id: int, 
    key_type: str, 
    key_name: str, 
    current_user_id: int
) -> VpnKey: ...
```

### Error Handling
- Use specific exceptions (`ValueError`, `TypeError`, `KeyError`)
- Include meaningful error messages
- Validate inputs with Pydantic validators

```python
try:
    user = await self.user_repo.get_by_id(user_id, current_user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
except Exception as e:
    logger.error(f"Error processing purchase: {e}")
    raise
```

### Logging
- Use emoji in logs: `logger.info(f"🔑 Key created for user {telegram_id}")`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Format: `logger.info(f"[ACTION] {detail}")`

## Domain Layer

### Entities (dataclasses)
```python
from dataclasses import dataclass
from domain.entities.user import User, UserRole

@dataclass
class VpnKey:
    id: str
    user_id: int
    key_type: KeyType
    name: str
    key_data: str
    external_id: str
    data_limit_bytes: int
    bytes_used: int = 0
    
    @property
    def is_active(self) -> bool:
        return self.status == KeyStatus.ACTIVE
```

### Interfaces (prefix with `i`)
```python
# domain/interfaces/ikey_repository.py
from abc import ABC, abstractmethod

class IKeyRepository(ABC):
    @abstractmethod
    async def save(self, key: VpnKey, current_user_id: int) -> VpnKey: ...
    
    @abstractmethod
    async def get_by_id(self, key_id: str, current_user_id: int) -> Optional[VpnKey]: ...
```

## Application Layer

### Services
```python
class VpnService:
    def __init__(
        self,
        user_repo: IUserRepository,
        key_repo: IKeyRepository,
        outline_client: OutlineClient,
        wireguard_client: WireGuardClient,
    ):
        self.user_repo = user_repo
        self.key_repo = key_repo
        self.outline_client = outline_client
        self.wireguard_client = wireguard_client
```

### Dependency Injection (Punq)
```python
from application.services.common.container import get_service
from application.services.vpn_service import VpnService

vpn_service = get_service(VpnService)
```

## Infrastructure Layer

### Repository Implementation
```python
class PostgresKeyRepository(IKeyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, key: VpnKey, current_user_id: int) -> VpnKey:
        try:
            model = KeyModel.from_entity(key)
            self.session.add(model)
            await self.session.commit()
            return key.copy(id=model.id)
        except Exception as e:
            await self.session.rollback()
            raise
```

### API Clients
```python
class OutlineClient:
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    async def create_key(self, name: str) -> dict: ...
```

## Configuration

### Settings (Pydantic)
```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str = Field(..., min_length=30)
    DATABASE_URL: str = Field(...)
    SECRET_KEY: str = Field(..., min_length=32)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )
```

Access via: `from config import settings`

## Testing

### Test Structure
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestCreateKey:
    @pytest.fixture
    def service(self, mock_key_repo, mock_user_repo, mock_outline, mock_wireguard):
        return VpnService(
            user_repo=mock_user_repo,
            key_repo=mock_key_repo,
            outline_client=mock_outline,
            wireguard_client=mock_wireguard,
        )
    
    @pytest.mark.asyncio
    async def test_create_outline_key(self, service, mock_key_repo, mock_user_repo):
        mock_user_repo.get_by_id.return_value = User(telegram_id=123, role=UserRole.USER)
        mock_outline.create_key.return_value = {"id": "key_123", "access_url": "ss://..."}
        
        result = await service.create_key(
            telegram_id=123,
            key_type="outline",
            key_name="my_key",
            current_user_id=123
        )
        
        assert result is not None
        mock_key_repo.save.assert_called_once()
```

### Running Tests
```bash
pytest                                    # all tests
pytest --cov=.                            # with coverage
pytest tests/application/services/test_vpn_service.py::TestCreateKey::test_create_outline_key  # single test
pytest -v --asyncio-mode=auto            # async verbose
```

## Key Project Patterns

### VPN Service Methods
- `create_key(telegram_id, key_type, key_name, current_user_id)` - Create WireGuard or Outline key
- `get_user_keys(telegram_id, current_user_id)` - Get all keys for user
- `delete_key(key_id, current_user_id)` - Delete a key
- `get_usage_stats(telegram_id)` - Get usage statistics

### User Entity Properties
- `user.can_create_more_keys()` - Check key limit
- `user.max_keys` - Maximum keys allowed
- `user.role` - UserRole (USER, ADMIN)

### Key Types
- `KeyType.WIREGUARD` - WireGuard VPN
- `KeyType.OUTLINE` - Outline VPN

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp example.env .env

# Run
python main.py

# Database
alembic upgrade head
alembic revision --autogenerate -m "Description"

# Linting
flake8 .
black .
mypy .
```

## Security Guidelines

- Never log sensitive data (tokens, keys, passwords)
- Validate all user inputs with Pydantic
- Use Telegram user IDs for authentication
- Store secrets in `.env` (never commit)
- Always use parameterized queries (ORM handles this)

## Common Issues

- **Database errors**: Check PostgreSQL service and credentials
- **Telegram errors**: Verify bot token and permissions
- **VPN errors**: Check WireGuard/Outline configuration
- **Config errors**: Ensure all required `.env` variables are set
