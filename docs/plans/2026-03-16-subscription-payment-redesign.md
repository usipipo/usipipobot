# Subscription Payment Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rediseñar el sistema de suscripciones para que siga el mismo patrón de compra que paquetes y slots, con selección de método de pago (Stars/Crypto) y mover el botón al menú Shop.

**Architecture:** El flujo seguirá el mismo patrón que `buy_gb`: menú de planes → selección de método de pago → confirmación → activación. Se refactorizarán los handlers y teclados para mantener consistencia con `BuyGbKeyboards` y `BuyGbMessages`.

**Tech Stack:** python-telegram-bot 21.10, SQLAlchemy async, Clean Architecture patterns.

---

## Task 1: Actualizar `OperationsKeyboards.shop_menu()` para incluir Suscripciones

**Files:**
- Modify: `telegram_bot/features/operations/keyboards_operations.py:53-67`

**Step 1: Mover botón de Suscripciones al menú Shop**

Modificar el método `shop_menu()` para incluir el botón de suscripciones:

```python
@staticmethod
def shop_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📦 Paquetes de GB", callback_data="buy_gb_menu"),
        ],
        [
            InlineKeyboardButton("🔑 Slots Adicionales", callback_data="buy_slots_menu"),
        ],
        [
            InlineKeyboardButton("💎 Suscripciones", callback_data="subscriptions"),
        ],
        [
            InlineKeyboardButton("✨ Extras con Creditos", callback_data="credits_menu"),
        ],
        [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Eliminar sección de Suscripciones del menú de operaciones**

Modificar `operations_menu()` para remover la sección de suscripciones:

```python
@staticmethod
def operations_menu(credits: int = 0) -> InlineKeyboardMarkup:
    keyboard = [
        # Sección de Beneficios y Referidos
        [
            InlineKeyboardButton(f"🎁 Créditos ({credits})", callback_data="credits_menu"),
            InlineKeyboardButton("👥 Referidos", callback_data="referral_menu"),
        ],
        # Sección de Compras e Historial
        [
            InlineKeyboardButton("🛒 Shop", callback_data="shop_menu"),
            InlineKeyboardButton("📜 Historial", callback_data="transactions_history"),
        ],
        # Volver
        [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 3: Run tests**

```bash
pytest tests/telegram_bot/features/operations/ -v
```

**Step 4: Commit**

```bash
git add telegram_bot/features/operations/keyboards_operations.py
git commit -m "feat: move subscriptions button to shop menu"
```

---

## Task 2: Crear `SubscriptionKeyboards.sub_payment_method_selection()`

**Files:**
- Modify: `telegram_bot/features/subscriptions/keyboards.py:13-55`

**Step 1: Agregar método de selección de pago**

Agregar después de `subscription_menu()`:

```python
@staticmethod
def sub_payment_method_selection(plan_type: str) -> InlineKeyboardMarkup:
    """Keyboard para seleccionar método de pago para suscripciones (Stars o Crypto)."""
    keyboard = [
        [
            InlineKeyboardButton(
                "⭐ Pagar con Stars", callback_data=f"pay_sub_stars_{plan_type}"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Pagar con Crypto", callback_data=f"pay_sub_crypto_{plan_type}"
            )
        ],
        [InlineKeyboardButton("🔙 Volver a Suscripciones", callback_data="subscriptions")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Actualizar `subscription_menu()` para usar nuevo patrón**

Modificar los callbacks para incluir selección de pago:

```python
@staticmethod
def subscription_menu() -> InlineKeyboardMarkup:
    """Keyboard para el menú de suscripciones."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🥇 1 Mes - 360 ⭐", callback_data="select_sub_payment_1_month"
            ),
        ],
        [
            InlineKeyboardButton(
                "🥈 3 Meses - 960 ⭐", callback_data="select_sub_payment_3_months"
            ),
        ],
        [
            InlineKeyboardButton(
                "🥉 6 Meses - 1560 ⭐", callback_data="select_sub_payment_6_months"
            ),
        ],
        [InlineKeyboardButton("« Volver", callback_data="operations_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 3: Commit**

```bash
git add telegram_bot/features/subscriptions/keyboards.py
git commit -m "feat: add payment method selection for subscriptions"
```

---

## Task 3: Crear `SubscriptionMessages.Payment` con mensajes de selección de método

**Files:**
- Modify: `telegram_bot/features/subscriptions/messages.py`

**Step 1: Agregar clase `Payment` después de `Menu`**

```python
class Payment:
    """Mensajes para selección de método de pago."""

    _HEADER = f"{_SEP_HEADER}\n" "💳 *MÉTODO DE PAGO*\n" f"{_SEP_HEADER}\n"

    _SELECT_METHOD_BODY = (
        "\n"
        "*Plan:* {plan_name}\n"
        "*Precio:* {stars} Stars ⭐ | ${usdt} USDT\n"
        "*Duración:* {duration} días\n"
        "*Datos:* 🌐 Ilimitados\n"
        f"{_SEP_DIVIDER}\n"
        "Selecciona tu método de pago:\n"
    )

    @classmethod
    def select_method(cls, plan_name: str, stars: int, usdt: float, duration: int) -> str:
        """Generate payment method selection message."""
        message = cls._HEADER
        message += cls._SELECT_METHOD_BODY.format(
            plan_name=plan_name,
            stars=stars,
            usdt=usdt,
            duration=duration,
        )
        return message
```

**Step 2: Commit**

```bash
git add telegram_bot/features/subscriptions/messages.py
git commit -m "feat: add payment method selection messages for subscriptions"
```

---

## Task 4: Actualizar `SubscriptionHandler` con nuevo flujo de pago

**Files:**
- Modify: `telegram_bot/features/subscriptions/handlers.py:26-200`

**Step 1: Agregar método `select_payment_method()`**

Agregar después de `show_subscriptions()`:

```python
async def select_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra opciones de método de pago para una suscripción."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    # Extraer plan_type de select_sub_payment_{plan_type}
    plan_type = query.data.replace("select_sub_payment_", "")

    try:
        plan_option = self.subscription_service.get_plan_option(plan_type)
        if not plan_option:
            await query.edit_message_text(
                text="❌ Plan no válido",
                reply_markup=SubscriptionKeyboards.subscription_menu(),
                parse_mode="Markdown",
            )
            return

        message = SubscriptionMessages.Payment.select_method(
            plan_name=plan_option.name,
            stars=plan_option.stars,
            usdt=plan_option.usdt,
            duration=plan_option.duration_months * 30,
        )

        keyboard = SubscriptionKeyboards.sub_payment_method_selection(plan_type)

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error en select_payment_method: {e}")
        await query.edit_message_text(
            text="❌ Error al cargar métodos de pago",
            reply_markup=SubscriptionKeyboards.subscription_menu(),
            parse_mode="Markdown",
        )
```

**Step 2: Refactorizar `select_plan()` para redirigir a selección de pago**

Reemplazar el método actual:

```python
async def select_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection - redirect to payment method selection."""
    # Este método ya no se usa directamente, el flujo va directo a select_payment_method
    pass
```

**Step 3: Agregar métodos de pago con Stars y Crypto**

```python
async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa pago de suscripción con Telegram Stars."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    plan_type = query.data.replace("pay_sub_stars_", "")
    user_id = update.effective_user.id

    try:
        plan_option = self.subscription_service.get_plan_option(plan_type)
        if not plan_option:
            await query.answer("❌ Plan no válido", show_alert=True)
            return

        # Check for existing subscription
        is_premium = await self.subscription_service.is_premium_user(
            user_id, settings.ADMIN_ID
        )
        if is_premium:
            await query.answer(
                "⚠️ Ya tienes una suscripción activa",
                show_alert=True,
            )
            return

        # TODO: Implement Telegram Stars invoice
        # Por ahora, simulamos activación directa
        payment_id = f"sub_stars_{user_id}_{plan_type}"

        subscription = await self.subscription_service.activate_subscription(
            user_id=user_id,
            plan_type=plan_type,
            stars_paid=plan_option.stars,
            payment_id=payment_id,
            current_user_id=settings.ADMIN_ID,
        )

        expires_at = subscription.expires_at.strftime("%d/%m/%Y")
        message = SubscriptionMessages.Success.subscription_activated(
            plan_name=plan_option.name,
            stars=plan_option.stars,
            expires_at=expires_at,
        )

        await query.edit_message_text(
            text=message,
            reply_markup=SubscriptionKeyboards.subscription_status(),
            parse_mode="Markdown",
        )

        logger.info(f"💎 Subscription activated with Stars for user {user_id}: {plan_option.name}")

    except ValueError as e:
        logger.warning(f"Subscription activation failed for user {user_id}: {e}")
        await query.answer(str(e), show_alert=True)
    except Exception as e:
        logger.error(f"Error in pay_with_stars: {e}")
        await query.answer("❌ Error al procesar pago", show_alert=True)

async def pay_with_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa pago de suscripción con Crypto (USDT/BSC)."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    plan_type = query.data.replace("pay_sub_crypto_", "")
    user_id = update.effective_user.id

    try:
        plan_option = self.subscription_service.get_plan_option(plan_type)
        if not plan_option:
            await query.answer("❌ Plan no válido", show_alert=True)
            return

        # Check for existing subscription
        is_premium = await self.subscription_service.is_premium_user(
            user_id, settings.ADMIN_ID
        )
        if is_premium:
            await query.answer(
                "⚠️ Ya tienes una suscripción activa",
                show_alert=True,
            )
            return

        # TODO: Implement crypto payment flow (similar to buy_gb)
        # Por ahora, simulamos activación directa
        payment_id = f"sub_crypto_{user_id}_{plan_type}"

        subscription = await self.subscription_service.activate_subscription(
            user_id=user_id,
            plan_type=plan_type,
            stars_paid=plan_option.stars,
            payment_id=payment_id,
            current_user_id=settings.ADMIN_ID,
        )

        expires_at = subscription.expires_at.strftime("%d/%m/%Y")
        message = SubscriptionMessages.Success.subscription_activated(
            plan_name=plan_option.name,
            stars=plan_option.stars,
            expires_at=expires_at,
        )

        await query.edit_message_text(
            text=message,
            reply_markup=SubscriptionKeyboards.subscription_status(),
            parse_mode="Markdown",
        )

        logger.info(f"💎 Subscription activated with Crypto for user {user_id}: {plan_option.name}")

    except ValueError as e:
        logger.warning(f"Subscription activation failed for user {user_id}: {e}")
        await query.answer(str(e), show_alert=True)
    except Exception as e:
        logger.error(f"Error in pay_with_crypto: {e}")
        await query.answer("❌ Error al procesar pago", show_alert=True)
```

**Step 4: Commit**

```bash
git add telegram_bot/features/subscriptions/handlers.py
git commit -m "feat: implement payment method selection flow for subscriptions"
```

---

## Task 5: Actualizar handlers callback en `get_subscription_callback_handlers()`

**Files:**
- Modify: `telegram_bot/features/subscriptions/handlers.py:218-230`

**Step 1: Actualizar lista de callbacks**

```python
def get_subscription_callback_handlers():
    """Get subscription callback handlers."""
    subscription_service = get_service(SubscriptionService)
    handler = SubscriptionHandler(subscription_service)

    return [
        CallbackQueryHandler(handler.show_subscriptions, pattern="^subscriptions$"),
        CallbackQueryHandler(handler.select_payment_method, pattern="^select_sub_payment_"),
        CallbackQueryHandler(handler.pay_with_stars, pattern="^pay_sub_stars_"),
        CallbackQueryHandler(handler.pay_with_crypto, pattern="^pay_sub_crypto_"),
        CallbackQueryHandler(handler.view_status, pattern="^sub_status$"),
    ]
```

**Step 2: Eliminar `confirm_purchase` del handler** (ya no se usa en este flujo)

**Step 3: Commit**

```bash
git add telegram_bot/features/subscriptions/handlers.py
git commit -m "refactor: update subscription callback handlers for new payment flow"
```

---

## Task 6: Verificar tests y ejecutar validación

**Files:**
- Test: `tests/telegram_bot/features/subscriptions/` (si existen)

**Step 1: Ejecutar tests existentes**

```bash
pytest tests/telegram_bot/features/subscriptions/ -v
```

**Step 2: Ejecutar tests generales del bot**

```bash
pytest tests/telegram_bot/ -v -k "subscription"
```

**Step 3: Verificar que no hay errores de importación**

```bash
python -m py_compile telegram_bot/features/subscriptions/handlers.py
python -m py_compile telegram_bot/features/subscriptions/keyboards.py
python -m py_compile telegram_bot/features/subscriptions/messages.py
python -m py_compile telegram_bot/features/operations/keyboards_operations.py
```

**Step 4: Commit final**

```bash
git status
git commit -am "chore: verify subscription redesign implementation"
```

---

## Task 7: Documentación y verificación manual

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Actualizar CHANGELOG**

Agregar entrada:

```markdown
## [3.9.1] - 2026-03-16

### Changed
- 💎 Suscripciones: Rediseñado flujo de pago para seguir mismo patrón que paquetes y slots
- 🛒 Shop: Movido botón de Suscripciones al menú Shop desde Operaciones
- ⭐ Crypto: Agregada selección de método de pago (Stars/Crypto) para suscripciones

### Fixed
- 🐛 Suscripciones: Botones de compra ahora siguen patrón consistente con resto del shop
```

**Step 2: Commit final**

```bash
git add CHANGELOG.md
git commit -m "docs: update changelog for subscription redesign"
```

**Step 3: Verificación manual**

Ejecutar el bot y verificar:
1. Botón "💎 Suscripciones" aparece en menú Shop
2. Al seleccionar plan, muestra opciones de pago (Stars/Crypto)
3. El flujo completo funciona correctamente

---

## Summary

**Total Tasks:** 7

**Files Modified:**
1. `telegram_bot/features/operations/keyboards_operations.py` - Mover botón a Shop
2. `telegram_bot/features/subscriptions/keyboards.py` - Agregar selección de pago
3. `telegram_bot/features/subscriptions/messages.py` - Agregar mensajes de pago
4. `telegram_bot/features/subscriptions/handlers.py` - Implementar nuevo flujo
5. `CHANGELOG.md` - Documentar cambios

**Key Changes:**
- ✅ Suscripciones siguen mismo patrón que paquetes/slots
- ✅ Selección de método de pago (Stars/Crypto) integrada
- ✅ Botón movido al menú Shop
- ✅ Mensajes con formato consistente

**Testing Strategy:**
- Tests existentes deben pasar
- Verificación manual del flujo completo
- Validar que no hay errores de compilación
