# Help UX Improvement & Ticket System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix help message display bug, improve UX, and implement ticket system for user support

**Architecture:** Feature-based modules for help and tickets following Clean Architecture. New domain entity for tickets, repository pattern, and Telegram handlers.

**Tech Stack:** Python, Telegram Bot API, SQLAlchemy, PostgreSQL, MarkdownV2

---

## Issues Found

### Issue 1: Critical Bug - Missing parse_mode in help callback
- **Location:** `telegram_bot/features/user_management/handlers_user_management.py:188-191`
- **Problem:** The `help` callback doesn't have `parse_mode="Markdown"` causing formatting issues
- **Impact:** Users see raw Markdown instead of formatted text

### Issue 2: Poor UX in Help Message
- **Problem:** Help message is basic and doesn't provide actionable support
- **Impact:** Users don't know how to contact support or find answers

### Issue 3: Missing Ticket System
- **Problem:** No way for users to contact admin for support
- **Impact:** Users cannot report issues or get help

### Issue 4: Missing FAQ
- **Problem:** No frequently asked questions section
- **Impact:** Users repeatedly ask same questions

---

## Task 1: Fix parse_mode Bug in Help Handler

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:188-191`

**Step 1: Add parse_mode to help callback**

Change from:
```python
elif callback_data == "help":
    await query.edit_message_text(
        text=UserManagementMessages.Welcome.HELP_TEXT,
        reply_markup=MainMenuKeyboard.main_menu(),
    )
```

To:
```python
elif callback_data == "help":
    await query.edit_message_text(
        text=UserManagementMessages.Welcome.HELP_TEXT,
        reply_markup=MainMenuKeyboard.main_menu(),
        parse_mode="Markdown",
    )
```

**Step 2: Verify fix works**

Run: `pytest tests/ -v -k help`
Expected: All tests pass

**Step 3: Commit**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "fix: add missing parse_mode in help callback"
```

---

## Task 2: Redesign Help Message with FAQ and Support Options

**Files:**
- Modify: `telegram_bot/features/user_management/messages_user_management.py`
- Modify: `telegram_bot/features/user_management/keyboards_user_management.py`
- Modify: `telegram_bot/features/user_management/handlers_user_management.py`

**Step 1: Create improved help messages**

In `messages_user_management.py`, add to `Welcome` class:

```python
HELP_TEXT = (
    "❓ *Centro de Ayuda de uSipipo*\n\n"
    "📱 *Guía Rápida:*\n"
    "🔑 _Mis Claves VPN_ - Ver todas tus claves activas\n"
    "➕ _Nueva Clave_ - Crear una nueva clave VPN\n"
    "📦 _Comprar GB_ - Adquirir más datos\n"
    "💾 _Mis Datos_ - Ver tu consumo actual\n\n"
    "💡 *Consejos:*\n"
    "• Puedes crear hasta 2 claves gratis\n"
    "• Cada clave tiene 10GB de datos\n"
    "• Compra más GB cuando los necesites"
)

FAQ_TEXT = (
    "📚 *Preguntas Frecuentes*\n\n"
    "❓ *¿Cómo configuro mi VPN?*\n"
    "Descarga la app WireGuard o Outline, importa tu clave y conecta.\n\n"
    "❓ *¿Cuántos dispositivos puedo usar?*\n"
    "Puedes crear hasta 2 claves gratuitas. Cada clave = 1 dispositivo.\n\n"
    "❓ *¿Qué pasa si agoto mis datos?*\n"
    "Compra más GB desde el menú principal con Telegram Stars.\n\n"
    "❓ *¿Cómo funciona el programa de referidos?*\n"
    "Comparte tu código de referido. Cuando alguien se registra, ambos reciben créditos.\n\n"
    "❓ *¿Necesitas más ayuda?*\n"
    "Crea un ticket de soporte y te responderemos pronto."
)

SUPPORT_PROMPT = (
    "🎫 *Soporte Técnico*\n\n"
    "¿Tienes un problema que no puedes resolver?\n\n"
    "Crea un ticket y nuestro equipo te ayudará:\n"
    "• Problemas de conexión\n"
    "• Errores en pagos\n"
    "• Solicitudes especiales\n"
    "• Reporte de bugs\n\n"
    "_Respuesta en menos de 24 horas_"
)

TICKET_CREATED = (
    "✅ *Ticket Creado*\n\n"
    "Tu ticket #{ticket_id} ha sido enviado.\n\n"
    "Te responderemos lo antes posible.\n\n"
    "Estado: 🟡 Pendiente"
)
```

