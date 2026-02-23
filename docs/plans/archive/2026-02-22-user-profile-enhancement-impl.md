# User Profile Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement complete user profile functionality with transaction history, data packages summary, and referral statistics.

**Architecture:** Create a new `UserProfileService` that orchestrates data from existing services (VpnService, DataPackageService, ReferralService, TransactionRepository). Update handlers to use the consolidated data. Add `/history` command and profile button for transaction history.

**Tech Stack:** Python 3.x, SQLAlchemy Async, python-telegram-bot, Clean Architecture patterns

---

## Task 1: Create UserProfileService

**Files:**
- Create: `application/services/user_profile_service.py`
- Create: `tests/application/services/test_user_profile_service.py`

**Step 1: Write the failing test**

```python
# tests/application/services/test_user_profile_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from application.services.user_profile_service import UserProfileService, UserProfileSummary


class TestUserProfileService:
    @pytest.fixture
    def mock_transaction_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_data_package_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_referral_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_vpn_service(self):
        return AsyncMock()

    @pytest.fixture
    def user_profile_service(
        self, mock_transaction_repo, mock_data_package_service, 
        mock_referral_service, mock_vpn_service
    ):
        return UserProfileService(
            transaction_repo=mock_transaction_repo,
            data_package_service=mock_data_package_service,
            referral_service=mock_referral_service,
            vpn_service=mock_vpn_service,
        )

    @pytest.mark.asyncio
    async def test_get_user_profile_summary_returns_complete_data(
        self, user_profile_service, mock_vpn_service, mock_data_package_service,
        mock_referral_service
    ):
        mock_user = MagicMock()
        mock_user.telegram_id = 123
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"
        mock_user.status.value = "active"
        mock_user.role.value = "user"
        mock_user.max_keys = 3
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.referral_credits = 100
        mock_user.free_data_remaining_bytes = 5 * 1024**3

        mock_vpn_service.get_user_status.return_value = {
            "user": mock_user,
            "keys_count": 2,
            "keys": [],
            "total_used_gb": 3.5,
            "total_limit_gb": 20.0,
            "remaining_gb": 16.5,
        }

        mock_data_package_service.get_user_data_summary.return_value = {
            "active_packages": 2,
            "packages": [],
            "free_plan": {"remaining_gb": 5.0},
            "total_limit_gb": 20.0,
            "total_used_gb": 3.5,
            "remaining_gb": 16.5,
        }

        mock_referral_service.get_referral_stats.return_value = MagicMock(
            referral_code="ABC123",
            total_referrals=5,
            referral_credits=100,
            referred_by=None,
        )

        result = await user_profile_service.get_user_profile_summary(123, 123)

        assert result is not None
        assert result.user_id == 123
        assert result.username == "testuser"
        assert result.keys_count == 2
        assert result.active_packages == 2
        assert result.total_referrals == 5
        assert result.referral_code == "ABC123"

    @pytest.mark.asyncio
    async def test_get_user_transactions_returns_transaction_list(
        self, user_profile_service, mock_transaction_repo
    ):
        mock_transaction_repo.get_user_transactions.return_value = [
            {
                "id": "1",
                "transaction_type": "package_purchase",
                "amount": 50,
                "description": "Paquete Básico",
                "created_at": datetime.now(timezone.utc),
            }
        ]

        result = await user_profile_service.get_user_transactions(123, limit=5)

        assert len(result) == 1
        assert result[0]["transaction_type"] == "package_purchase"
        mock_transaction_repo.get_user_transactions.assert_called_once_with(123, 5)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/application/services/test_user_profile_service.py -v`
Expected: FAIL with "No module named 'application.services.user_profile_service'"

**Step 3: Write minimal implementation**

