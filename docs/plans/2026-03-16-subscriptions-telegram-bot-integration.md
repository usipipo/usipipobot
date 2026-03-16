# Subscription Plans - Telegram Bot Integration & Mini App Enhancement

**Date:** March 16, 2026
**Version:** 1.1.0 (Corrección de huecos del diseño original)
**Status:** Pending Approval
**Author:** uSipipo Team

---

## 1. Executive Summary (Actualizado)

Este documento **complementa** el diseño original (`2026-03-16-subscription-plans-design.md`) abordando los **huecos identificados**:

### Huecos Cubiertos

| # | Hueco | Solución |
|---|-------|----------|
| 1 | Flujo de pago no implementado | `SubscriptionPaymentService` + Webhook handlers |
| 2 | Bot handlers ausentes | Módulo `telegram_bot/features/subscriptions/` |
| 3 | Mini App página no diseñada | `subscriptions.html` + rutas dedicadas |
| 4 | Integración VPN incompleta | Patch a `VpnService` + `ConsumptionBillingService` |
| 5 | Tests incompletos | Tests E2E + integration tests |

---

## 2. Arquitectura de Pagos (NUEVO)

### 2.1 Diagrama de Flujo de Pago

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO SELECCIONA PLAN                  │
│                   (1 Mes / 3 Meses / 6 Meses)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         SELECCIONAR MÉTODO DE PAGO (Stars | Crypto)         │
│              Mismo patrón que compra de paquetes            │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
        ▼                            ▼
┌──────────────┐            ┌──────────────┐
│   STARS      │            │    CRYPTO    │
│  PAYMENT     │            │   PAYMENT    │
└──────┬───────┘            └──────┬───────┘
       │                           │
       │ 1. send_stars_invoice()   │ 1. create_crypto_order()
       │ 2. Invoice en Telegram    │ 2. Wallet + QR code
       │ 3. User paga en bot       │ 3. Info en Telegram
       │ 4. Webhook: /stars_invoice│ 4. Webhook: /crypto_webhook
       │                           │
       ▼                           ▼
┌──────────────────────────────────────────────────────────────┐
│              SubscriptionService.activate_subscription()     │
│  - Check: user already has active subscription?              │
│  - Check: payment_id already used? (idempotency)             │
│  - Create: SubscriptionPlan entity                           │
│  - Save: PostgreSQL with audit trail                         │
│  - Update: user.premium_status (denormalization)             │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│              NOTIFICACIÓN Y ENTREGA                          │
│  - Mensaje confirmación (cyberpunk style)                    │
│  - Update VPN keys: is_premium = True                        │
│  - Dashboard Mini App: premium badge                         │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Nuevo Servicio: `SubscriptionPaymentService`

**File:** `application/services/subscription_payment_service.py`