**Step 2: Create help navigation keyboard**

In `keyboards_user_management.py`, add:

```python
@staticmethod
def help_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📚 FAQ", callback_data="help_faq"),
            InlineKeyboardButton("🎫 Soporte", callback_data="help_support"),
        ],
        [InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

@staticmethod
def support_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎫 Crear Ticket", callback_data="create_ticket")],
        [InlineKeyboardButton("📋 Mis Tickets", callback_data="list_my_tickets")],
        [InlineKeyboardButton("🔙 Volver", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

@staticmethod
def back_to_help() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Ayuda", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 3: Update help callback handler**

In `handlers_user_management.py`, update the `help` callback section:

```python
elif callback_data == "help":
    await query.edit_message_text(
        text=UserManagementMessages.Welcome.HELP_TEXT,
        reply_markup=UserManagementKeyboards.help_menu(),
        parse_mode="Markdown",
    )

elif callback_data == "help_faq":
    await query.edit_message_text(
        text=UserManagementMessages.Welcome.FAQ_TEXT,
        reply_markup=UserManagementKeyboards.back_to_help(),
        parse_mode="Markdown",
    )

elif callback_data == "help_support":
    await query.edit_message_text(
        text=UserManagementMessages.Welcome.SUPPORT_PROMPT,
        reply_markup=UserManagementKeyboards.support_menu(),
        parse_mode="Markdown",
    )
```

**Step 4: Update callback pattern**

In `get_user_callback_handlers()`, update the pattern:

```python
CallbackQueryHandler(
    handler.main_menu_callback,
    pattern="^(show_keys|buy_data|show_usage|help|help_faq|help_support|admin_panel|show_history|create_ticket|list_my_tickets)$",
),
```

**Step 5: Commit**

```bash
git add telegram_bot/features/user_management/
git commit -m "feat: improve help UX with FAQ and support menu"
```

---

## Task 3: Create Ticket Domain Entity

**Files:**
- Create: `domain/entities/ticket.py`
- Modify: `domain/entities/__init__.py`

**Step 1: Create Ticket entity**

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Ticket:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: int = 0
    subject: str = ""
    message: str = ""
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    response: Optional[str] = None

    @property
    def is_open(self) -> bool:
        return self.status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS)

    def add_response(self, response: str, admin_id: int) -> None:
        self.response = response
        self.resolved_by = admin_id
        self.resolved_at = datetime.now(timezone.utc)
        self.status = TicketStatus.RESOLVED
        self.updated_at = datetime.now(timezone.utc)

    def close(self) -> None:
        self.status = TicketStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)
```

**Step 2: Update __init__.py**

Add to exports:
```python
from .ticket import Ticket, TicketStatus, TicketPriority
```

**Step 3: Commit**

```bash
git add domain/entities/
git commit -m "feat: add Ticket domain entity"
```

---

## Task 4: Create Ticket Database Model

**Files:**
- Create: `infrastructure/persistence/postgresql/models/ticket.py`
- Modify: `infrastructure/persistence/postgresql/models/__init__.py`

**Step 1: Create TicketModel**

```python
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class TicketModel(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, server_default="open")
    priority: Mapped[str] = mapped_column(String, server_default="medium")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

**Step 2: Update __init__.py**

```python
from .ticket import TicketModel
```

**Step 3: Commit**

```bash
git add infrastructure/persistence/postgresql/models/
git commit -m "feat: add TicketModel database model"
```

---

## Task 5: Create Alembic Migration for Tickets

**Files:**
- Create: Migration file via alembic

**Step 1: Create migration**

Run:
```bash
alembic revision --autogenerate -m "add tickets table"
```

**Step 2: Run migration**

Run:
```bash
alembic upgrade head
```

**Step 3: Commit**

```bash
git add migrations/
git commit -m "feat: add tickets table migration"
```

---

## Task 6: Create Ticket Repository

**Files:**
- Create: `domain/interfaces/iticket_repository.py`
- Create: `infrastructure/persistence/postgresql/ticket_repository.py`

**Step 1: Create interface**

```python
from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from domain.entities.ticket import Ticket


class ITicketRepository(ABC):
    @abstractmethod
    async def save(self, ticket: Ticket, current_user_id: int) -> Ticket:
        pass

    @abstractmethod
    async def get_by_id(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int, current_user_id: int) -> List[Ticket]:
        pass

    @abstractmethod
    async def get_all_open(self, current_user_id: int) -> List[Ticket]:
        pass

    @abstractmethod
    async def update(self, ticket: Ticket, current_user_id: int) -> Ticket:
        pass