```python
# application/services/user_profile_service.py
"""
Servicio para consolidar información del perfil de usuario.

Author: uSipipo Team
Version: 1.0.0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from application.services.data_package_service import DataPackageService
from application.services.referral_service import ReferralService
from application.services.vpn_service import VpnService
from domain.interfaces.itransaction_repository import ITransactionRepository
from utils.logger import logger


@dataclass
class UserProfileSummary:
    """Resumen completo del perfil de usuario."""
    user_id: int
    username: Optional[str]
    full_name: Optional[str]
    status: str
    role: str
    created_at: datetime
    max_keys: int
    keys_count: int
    keys_used: int
    total_used_gb: float
    total_limit_gb: float
    remaining_gb: float
    free_data_remaining_gb: float
    active_packages: int
    referral_code: str
    total_referrals: int
    referral_credits: int
    referred_by: Optional[int]


class UserProfileService:
    """
    Servicio que consolida toda la información del perfil de usuario.
    
    Orquesta llamadas a VpnService, DataPackageService, ReferralService
    y TransactionRepository para proporcionar una vista unificada.
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        data_package_service: DataPackageService,
        referral_service: ReferralService,
        vpn_service: VpnService,
    ):
        self.transaction_repo = transaction_repo
        self.data_package_service = data_package_service
        self.referral_service = referral_service
        self.vpn_service = vpn_service

    async def get_user_profile_summary(
        self, user_id: int, current_user_id: int
    ) -> Optional[UserProfileSummary]:
        """
        Obtiene un resumen completo del perfil de usuario.
        
        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            UserProfileSummary con toda la información consolidada
        """
        try:
            vpn_status = await self.vpn_service.get_user_status(user_id, current_user_id)
            user = vpn_status.get("user")
            
            if not user:
                logger.warning(f"Usuario no encontrado: {user_id}")
                return None

            data_summary = await self.data_package_service.get_user_data_summary(
                user_id, current_user_id
            )
            
            referral_stats = await self.referral_service.get_referral_stats(
                user_id, current_user_id
            )

            keys = vpn_status.get("keys", [])
            active_keys = [k for k in keys if getattr(k, "is_active", True)]

            return UserProfileSummary(
                user_id=user.telegram_id,
                username=user.username,
                full_name=user.full_name,
                status=user.status.value,
                role=user.role.value,
                created_at=user.created_at,
                max_keys=user.max_keys,
                keys_count=len(keys),
                keys_used=len(active_keys),
                total_used_gb=vpn_status.get("total_used_gb", 0),
                total_limit_gb=vpn_status.get("total_limit_gb", 0),
                remaining_gb=vpn_status.get("remaining_gb", 0),
                free_data_remaining_gb=data_summary.get("free_plan", {}).get("remaining_gb", 0),
                active_packages=data_summary.get("active_packages", 0),
                referral_code=referral_stats.referral_code,
                total_referrals=referral_stats.total_referrals,
                referral_credits=referral_stats.referral_credits,
                referred_by=referral_stats.referred_by,
            )

        except Exception as e:
            logger.error(f"Error obteniendo resumen de perfil para usuario {user_id}: {e}")
            return None

    async def get_user_transactions(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de transacciones del usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de transacciones a retornar
            
        Returns:
            Lista de transacciones
        """
        try:
            return await self.transaction_repo.get_user_transactions(user_id, limit)
        except Exception as e:
            logger.error(f"Error obteniendo transacciones para usuario {user_id}: {e}")
            return []
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/application/services/test_user_profile_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add application/services/user_profile_service.py tests/application/services/test_user_profile_service.py
git commit -m "feat: add UserProfileService for consolidated profile data"
```

---

## Task 2: Register UserProfileService in Container

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Add UserProfileService registration**

Add to imports:
```python
from application.services.user_profile_service import UserProfileService
```

Add factory function in `_configure_application_services`:
```python
def create_user_profile_service() -> UserProfileService:
    return UserProfileService(
        transaction_repo=create_transaction_repo(),
        data_package_service=create_data_package_service(),
        referral_service=create_referral_service(),
        vpn_service=create_vpn_service(),
    )

container.register(UserProfileService, factory=create_user_profile_service)
```

**Step 2: Commit**

```bash
git add application/services/common/container.py
git commit -m "feat: register UserProfileService in DI container"
```

---

## Task 3: Update UserManagementMessages

**Files:**
- Modify: `telegram_bot/features/user_management/messages_user_management.py`

**Step 1: Remove hardcoded fields and add new fields**

Replace `USER_INFO` in `Info` class:
```python
USER_INFO = (
    "ℹ️ *Información Detallada*\n\n"
    "👤 *Usuario:* {name}\n"
    "🆔 *ID:* {user_id}\n"
    "👥 *Username:* @{username}\n"
    "📅 *Registro:* {join_date}\n"
    "🟢 *Estado:* {status}\n\n"
    "📊 *Datos:*\n"
    "├─ Usados: {data_used}\n"
    "├─ Gratuitos restantes: {free_data_remaining}\n"
    "└─ Paquetes activos: {active_packages}\n\n"
    "🔑 *Claves VPN:*\n"
    "└─ Usadas: {keys_used}/{keys_total}\n\n"
    "🎁 *Referidos:*\n"
    "├─ Código: {referral_code}\n"
    "├─ Invitados: {total_referrals}\n"
    "└─ Créditos: {credits}"
)
```