```python
class SubscriptionPaymentService:
    """Orquesta pagos de suscripciones (Stars + Crypto)."""

    def __init__(
        self,
        subscription_service: SubscriptionService,
        notification_service: NotificationService,
        crypto_payment_service: CryptoPaymentService,
    ):
        self.subscription_service = subscription_service
        self.notification_service = notification_service
        self.crypto_payment_service = crypto_payment_service

    async def create_stars_invoice(
        self,
        user_id: int,
        plan_type: str,
        transaction_id: str,
    ) -> dict:
        """Crear factura Stars para suscripción."""
        plan_option = self.subscription_service.get_plan_option(plan_type)

        if not plan_option:
            raise ValueError(f"Plan no válido: {plan_type}")

        # Check existing subscription
        is_premium = await self.subscription_service.is_premium_user(user_id)
        if is_premium:
            raise ValueError("Ya tienes una suscripción activa")

        # Send invoice via Telegram Bot
        invoice_sent = await self.notification_service.send_stars_invoice(
            user_id=user_id,
            title=f"Suscripción {plan_option.name}",
            description=f"{plan_option.duration_months} meses de datos ilimitados",
            payload=f"subscription_{plan_type}_{user_id}_{transaction_id}",
            amount=plan_option.stars,
        )

        if not invoice_sent:
            raise Exception("No se pudo crear la factura")

        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount_stars": plan_option.stars,
        }

    async def create_crypto_order(
        self,
        user_id: int,
        plan_type: str,
        transaction_id: str,
    ) -> dict:
        """Crear orden crypto para suscripción."""
        plan_option = self.subscription_service.get_plan_option(plan_type)

        if not plan_option:
            raise ValueError(f"Plan no válido: {plan_type}")

        # Check existing subscription
        is_premium = await self.subscription_service.is_premium_user(user_id)
        if is_premium:
            raise ValueError("Ya tienes una suscripción activa")

        # Create crypto order via existing service
        usdt_amount = plan_option.usdt
        order_data = await self.crypto_payment_service.create_order(
            user_id=user_id,
            amount_usdt=usdt_amount,
            product_type="subscription",
            product_id=plan_type,
            transaction_id=transaction_id,
        )

        return {
            **order_data,
            "success": True,
            "plan_type": plan_type,
            "amount_usdt": usdt_amount,
        }

    async def confirm_stars_payment(
        self,
        user_id: int,
        plan_type: str,
        payment_id: str,
        stars_paid: int,
    ) -> SubscriptionPlan:
        """Confirmar pago Stars y activar suscripción."""
        # Idempotency check
        existing = await self.subscription_service.get_by_payment_id(payment_id)
        if existing:
            logger.info(f"Pago duplicado detectado: {payment_id}")
            return existing

        # Activate subscription
        subscription = await self.subscription_service.activate_subscription(
            user_id=user_id,
            plan_type=plan_type,
            stars_paid=stars_paid,
            payment_id=payment_id,
            current_user_id=user_id,
        )

        # Send confirmation message
        await self.notification_service.send_subscription_confirmation(
            user_id=user_id,
            plan_type=plan_type,
            stars_paid=stars_paid,
        )

        return subscription

    async def confirm_crypto_payment(
        self,
        user_id: int,
        plan_type: str,
        payment_id: str,
        stars_paid: int,
    ) -> SubscriptionPlan:
        """Confirmar pago crypto y activar suscripción."""
        # Idempotency check
        existing = await self.subscription_service.get_by_payment_id(payment_id)
        if existing:
            logger.info(f"Pago duplicado detectado: {payment_id}")
            return existing

        # Activate subscription
        subscription = await self.subscription_service.activate_subscription(
            user_id=user_id,
            plan_type=plan_type,
            stars_paid=stars_paid,
            payment_id=payment_id,
            current_user_id=user_id,
        )

        # Send confirmation message
        await self.notification_service.send_subscription_confirmation(
            user_id=user_id,
            plan_type=plan_type,
            stars_paid=stars_paid,
            payment_method="Crypto (USDT)",
        )

        return subscription
```

---

## 3. Telegram Bot - Módulo de Suscripciones (NUEVO)

### 3.1 Estructura de Archivos

```
telegram_bot/features/subscriptions/
├── __init__.py
├── handlers_subscriptions.py        # Handlers principales
├── keyboards_subscriptions.py       # Teclados inline
├── messages_subscriptions.py        # Mensajes cyberpunk
└── operations/
    └── subscription_operations.py   # Operaciones de negocio
```

### 3.2 Handlers Principales

**File:** `telegram_bot/features/subscriptions/handlers_subscriptions.py`