```

**Step 2: Create repository implementation**

```python
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from domain.interfaces.iticket_repository import ITicketRepository
from infrastructure.persistence.postgresql.models.ticket import TicketModel


class PostgresTicketRepository(ITicketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ticket: Ticket, current_user_id: int) -> Ticket:
        model = TicketModel(
            user_id=ticket.user_id,
            subject=ticket.subject,
            message=ticket.message,
            status=ticket.status.value,
            priority=ticket.priority.value,
        )
        self.session.add(model)
        await self.session.commit()
        return Ticket(
            id=model.id,
            user_id=model.user_id,
            subject=model.subject,
            message=model.message,
            status=TicketStatus(model.status),
            priority=TicketPriority(model.priority),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        result = await self.session.execute(
            select(TicketModel).where(TicketModel.id == ticket_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(self, user_id: int, current_user_id: int) -> List[Ticket]:
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.user_id == user_id)
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_all_open(self, current_user_id: int) -> List[Ticket]:
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.status.in_(["open", "in_progress"]))
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, ticket: Ticket, current_user_id: int) -> Ticket:
        result = await self.session.execute(
            select(TicketModel).where(TicketModel.id == ticket.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = ticket.status.value
            model.response = ticket.response
            model.resolved_by = ticket.resolved_by
            model.resolved_at = ticket.resolved_at
            await self.session.commit()
        return ticket

    def _to_entity(self, model: TicketModel) -> Ticket:
        return Ticket(
            id=model.id,
            user_id=model.user_id,
            subject=model.subject,
            message=model.message,
            status=TicketStatus(model.status),
            priority=TicketPriority(model.priority),
            created_at=model.created_at,
            updated_at=model.updated_at,
            resolved_at=model.resolved_at,
            resolved_by=model.resolved_by,
            response=model.response,
        )
```

**Step 3: Commit**

```bash
git add domain/interfaces/ infrastructure/persistence/postgresql/
git commit -m "feat: add ticket repository"
```

---

## Task 7: Create Ticket Service

**Files:**
- Create: `application/services/ticket_service.py`

**Step 1: Create service**

```python
from typing import List, Optional
import uuid

from domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from domain.interfaces.iticket_repository import ITicketRepository
from utils.logger import logger


class TicketService:
    def __init__(self, ticket_repo: ITicketRepository):
        self.ticket_repo = ticket_repo

    async def create_ticket(
        self,
        user_id: int,
        subject: str,
        message: str,
        current_user_id: int,
        priority: str = "medium",
    ) -> Ticket:
        ticket = Ticket(
            user_id=user_id,
            subject=subject,
            message=message,
            priority=TicketPriority(priority),
        )
        saved = await self.ticket_repo.save(ticket, current_user_id)
        logger.info(f"Ticket {saved.id} created by user {user_id}")
        return saved

    async def get_user_tickets(self, user_id: int, current_user_id: int) -> List[Ticket]:
        return await self.ticket_repo.get_by_user(user_id, current_user_id)

    async def get_ticket(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        return await self.ticket_repo.get_by_id(ticket_id, current_user_id)

    async def get_all_open_tickets(self, current_user_id: int) -> List[Ticket]:
        return await self.ticket_repo.get_all_open(current_user_id)

    async def respond_to_ticket(
        self,
        ticket_id: uuid.UUID,
        response: str,
        admin_id: int,
        current_user_id: int,
    ) -> Ticket:
        ticket = await self.ticket_repo.get_by_id(ticket_id, current_user_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        ticket.add_response(response, admin_id)
        return await self.ticket_repo.update(ticket, current_user_id)
```

**Step 2: Commit**

```bash
git add application/services/ticket_service.py
git commit -m "feat: add TicketService for ticket management"
```

---

## Task 8: Create Ticket Feature Module

**Files:**
- Create: `telegram_bot/features/tickets/__init__.py`
- Create: `telegram_bot/features/tickets/messages_tickets.py`
- Create: `telegram_bot/features/tickets/keyboards_tickets.py`
- Create: `telegram_bot/features/tickets/handlers_tickets.py`

**Step 1: Create messages**

```python
class TicketMessages:
    class User:
        CREATE_PROMPT = (
            "🎫 *Crear Ticket de Soporte*\n\n"
            "Escribe tu mensaje describing el problema:\n\n"
            "_Ejemplo: No puedo conectar mi VPN desde mi teléfono_"
        )
        
        CREATED = (
            "✅ *Ticket Creado*\n\n"
            "ID: #{ticket_id}\n"
            "Asunto: {subject}\n"
            "Estado: 🟡 Pendiente\n\n"
            "Te responderemos pronto."
        )
        
        MY_TICKETS_HEADER = "📋 *Mis Tickets*\n\n"
        
        NO_TICKETS = (
            "📋 *Mis Tickets*\n\n"
            "No tienes tickets abiertos.\n\n"
            "¿Necesitas ayuda? Crea uno nuevo."
        )
        
        TICKET_DETAIL = (
            "🎫 *Ticket #{ticket_id}*\n\n"
            "📝 *Asunto:* {subject}\n"
            "📊 *Estado:* {status}\n"
            "📅 *Creado:* {created_at}\n\n"
            "💬 *Mensaje:*\n{message}\n\n"
            "{response_section}"
        )
        
        RESPONSE_SECTION = (
            "✅ *Respuesta del soporte:*\n"
            "{response}\n\n"
            "_Respondido el {resolved_at}_"
        )

    class Admin:
        LIST_HEADER = "🔧 *Tickets Pendientes*\n\n"
        
        NO_PENDING = (
            "🔧 *Tickets Pendientes*\n\n"
            "No hay tickets pendientes."
        )
        
        TICKET_DETAIL = (
            "🎫 *Ticket #{ticket_id}*\n\n"
            "👤 *Usuario:* {user_id}\n"
            "📝 *Asunto:* {subject}\n"
            "📊 *Estado:* {status}\n"
            "📅 *Creado:* {created_at}\n\n"
            "💬 *Mensaje:*\n{message}\n\n"
            "{response_section}"
        )

    class Error:
        NOT_FOUND = "❌ Ticket no encontrado."
        CREATE_FAILED = "❌ Error al crear el ticket. Intenta de nuevo."
```

**Step 2: Create keyboards**

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import uuid


class TicketKeyboards:
    @staticmethod
    def ticket_actions(ticket_id: uuid.UUID) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✅ Responder", callback_data=f"ticket_respond_{ticket_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin_tickets")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def user_ticket_actions(ticket_id: uuid.UUID) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a Mis Tickets", callback_data="list_my_tickets")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_support() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a Soporte", callback_data="help_support")],
        ]
        return InlineKeyboardMarkup(keyboard)
```

**Step 3: Create handlers (see full implementation in next task)**

**Step 4: Commit**

```bash
git add telegram_bot/features/tickets/
git commit -m "feat: add ticket feature module"
```

---

## Task 9: Integrate Tickets into Main Handler

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py`
- Modify: `telegram_bot/handlers/handler_initializer.py`

**Step 1: Add ticket imports and callbacks in main_menu_callback**

Add the ticket callback handling in `main_menu_callback` method.

**Step 2: Register ticket handlers in handler_initializer**

**Step 3: Commit**

```bash
git add telegram_bot/
git commit -m "feat: integrate ticket system into main handlers"
```

---

## Task 10: Update DI Container

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Register TicketService and repository**

**Step 2: Commit**

```bash
git add application/services/common/container.py
git commit -m "feat: register ticket services in DI container"
```

---

## Task 11: Add Admin Ticket Management

**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- Modify: `telegram_bot/features/admin/messages_admin.py`

**Step 1: Add admin ticket list view**

**Step 2: Add admin ticket response flow**

**Step 3: Commit**

```bash
git add telegram_bot/features/admin/
git commit -m "feat: add admin ticket management UI"
```

---

## Task 12: Run Tests and Verify

**Step 1: Run all tests**

```bash
pytest -v
```

**Step 2: Run linting**

```bash
flake8 . --exclude=venv,migrations,__pycache__
```

**Step 3: Manual testing checklist**
- [ ] Help button shows formatted message
- [ ] FAQ button shows FAQ
- [ ] Support button shows support menu
- [ ] Create ticket works
- [ ] User can see their tickets
- [ ] Admin can see all tickets
- [ ] Admin can respond to tickets

---

## Execution Order

1. Task 1 - Fix parse_mode bug (CRITICAL)
2. Task 2 - Improve help UX
3. Task 3 - Create Ticket entity
4. Task 4 - Create database model
5. Task 5 - Run migration
6. Task 6 - Create repository
7. Task 7 - Create service
8. Task 8 - Create feature module
9. Task 9 - Integrate into handlers
10. Task 10 - Update DI container
11. Task 11 - Add admin management
12. Task 12 - Test and verify
