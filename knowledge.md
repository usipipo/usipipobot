# Project Knowledge

## What is this?
uSipipo VPN Bot — a Telegram bot + Mini App for managing VPN keys (WireGuard & Outline) with integrated payments (Telegram Stars, crypto via TronDealer). Python 3.11+, Clean Architecture.

## Key directories
- `domain/` — entities (`@dataclass`) and repository interfaces (`i*.py`)
- `application/services/` — use-case services; DI via `punq` (container in `application/services/common/container.py`)
- `infrastructure/` — persistence (PostgreSQL/SQLAlchemy 2.0 async), API clients, FastAPI webhooks, background jobs
- `telegram_bot/` — handlers organized by feature (`features/<feature>/`), each with `handlers_*.py`, `keyboards_*.py`, `messages_*.py`
- `miniapp/` — Telegram Mini App (FastAPI + Jinja2 templates, cyberpunk CSS)
- `utils/` — logging (loguru), message separators, QR generator, spinner, telegram helpers
- `tests/` — pytest with async support (`asyncio_mode = auto`)
- `scripts/` — setup, migration, server management shell scripts
- `migrations/` — Alembic migration versions

## Commands

### Setup
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp example.env .env  # then edit .env
alembic upgrade head
```

### Run
```bash
python main.py                    # starts bot + FastAPI server (threaded)
```

### Test
```bash
pytest                            # all tests (verbose, short traceback by default via pytest.ini)
pytest --cov=.                    # with coverage
pytest tests/path/to/test.py::TestClass::test_method  # single test
```

### Lint / Format / Typecheck
```bash
flake8 .
black .
mypy .
```

### Database migrations
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic current
alembic history
```

## Tech stack
| Component        | Technology                              |
|------------------|-----------------------------------------|
| Language         | Python 3.11+                            |
| Bot framework    | python-telegram-bot 21+ (job-queue)     |
| Database         | PostgreSQL + SQLAlchemy 2.0 (async) + asyncpg |
| Migrations       | Alembic                                 |
| Validation       | Pydantic v2 + pydantic-settings         |
| DI container     | punq                                    |
| HTTP clients     | httpx, aiohttp                          |
| API server       | FastAPI + uvicorn                       |
| Auth             | PyJWT + cryptography                    |
| Logging          | loguru                                  |
| Testing          | pytest + pytest-asyncio                 |

## Conventions
- **Architecture**: Clean/Hexagonal — domain has no infra deps; services consume repository interfaces
- **Naming**: files `snake_case`, classes `PascalCase`, interfaces prefixed `i` (e.g. `iuser_repository.py`)
- **Imports**: stdlib → third-party → local (domain → application → infrastructure)
- **Type hints**: always required; use `Optional[T]`, `List[T]`, `Dict[K, V]`
- **Async**: all DB operations are async; use `AsyncMock` in tests
- **Config**: all settings via `pydantic-settings` in `config.py`, loaded from `.env`
- **Telegram messages**: use `utils/message_separators.py` with `MessageSeparatorBuilder`; follow tree-structure patterns in `messages_*.py` files
- **Handler pattern**: feature handlers use mixin classes; registered via `handler_initializer.py`
- **Testing pattern**: class-based tests with `@pytest.fixture` for service setup, `@pytest.mark.asyncio` for async

## Gotchas
- `package.json` is empty — this is a Python-only project, no npm/node
- The bot and FastAPI server run in the same process (API in a daemon thread)
- `TRON_DEALER_API_KEY` and `TRON_DEALER_WEBHOOK_SECRET` are **required** in production
- Alembic reads DB URL from `.env` via `migrations/env.py`, not from `alembic.ini`
- Primary language for docs/comments is Spanish