```python
class SubscriptionsHandler:
    """Manages subscription-related conversations."""

    def __init__(self, subscription_service: SubscriptionService):
        self.subscription_service = subscription_service

    async def show_subscriptions_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra menú de planes de suscripción."""
        query = update.callback_query
        if query:
            await query.answer()

        message = SubscriptionMessages.Menu.PLANS_LIST
        keyboard = SubscriptionKeyboards.subscriptions_menu()

        if query:
            await TelegramUtils.safe_edit_message(
                query, context, text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        elif update.message:
            await update.message.reply_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )

    async def select_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Usuario selecciona un plan específico."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        plan_type = query.data.split("_")[-1]  # e.g., "one_month"

        message = SubscriptionMessages.Payment.SELECT_METHOD.format(
            plan_name=plan_type.replace("_", " ").title(),
        )
        keyboard = SubscriptionKeyboards.payment_method_selection(plan_type)

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def select_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa selección de método de pago."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        # Parse: pay_stars_one_month or pay_crypto_three_months
        parts = query.data.split("_")
        payment_method = parts[-2]  # "stars" or "crypto"
        plan_type = parts[-1]  # "one_month", etc.

        if payment_method == "stars":
            await self.process_stars_payment(update, context, plan_type)
        else:
            await self.process_crypto_payment(update, context, plan_type)

    async def process_stars_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str):
        """Procesa pago con Telegram Stars."""
        query = update.callback_query
        user_id = update.effective_user.id

        # Generate transaction ID
        transaction_id = str(uuid.uuid4())[:16]

        # Create invoice via service
        payment_service = get_service(SubscriptionPaymentService)
        result = await payment_service.create_stars_invoice(
            user_id=user_id,
            plan_type=plan_type,
            transaction_id=transaction_id,
        )

        # Send confirmation
        message = SubscriptionMessages.Payment.INVOICE_SENT
        await query.edit_message_text(text=message, parse_mode="Markdown")

    async def process_crypto_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str):
        """Procesa pago con Crypto (USDT)."""
        query = update.callback_query
        user_id = update.effective_user.id

        # Generate transaction ID
        transaction_id = str(uuid.uuid4())[:16]

        # Create crypto order
        payment_service = get_service(SubscriptionPaymentService)
        result = await payment_service.create_crypto_order(
            user_id=user_id,
            plan_type=plan_type,
            transaction_id=transaction_id,
        )

        # Send wallet info
        message = SubscriptionMessages.Crypto.PAYMENT_INFO.format(
            wallet_address=result["wallet_address"],
            amount_usdt=result["amount_usdt"],
            qr_code_url=result["qr_code_url"],
        )
        keyboard = SubscriptionKeyboards.crypto_payment_complete()

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def view_subscription_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra estado de suscripción activa."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        user_id = update.effective_user.id
        subscription = await self.subscription_service.get_active_subscription(user_id)

        if not subscription:
            message = SubscriptionMessages.Status.NO_ACTIVE_SUBSCRIPTION
            keyboard = SubscriptionKeyboards.back_to_plans()
        else:
            message = SubscriptionMessages.Status.ACTIVE_SUBSCRIPTION.format(
                plan_name=subscription.plan_type.value.replace("_", " ").title(),
                expires_at=subscription.expires_at.strftime("%Y-%m-%d %H:%M"),
                days_remaining=subscription.days_remaining,
            )
            keyboard = SubscriptionKeyboards.subscription_management()

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )
```

### 3.3 Teclados

**File:** `telegram_bot/features/subscriptions/keyboards_subscriptions.py`

```python
class SubscriptionKeyboards:
    """Teclados para módulo de suscripciones."""

    @staticmethod
    def subscriptions_menu() -> InlineKeyboardMarkup:
        """Menú principal con los 3 planes."""
        keyboard = [
            [
                InlineKeyboardButton("👑 1 Mes - 360⭐", callback_data="select_plan_one_month"),
                InlineKeyboardButton("🥈 3 Meses - 960⭐", callback_data="select_plan_three_months"),
            ],
            [
                InlineKeyboardButton("🥉 6 Meses - 1560⭐", callback_data="select_plan_six_months"),
            ],
            [
                InlineKeyboardButton("📊 Ver Mi Suscripción", callback_data="view_subscription_status"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="shop_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_method_selection(plan_type: str) -> InlineKeyboardMarkup:
        """Seleccionar método de pago (Stars | Crypto)."""
        keyboard = [
            [InlineKeyboardButton("⭐ Pagar con Stars", callback_data=f"pay_stars_{plan_type}")],
            [InlineKeyboardButton("💰 Pagar con Crypto", callback_data=f"pay_crypto_{plan_type}")],
            [InlineKeyboardButton("🔙 Volver a Planes", callback_data="subscription_plans_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def subscription_management() -> InlineKeyboardMarkup:
        """Gestión de suscripción activa."""
        keyboard = [
            [InlineKeyboardButton("🔁 Renovar", callback_data="renew_subscription")],
            [InlineKeyboardButton("📦 Ver Otros Planes", callback_data="subscription_plans_menu")],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def crypto_payment_complete() -> InlineKeyboardMarkup:
        """Confirmar pago crypto completado."""
        keyboard = [
            [InlineKeyboardButton("✅ Ya Envié el Pago", callback_data="crypto_payment_sent")],
            [InlineKeyboardButton("🔙 Volver", callback_data="subscription_plans_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_plans() -> InlineKeyboardMarkup:
        """Volver a planes."""
        keyboard = [
            [InlineKeyboardButton("📦 Ver Planes", callback_data="subscription_plans_menu")],
            [InlineKeyboardButton("🔙 Volver", callback_data="shop_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
```

