# AGENTS.md - Development Guidelines for uSipipo VPN Bot

## Build & Development Commands

### Python Environment
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # dev dependencies
```

### Testing
```bash
pytest                                    # run all tests
pytest --cov=.                            # with coverage
pytest tests/application/services/test_data_package_service.py::TestPurchasePackage::test_purchase_creates_package  # single test
pytest -v                                 # verbose
pytest -v --asyncio-mode=auto             # async tests
```

### Database Migrations
```bash
alembic upgrade head           # run all migrations
alembic revision --autogenerate -m "Description"
alembic current
alembic history
```

### Linting & Code Quality
```bash
flake8 .    # check style
black .     # format code
mypy .      # type checking
```

### Pre-commit Hooks

The project uses pre-commit hooks for automatic code formatting and quality checks.

**Setup (One-time):**
```bash
# Install pre-commit hooks
./scripts/setup-pre-commit.sh
# Or manually:
uv run pre-commit install
```

**Usage:**
```bash
# Hooks run automatically on git commit
git add .
git commit -m "feat: new feature"

# Run manually on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black --files main.py

# Update hook versions
uv run pre-commit autoupdate
```

**Hooks Configured:**

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| trailing-whitespace | Remove trailing spaces | ✅ |
| end-of-file-fixer | Ensure newline at EOF | ✅ |
| check-yaml | Validate YAML syntax | ❌ |
| check-json | Validate JSON syntax | ❌ |
| detect-private-key | Detect leaked secrets | ❌ |
| isort | Sort imports | ✅ |
| black | Format code | ✅ |
| detect-secrets | Advanced secret detection | ❌ |
| flake8 | Python linting (critical issues only) | ❌ |

### Running the Bot
```bash
python main.py                           # development
sudo systemctl start usipipo            # production
sudo journalctl -u usipipo -f           # view logs
```

## Code Style Guidelines

### Import Organization (in order)
1. Standard library (`sys`, `asyncio`, `datetime`, `typing`)
2. Third-party (`pytest`, `pydantic`, `sqlalchemy`)
3. Local imports (by layer: domain → application → infrastructure)

```python
import sys
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from application.services.data_package_service import DataPackageService
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
```

### Naming Conventions
- **Files/directories**: `snake_case` (e.g., `user_repository.py`)
- **Classes/types**: `PascalCase` (e.g., `UserService`)
- **Functions/variables**: `snake_case` (e.g., `get_user_by_id`)
- **Private methods**: prefix with `_` (e.g., `_validate_user`)
- **Interfaces**: prefix with `i` (e.g., `idata_package_repository.py`)

### Type Hints
Always use type hints. Use `Optional[T]`, `List[T]`, `Dict[K, V]`, `Union[T, U]`.

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
- Use specific exceptions (`ValueError`, `TypeError`, `KeyError`)
- Include meaningful error messages
- Validate inputs at function boundaries with Pydantic validators

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
- `DEBUG`: detailed debug info
- `INFO`: general flow
- `WARNING`: unusual conditions
- `ERROR`: recoverable errors
- `CRITICAL`: system failures
- Format: `logger.info(f"Package {name} purchased for user {user_id}")`

## Database Patterns

### Repository Pattern
- Implement interfaces in infrastructure layer
- Use async database operations
- Handle transactions with rollback on error

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

### Entity Patterns
- Use `@dataclass` for domain entities
- Include business logic in entities (keep them pure)
- Use `@property` for computed attributes

```python
@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
```

## Testing Patterns

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
        mock_user_repo.get_by_id.return_value = MagicMock(telegram_id=123)
        mock_package_repo.save.return_value = DataPackage(...)

        result = await service.purchase_package(
            user_id=123, package_type="basic",
            telegram_payment_id="pay_123", current_user_id=123
        )

        assert result is not None
        mock_package_repo.save.assert_called_once()
```

Use `AsyncMock` for async dependencies, `MagicMock` for sync mocks.

## Project Structure
```
usipipobot/
├── domain/           # entities, interfaces
├── application/      # services, ports
├── infrastructure/   # persistence, api_clients
├── telegram_bot/    # handlers, features
├── tests/
└── scripts/
```

## Security & Configuration
- Store secrets in `.env` (never commit)
- Use Pydantic Settings with `BaseSettings`
- Validate all user inputs with Pydantic
- Use Telegram user IDs for authentication

## Common Patterns

### Service Layer
```python
class DataPackageService:
    def __init__(self, package_repo: IDataPackageRepository, user_repo: IUserRepository):
        self.package_repo = package_repo
        self.user_repo = user_repo
```

### Dependency Injection (Punq)
```python
from punq import Container
container = Container()
container.register(VpnService)
vpn_service = container.resolve(VpnService)
```

## UI/UX Message Design Patterns

### Message Separator System

Use `utils/message_separators.py` for consistent visual styling across all Telegram messages.

#### Standard Separators
```python
from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
    section_separator,
)

# Module-level separator constants (define at top of file)
_SEP_HEADER = (
    MessageSeparatorBuilder()
    .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder()
    .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)
```

#### Menu Message Structure

All menu messages should follow this pattern:

```python
class FeatureMessages:
    class Menu:
        """Menu messages with visual hierarchy."""

        _HEADER = (
            f"{_SEP_HEADER}\n"
            "🔧 *SECTION TITLE*\n"
            f"{_SEP_HEADER}\n"
        )

        _DYNAMIC_INDICATOR = (
            "\n"
            "💎 *Metric:* `{value}`\n"
            f"{_SEP_DIVIDER}\n"
        )

        _TREE_STRUCTURE = (
            "\n"
            "*Section label:*\n"
            "│\n"
            "├─ 🎁 *Option 1*\n"
            "│  └─ Description\n"
            "│\n"
            "└─ 📜 *Option 2*\n"
            "   └─ Description\n"
        )

        _FOOTER = (
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Call to action:*"
        )

        @classmethod
        def main_with_data(cls, value: int = 0) -> str:
            """Generate main message with dynamic data."""
            message = cls._HEADER
            if value > 0:
                message += cls._DYNAMIC_INDICATOR.format(value=value)
            message += cls._TREE_STRUCTURE
            message += cls._FOOTER
            return message

        # Legacy fallback (without dynamic data)
        MAIN = _HEADER + _TREE_STRUCTURE + _FOOTER
```

#### Visual Style Guidelines

| Element | Style | Length | Emoji Position |
|---------|-------|--------|----------------|
| Header | `double` (`═`) | 13 (TELEGRAM_MOBILE_WIDTH) | None |
| Section divider | `simple` (`─`) | 13 | None |
| Decorative | `bold` (`━`) | 9 | `both` |
| Tree structure | Use `│ ├─ └─` symbols | - | - |

#### Style Presets
- **Modern/Tech**: Use tree structures (`│ ├─ └─`) + double headers
- **Elegant/Luxury**: Use decorative separators with emojis
- **Minimalist**: Simple separators only, no tree

### Import Order
When using separators, imports go in standard order:
```python
from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
    section_separator,
)
```

## Notes
- Clean Architecture / Hexagonal Architecture patterns
- Write tests for new functionality
- Run `pytest`, `flake8`, `black`, `mypy` before committing
- Follow existing code conventions strictly
- **For UI messages**: Always check `utils/message_separators.py` and follow patterns in `telegram_bot/features/operations/messages_operations.py`
