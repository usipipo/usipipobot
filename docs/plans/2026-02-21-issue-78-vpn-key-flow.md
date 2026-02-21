# Issue #78: Flujo de Obtención de Claves VPN - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corregir bug crítico, validar límites de claves, y completar el flujo de creación/listado de claves VPN.

**Architecture:** Clean Architecture con separación de capas. Los handlers de Telegram usan VpnService (Application Layer) que orquesta la creación de claves mediante repositorios y clientes API.

**Tech Stack:** Python 3.11, python-telegram-bot, PostgreSQL, WireGuard, Outline Server

---

## Task 1: Corregir bug crítico en create_key()

**Files:**
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:91`

**Step 1: Verificar el bug actual**

El método `VpnService.create_key()` requiere 4 argumentos:
- `telegram_id: int`
- `key_type: str`
- `key_name: str`
- `current_user_id: int`

Pero en `handlers_vpn_keys.py:91` solo se pasan 3 argumentos.

**Step 2: Corregir la llamada**

Modificar línea 91 en `handlers_vpn_keys.py`:

```python
# ANTES:
new_key = await self.vpn_service.create_key(telegram_id, key_type, key_name)

# DESPUÉS:
new_key = await self.vpn_service.create_key(telegram_id, key_type, key_name, current_user_id=telegram_id)
```

**Step 3: Verificar sintaxis**

Run: `python -m py_compile telegram_bot/features/vpn_keys/handlers_vpn_keys.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add telegram_bot/features/vpn_keys/handlers_vpn_keys.py
git commit -m "fix: add missing current_user_id parameter in create_key call"
```

---

## Task 2: Agregar validación de límite de claves pre-creación

**Files:**
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:43-61`
- Test: `tests/telegram_bot/features/vpn_keys/test_handlers_vpn_keys.py`

**Step 1: Escribir test para validación de límite**

Crear archivo de test si no existe:

```python
# tests/telegram_bot/features/vpn_keys/test_handlers_vpn_keys.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram_bot.features.vpn_keys.handlers_vpn_keys import VpnKeysHandler
from application.services.vpn_service import VpnService

class TestVpnKeysHandler:
    
    @pytest.fixture
    def vpn_service(self):
        return MagicMock(spec=VpnService)
    
    @pytest.fixture
    def handler(self, vpn_service):
        return VpnKeysHandler(vpn_service)
    
    @pytest.mark.asyncio
    async def test_start_creation_blocks_when_limit_reached(self, handler, vpn_service):
        """Usuario con límite de claves alcanzado no puede crear más."""
        # Arrange
        from domain.entities.user import User, UserRole
        
        user = User(telegram_id=123, max_keys=2)
        user.keys = [MagicMock(is_active=True), MagicMock(is_active=True)]
        
        vpn_service.can_user_create_key = AsyncMock(return_value=(False, "Has alcanzado el límite de 2 llaves."))
        
        update = MagicMock()
        update.effective_user.id = 123
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        
        context = MagicMock()
        context.user_data = {}
        
        # Act
        result = await handler.start_creation(update, context)
        
        # Assert
        assert result == -1  # ConversationHandler.END
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "límite" in call_args.kwargs['text'].lower() or "limit" in call_args.kwargs['text'].lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/telegram_bot/features/vpn_keys/test_handlers_vpn_keys.py -v 2>/dev/null || echo "Test file may not exist yet"`
Expected: FAIL (handler doesn't validate limit)

**Step 3: Modificar start_creation() para validar límite**

```python
async def start_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de creación preguntando el tipo de VPN."""
    telegram_id = update.effective_user.id
    is_admin = telegram_id == int(settings.ADMIN_ID)
    
    # Validar si el usuario puede crear más claves
    can_create, message = await self.vpn_service.can_user_create_key(
        await self._get_or_create_user(telegram_id), 
        current_user_id=telegram_id
    )
    
    if not can_create:
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=VpnKeysMessages.Error.KEY_LIMIT_REACHED,
                reply_markup=VpnKeysKeyboards.main_menu(is_admin=is_admin),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=VpnKeysMessages.Error.KEY_LIMIT_REACHED,
                reply_markup=VpnKeysKeyboards.main_menu(is_admin=is_admin),
                parse_mode="Markdown"
            )
        return ConversationHandler.END
    
    # Manejar tanto Message como CallbackQuery
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=VpnKeysMessages.SELECT_TYPE,
            reply_markup=VpnKeysKeyboards.vpn_types(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=VpnKeysMessages.SELECT_TYPE,
            reply_markup=VpnKeysKeyboards.vpn_types(),
            parse_mode="Markdown"
        )
    return SELECT_TYPE

async def _get_or_create_user(self, telegram_id: int) -> 'User':
    """Helper para obtener o crear usuario."""
    from domain.entities.user import User
    user = await self.vpn_service.user_repo.get_by_id(telegram_id, telegram_id)
    if not user:
        user = User(telegram_id=telegram_id)
    return user
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/telegram_bot/features/vpn_keys/test_handlers_vpn_keys.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add telegram_bot/features/vpn_keys/handlers_vpn_keys.py tests/telegram_bot/features/vpn_keys/test_handlers_vpn_keys.py
git commit -m "feat: add key limit validation before starting creation flow"
```

---

## Task 3: Mejorar mensaje de límite con datos actuales

**Files:**
- Modify: `telegram_bot/features/vpn_keys/messages_vpn_keys.py:36-42`
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py`

**Step 1: Actualizar mensaje de error KEY_LIMIT_REACHED**

```python
KEY_LIMIT_REACHED = (
    "❌ **Límite de llaves alcanzado**\n\n"
    "Has alcanzado el límite de **{max_keys}** llaves para tu plan.\n\n"
    "💡 *Soluciones:*\n"
    "• Elimina llaves que no usas desde **🛡️ Mis Llaves**\n"
    "• Actualiza tu plan para más llaves"
)
```

**Step 2: Modificar handler para pasar max_keys al mensaje**

```python
if not can_create:
    user = await self._get_or_create_user(telegram_id)
    error_message = VpnKeysMessages.Error.KEY_LIMIT_REACHED.format(max_keys=user.max_keys)
    # ... resto del código usando error_message
```

**Step 3: Verificar sintaxis**

Run: `python -m py_compile telegram_bot/features/vpn_keys/messages_vpn_keys.py telegram_bot/features/vpn_keys/handlers_vpn_keys.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add telegram_bot/features/vpn_keys/messages_vpn_keys.py telegram_bot/features/vpn_keys/handlers_vpn_keys.py
git commit -m "feat: improve key limit error message with max_keys info"
```

---

## Task 4: Agregar acceso directo "Ver Mis Claves" en flujo post-creación

**Files:**
- Modify: `telegram_bot/features/vpn_keys/keyboards_vpn_keys.py`

**Step 4: Agregar botón "Ver Mis Claves" al teclado main_menu**

```python
@staticmethod
def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Teclado del menú principal contextual.
    """
    keyboard = [
        [
            InlineKeyboardButton("🛡️ Mis Llaves", callback_data="key_management"),
            InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key")
        ],
        [
            InlineKeyboardButton("📊 Estado", callback_data="status"),
            InlineKeyboardButton("🏆 Logros", callback_data="achievements")
        ],
        [
            InlineKeyboardButton("⚙️ Ayuda", callback_data="help")
        ]
    ]
    
    if is_admin:
        keyboard.insert(0, [
            InlineKeyboardButton("🔧 Panel Admin", callback_data="admin")
        ])
    
    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Verificar sintaxis**

Run: `python -m py_compile telegram_bot/features/vpn_keys/keyboards_vpn_keys.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add telegram_bot/features/vpn_keys/keyboards_vpn_keys.py
git commit -m "feat: add direct 'Mis Llaves' and 'Nueva Clave' buttons to main menu"
```

---

## Task 5: Agregar mensaje post-creación con datos disponibles

**Files:**
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:83-155`
- Modify: `telegram_bot/features/vpn_keys/messages_vpn_keys.py`

**Step 1: Agregar mensaje de éxito post-creación**

En `messages_vpn_keys.py`:

```python
class Success:
    """Mensajes de éxito."""
    
    KEY_CREATED_WITH_DATA = (
        "✅ **¡Llave creada exitosamente!**\n\n"
        "📡 **Protocolo:** {type}\n"
        "🔑 **Nombre:** {name}\n"
        "📊 **Datos disponibles:** {data_limit:.1f} GB\n\n"
        "Sigue las instrucciones para conectarte."
    )
```

**Step 2: Modificar name_received para mostrar datos**

Actualizar la parte donde se muestra el caption:

```python
# Para Outline:
caption = VpnKeysMessages.Success.KEY_CREATED_WITH_DATA.format(
    type="OUTLINE",
    name=key_name,
    data_limit=new_key.data_limit_gb
)

# Para WireGuard:
caption = VpnKeysMessages.Success.KEY_CREATED_WITH_DATA.format(
    type="WIREGUARD",
    name=key_name,
    data_limit=new_key.data_limit_gb
)
```

**Step 3: Verificar sintaxis**

Run: `python -m py_compile telegram_bot/features/vpn_keys/handlers_vpn_keys.py telegram_bot/features/vpn_keys/messages_vpn_keys.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add telegram_bot/features/vpn_keys/handlers_vpn_keys.py telegram_bot/features/vpn_keys/messages_vpn_keys.py
git commit -m "feat: show data limit in post-creation success message"
```

---

## Task 6: Tests de integración del flujo completo

**Files:**
- Create: `tests/integration/test_vpn_key_flow.py`

**Step 1: Escribir test de integración**

```python
# tests/integration/test_vpn_key_flow.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from application.services.vpn_service import VpnService
from domain.entities.vpn_key import VpnKey, KeyType
from domain.entities.user import User

class TestVpnKeyFlow:
    
    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_key_repo(self):
        repo = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_user_id = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_outline_client(self):
        client = AsyncMock()
        client.create_key = AsyncMock(return_value={
            "id": "outline-key-123",
            "access_url": "ss://test@server:1234#TestKey"
        })
        return client
    
    @pytest.fixture
    def mock_wireguard_client(self):
        client = AsyncMock()
        client.create_peer = AsyncMock(return_value={
            "client_name": "wg-client-123",
            "config": "[Interface]\nPrivateKey = xxx\nAddress = 10.0.0.2/24\n"
        })
        return client
    
    @pytest.fixture
    def vpn_service(self, mock_user_repo, mock_key_repo, mock_outline_client, mock_wireguard_client):
        return VpnService(
            user_repo=mock_user_repo,
            key_repo=mock_key_repo,
            outline_client=mock_outline_client,
            wireguard_client=mock_wireguard_client
        )
    
    @pytest.mark.asyncio
    async def test_create_outline_key_success(self, vpn_service, mock_user_repo, mock_key_repo):
        """Flujo completo de creación de clave Outline."""
        telegram_id = 12345
        
        key = await vpn_service.create_key(
            telegram_id=telegram_id,
            key_type="outline",
            key_name="Mi iPhone",
            current_user_id=telegram_id
        )
        
        assert key is not None
        assert key.key_type == "outline"
        assert key.name == "Mi iPhone"
        assert key.user_id == telegram_id
        assert key.key_data.startswith("ss://")
        mock_key_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_wireguard_key_success(self, vpn_service, mock_key_repo):
        """Flujo completo de creación de clave WireGuard."""
        telegram_id = 12345
        
        key = await vpn_service.create_key(
            telegram_id=telegram_id,
            key_type="wireguard",
            key_name="Mi Laptop",
            current_user_id=telegram_id
        )
        
        assert key is not None
        assert key.key_type == "wireguard"
        assert key.name == "Mi Laptop"
        assert "[Interface]" in key.key_data
        mock_key_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cannot_create_key_when_limit_reached(self, vpn_service, mock_user_repo):
        """Usuario con 2 claves no puede crear más."""
        telegram_id = 12345
        
        # Usuario existente con 2 claves
        existing_user = User(telegram_id=telegram_id, max_keys=2)
        existing_user.keys = [
            MagicMock(is_active=True),
            MagicMock(is_active=True)
        ]
        mock_user_repo.get_by_id = AsyncMock(return_value=existing_user)
        
        can_create, message = await vpn_service.can_user_create_key(existing_user, telegram_id)
        
        assert can_create is False
        assert "límite" in message.lower() or "limit" in message.lower()
```

**Step 2: Run tests**

Run: `pytest tests/integration/test_vpn_key_flow.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/integration/test_vpn_key_flow.py
git commit -m "test: add integration tests for VPN key creation flow"
```

---

## Task 7: Verificación final y documentación

**Step 1: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 2: Run linter**

Run: `python -m py_compile telegram_bot/features/vpn_keys/*.py application/services/vpn_service.py`
Expected: No output (success)

**Step 3: Update AGENTS.md if needed**

Si se agregaron nuevas funcionalidades significativas, documentarlas.

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(issue-78): complete VPN key creation flow with validations"
```

---

## Verification Checklist

- [ ] Bug de `current_user_id` corregido
- [ ] Validación de límite de claves funciona
- [ ] Mensaje de error incluye límite actual
- [ ] Botones de navegación funcionan
- [ ] Mensaje post-creación muestra datos disponibles
- [ ] Todos los tests pasan
- [ ] Código sin errores de sintaxis