### 3.4 Mensajes Cyberpunk

**File:** `telegram_bot/features/subscriptions/messages_subscriptions.py`

```python
class SubscriptionMessages:
    """Mensajes para módulo de suscripciones."""

    class Menu:
        """Menú de planes."""

        _HEADER = (
            f"{_SEP_HEADER}\n"
            "🚀 PLANES PREMIUM\n"
            f"{_SEP_HEADER}\n"
        )

        _PLANS_LIST = (
            "┌──────────────────────────┐\n"
            "│ 👑 1 MES                 │\n"
            "│ ⭐ 360 Stars             │\n"
            "│ 💰 $2.99 USDT            │\n"
            "└──────────────────────────┘\n"
            "\n"
            "┌──────────────────────────┐\n"
            "│ 🥈 3 MESES               │\n"
            "│ ⭐ 960 Stars             │\n"
            "│ 💰 $7.99 USDT            │\n"
            "│ 💎 Ahorra 11%            │\n"
            "└──────────────────────────┘\n"
            "\n"
            "┌──────────────────────────┐\n"
            "│ 🥉 6 MESES               │\n"
            "│ ⭐ 1,560 Stars           │\n"
            "│ 💰 $12.99 USDT           │\n"
            "│ 💎 Ahorra 28%            │\n"
            "└──────────────────────────┘\n"
        )

        _BENEFITS = (
            "\n"
            "✅ *Beneficios Incluidos:*\n"
            "├─ 📊 Datos ILIMITADOS\n"
            "├─ 🚀 Velocidad prioritaria\n"
            "├─ 💎 Soporte prioritario\n"
            "└─ ⚠️ Uso Justo (Fair Use)\n"
        )

        _FOOTER = (
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Selecciona tu plan:*\n"
        )

        PLANS_LIST = _HEADER + _PLANS_LIST + _BENEFITS + _FOOTER

    class Payment:
        """Mensajes de pago."""

        SELECT_METHOD = (
            "💳 *Seleccionar Método de Pago*\n\n"
            "🚀 **Plan:** {plan_name}\n\n"
            "Elige cómo quieres pagar:\n"
        )

        INVOICE_SENT = (
            "✅ **Factura Enviada**\n\n"
            "Revisa tu chat de Telegram para completar el pago.\n\n"
            "💡 *La factura aparecerá en tu conversación con el bot*"
        )

    class Crypto:
        """Mensajes de pago crypto."""

        PAYMENT_INFO = (
            "💰 **Pago con USDT (BSC)**\n\n"
            "🏦 **Enviar a:**\n"
            "`{wallet_address}`\n\n"
            "💰 **Monto:** `{amount_usdt:.2f} USDT`\n\n"
            "🔗 **Red:** BSC (BEP20)\n\n"
            "⚠️ **Importante:**\n"
            "• Solo envía USDT en red BSC\n"
            "• El pago se detecta automáticamente\n"
            "• QR code enviado a tu Telegram\n\n"
        )

    class Status:
        """Estado de suscripción."""

        NO_ACTIVE_SUBSCRIPTION = (
            "⚠️ **Sin Suscripción Activa**\n\n"
            "No tienes una suscripción premium activa.\n\n"
            "💡 *Adquiere un plan para datos ilimitados*"
        )

        ACTIVE_SUBSCRIPTION = (
            "✅ **Suscripción Activa**\n\n"
            "🚀 **Plan:** {plan_name}\n"
            "📅 **Expira:** {expires_at}\n"
            "⏰ **Días restantes:** {days_remaining}\n\n"
            "💎 *Disfruta de datos ilimitados*"
        )
```

### 3.5 Registro de Handlers

**File:** `telegram_bot/__init__.py` o `telegram_bot/router.py`