**Step 2: Add History messages class**

Add new class after `Info`:
```python
class History:
    """Mensajes de historial de transacciones."""

    HEADER = "📜 *Historial de Transacciones*\n\n"

    NO_TRANSACTIONS = (
        "📜 *Historial de Transacciones*\n\n"
        "No tienes transacciones registradas aún."
    )

    TRANSACTION_ITEM = (
        "{number}\\. `{date}` \\- {description}\n"
        "   {amount} | {status}"
    )

    FOOTER = "\n\n📄 _Ver más_ | 🏠 _Menú principal_"
```

**Step 3: Commit**

```bash
git add telegram_bot/features/user_management/messages_user_management.py
git commit -m "feat: update profile messages and add history messages"
```

---

## Task 4: Update UserManagementHandler

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py`
- Modify: `telegram_bot/features/user_management/keyboards_user_management.py`

**Step 1: Update handler imports and constructor**

Add import:
```python
from application.services.user_profile_service import UserProfileService
```

Update constructor:
```python
def __init__(self, vpn_service: VpnService, user_profile_service: UserProfileService = None):
    self.vpn_service = vpn_service
    self.user_profile_service = user_profile_service
    logger.info("👤 UserManagementHandler inicializado")
```

**Step 2: Rewrite info_handler with consolidated data**

Replace the `info_handler` method:
```python
async def info_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra información detallada del usuario.
    """
    telegram_id = update.effective_user.id
    
    try:
        if self.user_profile_service:
            profile = await self.user_profile_service.get_user_profile_summary(
                telegram_id, telegram_id
            )
            
            if not profile:
                await update.message.reply_text(
                    text=UserManagementMessages.Error.INFO_FAILED,
                    reply_markup=UserManagementKeyboards.main_menu(),
                )
                return

            join_date = profile.created_at.strftime("%Y-%m-%d")
            status_text = "Activo ✅" if profile.status == "active" else "Inactivo ⚠️"
            plan = "Premium" if profile.referral_credits > 0 else "Gratis"

            text = (
                UserManagementMessages.Info.HEADER
                + "\n\n"
                + UserManagementMessages.Info.USER_INFO.format(
                    name=profile.full_name or "N/A",
                    user_id=telegram_id,
                    username=profile.username or "N/A",
                    join_date=join_date,
                    status=status_text,
                    data_used=f"{profile.total_used_gb:.2f} GB",
                    free_data_remaining=f"{profile.free_data_remaining_gb:.2f} GB",
                    active_packages=profile.active_packages,
                    keys_used=profile.keys_used,
                    keys_total=profile.max_keys,
                    referral_code=profile.referral_code,
                    total_referrals=profile.total_referrals,
                    credits=profile.referral_credits,
                )
            )
        else:
            text = UserManagementMessages.Error.INFO_FAILED

        is_admin_menu = telegram_id == int(settings.ADMIN_ID)

        await update.message.reply_text(
            text=text,
            reply_markup=UserManagementKeyboards.profile_menu(is_admin=is_admin_menu),
            parse_mode="Markdown",
        )

    except (AttributeError, ValueError, KeyError) as e:
        logger.error(f"❌ Error en info_handler para usuario {telegram_id}: {e}")
        await update.message.reply_text(
            text=UserManagementMessages.Error.INFO_FAILED,
            reply_markup=UserManagementKeyboards.main_menu(),
        )
```

**Step 3: Add history_handler method**

Add after `info_handler`:
```python
async def history_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el historial de transacciones del usuario.
    """
    telegram_id = update.effective_user.id

    try:
        if not self.user_profile_service:
            await update.message.reply_text(
                text="❌ Servicio no disponible",
                reply_markup=UserManagementKeyboards.main_menu(),
            )
            return

        transactions = await self.user_profile_service.get_user_transactions(
            telegram_id, limit=5
        )

        if not transactions:
            await update.message.reply_text(
                text=UserManagementMessages.History.NO_TRANSACTIONS,
                reply_markup=UserManagementKeyboards.main_menu(),
                parse_mode="Markdown",
            )
            return

        lines = [UserManagementMessages.History.HEADER]
        lines.append("*Últimos 5 movimientos:*\n")

        for i, tx in enumerate(transactions, 1):
            tx_type = tx.get("transaction_type", "unknown")
            amount = tx.get("amount", 0)
            description = tx.get("description", "Sin descripción")
            created_at = tx.get("created_at")
            
            date_str = created_at.strftime("%Y-%m-%d") if created_at else "N/A"
            
            if "purchase" in tx_type or "package" in tx_type:
                status_icon = "⭐"
                amount_str = f"{amount} Stars"
            elif "referral" in tx_type:
                status_icon = "🎁"
                amount_str = f"+{amount} créditos"
            elif "redemption" in tx_type:
                status_icon = "💳"
                amount_str = f"-{abs(amount)} créditos"
            else:
                status_icon = "📝"
                amount_str = str(amount)

            lines.append(f"{i}\\. `{date_str}` \\- {description}")
            lines.append(f"   {status_icon} {amount_str}")
            lines.append("")

        lines.append(UserManagementMessages.History.FOOTER)

        text = "\n".join(lines)
        is_admin_menu = telegram_id == int(settings.ADMIN_ID)

        await update.message.reply_text(
            text=text,
            reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"❌ Error en history_handler para usuario {telegram_id}: {e}")
        await update.message.reply_text(
            text="❌ Error al cargar historial",
            reply_markup=UserManagementKeyboards.main_menu(),
        )