```python
# Registrar handlers de suscripciones
from telegram_bot.features.subscriptions.handlers_subscriptions import SubscriptionsHandler

subscription_handler = SubscriptionsHandler(get_service(SubscriptionService))

application.add_handler(
    CallbackQueryHandler(subscription_handler.show_subscriptions_menu, pattern="^subscription_plans_menu$")
)
application.add_handler(
    CallbackQueryHandler(subscription_handler.select_plan, pattern="^select_plan_")
)
application.add_handler(
    CallbackQueryHandler(subscription_handler.select_payment_method, pattern="^pay_(stars|crypto)_")
)
application.add_handler(
    CallbackQueryHandler(subscription_handler.view_subscription_status, pattern="^view_subscription_status$")
)
```

---

## 4. Mini App - Página de Suscripciones (NUEVO)

### 4.1 Nueva Ruta

**File:** `miniapp/routes_subscriptions.py` (modificar para agregar ruta HTML)

```python
@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página dedicada para suscripciones premium."""
    logger.info(f"💎 MiniApp subscriptions page accessed by user {ctx.user.id}")

    # Get user's current subscription
    subscription_service = get_service(SubscriptionService)
    is_premium = await subscription_service.is_premium_user(ctx.user.id, ctx.user.id)
    subscription = await subscription_service.get_user_subscription(ctx.user.id, ctx.user.id)

    # Get plan options
    plan_options = [
        {
            "id": "one_month",
            "name": "1 Mes Premium",
            "duration_months": 1,
            "stars": 360,
            "usdt": 2.99,
            "badge": None,
            "featured": False,
        },
        {
            "id": "three_months",
            "name": "3 Meses Premium",
            "duration_months": 3,
            "stars": 960,
            "usdt": 7.99,
            "badge": "+11% BONUS",
            "featured": True,
        },
        {
            "id": "six_months",
            "name": "6 Meses Premium",
            "duration_months": 6,
            "stars": 1560,
            "usdt": 12.99,
            "badge": "+28% BONUS",
            "featured": False,
        },
    ]

    return templates.TemplateResponse(
        "subscriptions.html",
        {
            "request": request,
            "user": ctx.user,
            "plan_options": plan_options,
            "is_premium": is_premium,
            "current_subscription": subscription,
            "bot_username": settings.BOT_USERNAME,
        },
    )
```

### 4.2 Template: `subscriptions.html`

**File:** `miniapp/templates/subscriptions.html`

```html
{% extends "base.html" %}

{% block title %}Suscripciones Premium - uSipipo VPN{% endblock %}

{% block content %}
<div class="glitch-title" style="margin-bottom: 20px;">💎 Premium</div>

<div class="terminal-output">
    Datos ilimitados para tus claves VPN
</div>

<!-- Current Subscription Status -->
{% if is_premium and current_subscription %}
<div class="card" style="margin-top: 20px; border: 1px solid var(--accent-magenta);">
    <div class="card-title" style="color: var(--accent-magenta);">✅ Suscripción Activa</div>
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 12px;">
        <div>
            <div style="color: var(--text-muted);">Plan</div>
            <div style="color: var(--text-primary); font-weight: 600;">{{ current_subscription.plan_name }}</div>
        </div>
        <div>
            <div style="color: var(--text-muted);">Expira</div>
            <div style="color: var(--accent-green); font-weight: 600;">{{ current_subscription.days_remaining }} días</div>
        </div>
        <div>
            <div style="color: var(--text-muted);">Inicio</div>
            <div style="color: var(--text-primary);">{{ current_subscription.starts_at.strftime('%Y-%m-%d') }}</div>
        </div>
        <div>
            <div style="color: var(--text-muted);">Fin</div>
            <div style="color: var(--text-primary);">{{ current_subscription.expires_at.strftime('%Y-%m-%d') }}</div>
        </div>
    </div>
    <div style="margin-top: 16px;">
        <button class="btn btn-primary btn-full" onclick="window.location.href='/miniapp/purchase'">
            🔁 Renovar
        </button>
    </div>
</div>
{% endif %}

<!-- Subscription Plans -->
<div style="margin-top: 20px;">
    <div style="font-size: 14px; color: var(--accent-cyan); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px;">
        🚀 Planes Disponibles
    </div>
    <div class="packages-grid">
        {% for plan in plan_options %}
        <div class="package-card {% if plan.featured %}featured{% endif %}"
             style="{% if plan.featured %}border-color: var(--accent-magenta);{% endif %}">

            {% if plan.badge %}
            <div style="position: absolute; top: 12px; right: 12px;">
                <span class="badge badge-active"
                      style="{% if plan.featured %}background: var(--accent-magenta);{% endif %}">
                    {{ plan.badge }}
                </span>
            </div>
            {% endif %}

            <div style="font-size: 24px; margin-bottom: 8px;">
                {% if plan.id == 'one_month' %}👑{% elif plan.id == 'three_months' %}🥈{% else %}🥉{% endif %}
            </div>

            <div class="package-name">{{ plan.name }}</div>
            <div class="package-data">{{ plan.duration_months }} {% if plan.duration_months == 1 %}Mes{% else %}Meses{% endif %}</div>

            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">
                Datos ilimitados
            </div>

            <div class="package-price">
                ⭐ {{ plan.stars }}
            </div>
            <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">
                Telegram Stars
            </div>
            <div style="font-size: 10px; color: var(--accent-green); margin-bottom: 16px;">
                💰 {{ plan.usdt }} USDT
            </div>

            <button class="btn {% if plan.featured %}btn-primary{% else %}btn-secondary{% endif %} btn-full"
                    onclick="showPaymentMethods('subscription', '{{ plan.id }}', {{ plan.stars }}, {{ plan.usdt }})">
                Activar Premium
            </button>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Benefits Section -->
<div class="card" style="margin-top: 20px;">
    <div class="card-title">🌟 Beneficios Premium</div>
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 12px; color: var(--text-secondary);">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--accent-cyan);">✓</span>
            <span>Datos ilimitados</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--accent-cyan);">✓</span>
            <span>Velocidad prioritaria</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--accent-cyan);">✓</span>
            <span>Sin límites de consumo</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--accent-cyan);">✓</span>
            <span>Soporte prioritario</span>
        </div>
    </div>
</div>

<!-- Fair Use Policy -->
<div class="card" style="margin-top: 20px; border: 1px solid var(--accent-yellow);">
    <div class="card-title" style="color: var(--accent-yellow);">⚠️ Política de Uso Justo</div>
    <div style="font-size: 11px; color: var(--text-secondary); line-height: 1.6;">
        <p style="margin-bottom: 8px;"><strong>Ideal para:</strong> Navegación, streaming HD (1080p), gaming, redes sociales, trabajo remoto</p>
        <p style="margin-bottom: 8px;"><strong>No recomendado:</strong> Streaming 4K 24/7, torrenting masivo, uso comercial intensivo</p>
        <p><strong>Velocidad:</strong> 50-100 Mbps (depende de la carga del servidor)</p>
    </div>
</div>

<!-- Payment Modal (reutilizado de purchase.html) -->
<div id="paymentModal" class="modal" style="display: none;">
    <!-- Same structure as purchase.html -->
</div>

<!-- Crypto Modal (reutilizado de purchase.html) -->
<div id="cryptoModal" class="modal" style="display: none;">
    <!-- Same structure as purchase.html -->
</div>
{% endblock %}

{% block extra_js %}
<!-- Same payment logic as purchase.html -->
<script>
// Reuse payment logic from purchase.html
let currentProduct = null;
let currentProductType = null;
let currentPriceStars = 0;
let currentPriceUsdt = 0;

function showPaymentMethods(type, id, starsPrice, usdtPrice) {
    // Same implementation as purchase.html
}

function closePaymentModal() {
    // Same implementation
}

async function payWithStars() {
    // Same implementation
}

async function payWithCrypto() {
    // Same implementation
}
</script>
{% endblock %}
```

### 4.3 Navegación Actualizada

**File:** `miniapp/templates/dashboard.html` (agregar botón)

```html
<!-- Agregar en el dashboard -->
<div class="card" style="margin-top: 20px;">
    <div class="card-title">💎 Premium</div>
    <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">
        Datos ilimitados para tus claves VPN
    </p>
    <button class="btn btn-primary btn-full" onclick="window.location.href='/miniapp/subscriptions'">
        🚀 Ver Planes Premium
    </button>
</div>
```

---

## 5. Integración con VPN Key Management (CORREGIDO)

### 5.1 Patch a `VpnService`

**File:** `application/services/vpn_service.py`