```

**Step 4: Update get_user_management_handlers function**

Update to include UserProfileService:
```python
def get_user_management_handlers(
    vpn_service: VpnService, user_profile_service: UserProfileService = None
):
    """
    Retorna los handlers de gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN
        user_profile_service: Servicio de perfil de usuario (opcional)

    Returns:
        list: Lista de handlers
    """
    handler = UserManagementHandler(vpn_service, user_profile_service)

    handlers = [
        CommandHandler("start", handler.start_handler),
        CommandHandler("info", handler.info_handler),
        CommandHandler("history", handler.history_handler),
        MessageHandler(filters.Regex("^📊 Estado$"), handler.status_handler),
        CommandHandler("status", handler.status_handler),
    ]
    
    return handlers
```

**Step 5: Update profile callback in main_menu_callback**

Add history callback handler inside `main_menu_callback`:
```python
elif callback_data == "show_history":
    await self.history_handler(update, _context)
```

**Step 6: Commit**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "feat: update handlers with UserProfileService and add /history command"
```

---

## Task 5: Add Profile Keyboard with History Button

**Files:**
- Modify: `telegram_bot/features/user_management/keyboards_user_management.py`

**Step 1: Add profile_menu keyboard method**

Add method to `UserManagementKeyboards` class:
```python
@staticmethod
def profile_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Teclado del menú de perfil con botón de historial.
    """
    keyboard = [
        [
            InlineKeyboardButton("📜 Historial", callback_data="show_history"),
            InlineKeyboardButton("📊 Estado", callback_data="status"),
        ],
        [
            InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu"),
        ],
    ]
    
    if is_admin:
        keyboard.append([
            InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel"),
        ])
    
    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Commit**

```bash
git add telegram_bot/features/user_management/keyboards_user_management.py
git commit -m "feat: add profile_menu keyboard with history button"
```

---

## Task 6: Update Main Bot Registration

**Files:**
- Modify: `main.py` or the file where handlers are registered

**Step 1: Register UserProfileService in handler creation**

Find where handlers are registered and update to include UserProfileService:
```python
from application.services.user_profile_service import UserProfileService

# In handler registration
user_profile_service = container.resolve(UserProfileService)
user_handlers = get_user_management_handlers(vpn_service, user_profile_service)
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: register UserProfileService in bot handlers"
```

---

## Task 7: Run All Tests

**Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Run linting if available**

Run: `flake8 .` or `black --check .`

**Step 3: Fix any issues**

---

## Task 8: Integration Testing

**Step 1: Start the bot locally**

Run: `python main.py`

**Step 2: Test /info command**

- Send `/info` to bot
- Verify all fields are populated
- Verify no hardcoded values

**Step 3: Test /history command**

- Send `/history` to bot
- Verify transactions are displayed

**Step 4: Test profile button**

- Send `/info`
- Click "📜 Historial" button
- Verify history is shown

---

## Acceptance Criteria Checklist

- [ ] `/info` muestra información completa sin valores hardcodeados
- [ ] `/info` muestra datos gratuitos restantes
- [ ] `/info` muestra número de paquetes activos
- [ ] `/info` muestra conteo de referidos
- [ ] Existe forma de ver historial de transacciones (/history + botón)
- [ ] `/status` muestra resumen de datos y claves
- [ ] Tests unitarios para UserProfileService
- [ ] Todos los tests existentes pasan