```python
class VpnService:
    async def create_key(self, user_id: int, ...) -> VpnKey:
        # Check if user has active subscription
        active_plan = await self.subscription_service.get_active_plan(user_id, user_id)
        is_premium = active_plan is not None

        # Create key with appropriate limits
        if is_premium:
            # Unlimited data for premium users
            key.data_limit_bytes = -1  # Special value for unlimited
            key.is_premium = True
            logger.info(f"👑 Creating premium key for user {user_id} (unlimited)")
        else:
            # Standard 5GB limit for free users
            key.data_limit_bytes = 5 * (1024 ** 3)
            key.is_premium = False
            logger.info(f"📊 Creating standard key for user {user_id} (5GB)")
```

### 5.2 Patch a `ConsumptionBillingService`

**File:** `application/services/consumption_billing_service.py`

```python
class ConsumptionBillingService:
    async def consume_data(self, user_id: int, bytes_used: int) -> bool:
        # Check for active subscription first
        active_plan = await self.subscription_service.get_active_plan(user_id, user_id)

        if active_plan and active_plan.is_active:
            # Premium user - no consumption tracking needed
            logger.info(f"👑 Premium user {user_id} consuming {bytes_used} bytes (unlimited)")
            return True

        # Non-premium: use existing GB package logic
        return await self._consume_from_packages(user_id, bytes_used)
```

---

## 6. Testing Strategy (COMPLETO)

### 6.1 Tests de Handlers del Bot

**File:** `tests/telegram_bot/features/subscriptions/test_handlers_subscriptions.py`

```python
class TestSubscriptionsHandlers:
    @pytest.fixture
    def handler(self, mock_subscription_service):
        return SubscriptionsHandler(mock_subscription_service)

    @pytest.mark.asyncio
    async def test_show_subscriptions_menu(self, handler, update, context):
        """Test que muestra menú de suscripciones."""
        await handler.show_subscriptions_menu(update, context)

        # Verify message was sent
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args
        assert "PLANES PREMIUM" in args[1]["text"]

    @pytest.mark.asyncio
    async def test_select_plan(self, handler, callback_query, context):
        """Test selección de plan."""
        callback_query.data = "select_plan_one_month"

        await handler.select_plan(callback_query, context)

        # Verify payment method selection shown
        callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_stars_payment(self, handler, callback_query, context, mock_payment_service):
        """Test pago con Stars."""
        callback_query.data = "pay_stars_one_month"

        await handler.process_stars_payment(callback_query, context, "one_month")

        # Verify invoice created
        mock_payment_service.create_stars_invoice.assert_called_once()
```

### 6.2 Tests de Integración E2E

**File:** `tests/integration/test_subscription_payment_flow.py`

```python
class TestSubscriptionPaymentFlow:
    @pytest.mark.asyncio
    async def test_full_stars_payment_flow(self, db_session, test_user):
        """Test flujo completo de pago con Stars."""
        # 1. User selects plan
        # 2. Creates stars invoice
        # 3. Simulates payment webhook
        # 4. Subscription activated
        # 5. VPN key created with unlimited data

        subscription_service = get_service(SubscriptionService)

        # Activate subscription
        subscription = await subscription_service.activate_subscription(
            user_id=test_user.telegram_id,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="test_payment_123",
            current_user_id=test_user.telegram_id,
        )

        assert subscription is not None
        assert subscription.plan_type == PlanType.ONE_MONTH
        assert subscription.is_active is True

        # Verify VPN key has unlimited data
        vpn_service = get_service(VpnService)
        key = await vpn_service.create_key(user_id=test_user.telegram_id)

        assert key.is_premium is True
        assert key.data_limit_bytes == -1

    @pytest.mark.asyncio
    async def test_full_crypto_payment_flow(self, db_session, test_user):
        """Test flujo completo de pago con Crypto."""
        # Similar to Stars flow but with crypto order
        pass

    @pytest.mark.asyncio
    async def test_premium_user_unlimited_consumption(self, db_session, test_user):
        """Test que premium users tienen consumo ilimitado."""
        # Activate subscription
        # Consume data
        # Verify no GB tracking

        consumption_service = get_service(ConsumptionBillingService)

        # Premium user
        result = await consumption_service.consume_data(
            user_id=test_user.telegram_id,
            bytes_used=10 * (1024 ** 3),  # 10GB
        )

        assert result is True  # Allowed without tracking
```

---

## 7. Migration Plan (Actualizado)

### 7.1 Deployment Checklist

```bash
# 1. Backup database
pg_dump vpn_manager > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migrations
uv run alembic upgrade head

# 3. Sync dependencies
uv sync

# 4. Restart service
sudo systemctl restart usipipo

# 5. Verify logs
sudo journalctl -u usipipo -f --no-pager | tail -50

# 6. Test subscription flow manually
# - Open bot: /suscripciones
# - Select plan
# - Test Stars payment
# - Test Crypto payment
```

### 7.2 Rollback Plan

```bash
# If something goes wrong:
uv run alembic downgrade -1
sudo systemctl restart usipipo
```

---

## 8. Monitoring & Alerts

### 8.1 New Metrics

```python
# Add to metrics endpoint
@router.get("/metrics")
async def get_metrics():
    return {
        "active_subscriptions": await count_active_subscriptions(),
        "subscription_revenue_mtd": await calculate_mtd_revenue(),
        "subscription_churn_rate": await calculate_churn_rate(),
    }
```

### 8.2 Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| `subscription_payment_failed` | > 5 failures in 1 hour | Notify admin |
| `subscription_expiring_soon` | User expires in < 3 days | Send reminder |
| `high_churn_rate` | Churn > 20% MoM | Review pricing |

---

## 9. Timeline Estimado

| Fase | Tareas | Duración |
|------|--------|----------|
| **1. Domain Layer** | Entity + Repository interface | 2 horas |
| **2. Infrastructure** | Model + Migration + Repository | 4 horas |
| **3. Application Services** | SubscriptionService + PaymentService | 4 horas |
| **4. Telegram Bot** | Handlers + Keyboards + Messages | 6 horas |
| **5. Mini App** | Página subscriptions.html + rutas | 4 horas |
| **6. Integration** | Patch VpnService + ConsumptionBilling | 2 horas |
| **7. Testing** | Unit + Integration + E2E | 6 horas |
| **8. Deployment** | Migration + deploy + verification | 2 horas |
| **Total** | | **30 horas** |

---

## 10. Criterios de Aceptación

### ✅ Definition of Done

1. **Domain Layer**
   - [ ] `SubscriptionPlan` entity con tests passing
   - [ ] `ISubscriptionRepository` interface definido

2. **Infrastructure**
   - [ ] `SubscriptionPlanModel` SQLAlchemy
   - [ ] Migration creada y testeada
   - [ ] `PostgresSubscriptionRepository` implementado

3. **Application Services**
   - [ ] `SubscriptionService` con todos los métodos
   - [ ] `SubscriptionPaymentService` para orquestar pagos
   - [ ] Tests de servicio passing (>90% coverage)

4. **Telegram Bot**
   - [ ] `/suscripciones` command handler
   - [ ] Callback handlers para selección de planes
   - [ ] Payment method selection (Stars | Crypto)
   - [ ] Mensajes cyberpunk consistentes
   - [ ] Tests de handlers passing

5. **Mini App**
   - [ ] Página `/subscriptions` funcional
   - [ ] Template `subscriptions.html` con cyberpunk theme
   - [ ] Modal de pago (Stars/Crypto) funcional
   - [ ] Navegación desde dashboard

6. **Integration**
   - [ ] `VpnService` chequea suscripciones
   - [ ] `ConsumptionBillingService` bypass para premium
   - [ ] Tests de integración passing

7. **Testing**
   - [ ] Tests unitarios (>90% coverage)
   - [ ] Tests de integración
   - [ ] Tests E2E de flujos de pago
   - [ ] Todos los tests passing en CI

8. **Deployment**
   - [ ] Migration aplicada en producción
   - [ ] Service restart exitoso
   - [ ] Logs sin errores
   - [ ] Manual testing completado

---

## 11. Riesgos y Mitigación

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Pagos duplicados | Alto | Idempotency con `payment_id` unique |
| Subscription no se activa | Alto | Webhook retry logic + admin alerts |
| VPN keys no actualizan | Medio | Background job de sync |
| Confusión con GB packages | Medio | Messaging claro: "Ilimitado vs GB" |
| Fair use abuse | Medio | Monitoring + manual intervention |

---

**Documento aprobado por:** [Pending]
**Fecha de aprobación:** [Pending]
**Próxima revisión:** March 23, 2026
