# Mini App Payment Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement complete payment flow for Mini App Web with Telegram Stars and Crypto payments, matching the Bot's functionality.

**Architecture:** Hybrid payment flow where users select products in Mini App, pay via Telegram (Stars) or Crypto (QR), and the system automatically detects completion via Bot handlers and Webhooks.

**Tech Stack:** FastAPI, python-telegram-bot, SQLAlchemy async, TronDealer API, Telegram Stars

---

## Overview

This plan implements the complete payment ecosystem for the Mini App Web platform:

1. **Payment Status API** - Poll endpoint to check payment completion
2. **Transaction History** - Dedicated page for full transaction history
3. **Bot Integration** - Detect Mini App payments in `successful_payment` handler
4. **Crypto Webhook** - Ensure TronDealer webhook supports Mini App
5. **Frontend Updates** - Auto-polling for payment status, improved UX

### Current State

- ✅ Mini App can create Stars invoices (via Bot)
- ✅ Mini App can create Crypto orders (QR display)
- ✅ TronDealer webhook exists and works
- ⚠️ No automatic payment detection for Stars
- ⚠️ No dedicated transaction history page
- ⚠️ User must manually confirm payment

### Target State

- ✅ User selects product in Mini App
- ✅ User pays in Telegram (Stars) or via QR (Crypto)
- ✅ System auto-detects payment completion
- ✅ Mini App shows real-time status via polling
- ✅ Full transaction history available

---

## Phase 1: Backend - Payment Status API

### Task 1.1: Create Payment Status Endpoint

**Files:**
- Create: `infrastructure/api/routes/miniapp_payments.py:600-700` (add new endpoint)
- Test: `tests/miniapp/test_payment_endpoints.py` (add new test class)

**Step 1: Add endpoint to check payment status**

```python
@router.get("/api/payment-status/{transaction_id}")
async def get_payment_status(
    transaction_id: str,
    ctx: MiniAppContext = Depends(get_current_user),
):
    """
    Check payment status for a transaction.

    Used by Mini App frontend to poll for payment completion.
    """
    logger.info(f"Checking payment status: {transaction_id} for user {ctx.user.id}")

    async with get_session_context() as session:
        # Check for Stars payment (DataPackage with telegram_payment_id starting with "miniapp_")
        package_repo = PostgresDataPackageRepository(session)
        packages = await package_repo.get_by_user_id(ctx.user.id, ctx.user.id)

        for pkg in packages:
            if pkg.telegram_payment_id and transaction_id in pkg.telegram_payment_id:
                return {
                    "success": True,
                    "status": "completed" if pkg.is_active else "pending",
                    "type": "package",
                    "product_id": pkg.package_type.value if hasattr(pkg.package_type, 'value') else pkg.package_type,
                    "data_gb": pkg.data_gb,
                    "activated_at": pkg.activated_at.isoformat() if pkg.activated_at else None,
                }

        # Check for Crypto payment
        from infrastructure.persistence.postgresql.crypto_order_repository import PostgresCryptoOrderRepository
        crypto_repo = PostgresCryptoOrderRepository(session)
        orders = await crypto_repo.get_by_user_id(ctx.user.id, ctx.user.id)

        for order in orders:
            if order.transaction_id == transaction_id:
                return {
                    "success": True,
                    "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                    "type": "crypto",
                    "amount_usdt": order.amount_usdt,
                    "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
                }

        # Check for subscription
        from infrastructure.persistence.postgresql.subscription_repository import PostgresSubscriptionRepository
        sub_repo = PostgresSubscriptionRepository(session)
        subscriptions = await sub_repo.get_by_user_id(ctx.user.id, ctx.user.id)

        for sub in subscriptions:
            if sub.payment_id and transaction_id in sub.payment_id:
                return {
                    "success": True,
                    "status": "completed" if sub.is_active else "pending",
                    "type": "subscription",
                    "plan_type": sub.plan_type.value if hasattr(sub.plan_type, 'value') else str(sub.plan_type),
                    "activated_at": sub.starts_at.isoformat() if sub.starts_at else None,
                }

    return {
        "success": True,
        "status": "pending",
        "message": "Payment not yet detected. Please complete payment in Telegram."
    }
```

**Step 2: Run tests to verify endpoint exists**

Run: `uv run pytest tests/miniapp/test_payment_endpoints.py::TestPaymentStatus -v`
Expected: FAIL (test doesn't exist yet)

**Step 3: Add test for payment status endpoint**

```python
class TestPaymentStatus:
    """Tests for /api/payment-status/{transaction_id} endpoint."""

    @pytest.mark.asyncio
    async def test_payment_status_pending(self, client):
        """Test checking status of pending payment."""
        transaction_id = "test_txn_123"
        response = await client.get(f"/api/v1/miniapp/api/payment-status/{transaction_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_payment_status_completed_package(self, client_with_package):
        """Test checking status of completed package payment."""
        # client_with_package is a fixture that creates a package with transaction_id
        response = await client_with_package.get(
            f"/api/v1/miniapp/api/payment-status/test_txn_123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["type"] == "package"
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/miniapp/test_payment_endpoints.py::TestPaymentStatus -v`
Expected: PASS (2/2 tests)

**Step 5: Commit**

```bash
git add infrastructure/api/routes/miniapp_payments.py tests/miniapp/test_payment_endpoints.py
git commit -m "feat: Add payment status polling endpoint for Mini App
- GET /api/v1/miniapp/api/payment-status/{transaction_id}
- Checks DataPackage, CryptoOrder, and Subscription
- Returns status: pending, completed, failed
- Enables auto-polling in Mini App frontend"
```

---

### Task 1.2: Create Transaction History Endpoint

**Files:**
- Create: `infrastructure/api/routes/miniapp_payments.py:700-850` (add new endpoint)
- Test: `tests/miniapp/test_payment_endpoints.py` (add new test class)

**Step 1: Add transaction history endpoint with pagination**

```python
@router.get("/transactions")
async def get_transactions(
    ctx: MiniAppContext = Depends(get_current_user),
    page: int = 1,
    limit: int = 20,
    type: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    Get user's transaction history with pagination and filters.

    Query params:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - type: Filter by type (package, slots, subscription, crypto)
    - status: Filter by status (pending, completed, failed, expired)
    """
    logger.info(f"Fetching transactions for user {ctx.user.id}: page={page}, limit={limit}")

    async with get_session_context() as session:
        transactions = []

        # Fetch packages
        if not type or type in ["package", "slots"]:
            package_repo = PostgresDataPackageRepository(session)
            packages = await package_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            for pkg in packages:
                if status and (status == "completed" and not pkg.is_active):
                    continue

                tx_type = "slots" if "slots" in str(pkg.package_type).lower() else "package"
                transactions.append({
                    "id": str(pkg.id),
                    "type": tx_type,
                    "description": f"Paquete {pkg.data_gb} GB",
                    "amount": -pkg.stars_paid if hasattr(pkg, 'stars_paid') else 0,
                    "status": "completed" if pkg.is_active else "pending",
                    "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
                    "payment_method": "stars" if pkg.telegram_payment_id else "crypto",
                })

        # Fetch crypto orders
        if not type or type == "crypto":
            from infrastructure.persistence.postgresql.crypto_order_repository import PostgresCryptoOrderRepository
            crypto_repo = PostgresCryptoOrderRepository(session)
            orders = await crypto_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            for order in orders:
                if status and str(order.status) != status:
                    continue

                transactions.append({
                    "id": str(order.id),
                    "type": "crypto",
                    "description": f"USDT {order.amount_usdt:.2f}",
                    "amount": -order.amount_usdt,
                    "status": str(order.status),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "payment_method": "crypto",
                })

        # Fetch subscriptions
        if not type or type == "subscription":
            from infrastructure.persistence.postgresql.subscription_repository import PostgresSubscriptionRepository
            sub_repo = PostgresSubscriptionRepository(session)
            subscriptions = await sub_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            for sub in subscriptions:
                if status and (status == "completed" and not sub.is_active):
                    continue

                transactions.append({
                    "id": str(sub.id),
                    "type": "subscription",
                    "description": f"Suscripción {sub.plan_type.value if hasattr(sub.plan_type, 'value') else str(sub.plan_type)}",
                    "amount": -sub.stars_paid if hasattr(sub, 'stars_paid') else 0,
                    "status": "completed" if sub.is_active else "pending",
                    "created_at": sub.created_at.isoformat() if sub.created_at else None,
                    "payment_method": "stars",
                })

        # Sort by created_at descending
        transactions.sort(key=lambda x: x["created_at"] or "", reverse=True)

        # Paginate
        total = len(transactions)
        start = (page - 1) * limit
        end = start + limit
        paginated = transactions[start:end]

        return {
            "success": True,
            "transactions": paginated,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }
```

**Step 2: Add tests for transaction history**

```python
class TestTransactionHistory:
    """Tests for /api/transactions endpoint."""

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, client):
        """Test getting transactions when user has none."""
        response = await client.get("/api/v1/miniapp/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transactions"] == []
        assert data["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_transactions_with_packages(self, client_with_packages):
        """Test getting transactions with existing packages."""
        response = await client.get("/api/v1/miniapp/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["transactions"]) > 0
        assert data["transactions"][0]["type"] in ["package", "slots", "crypto", "subscription"]

    @pytest.mark.asyncio
    async def test_get_transactions_pagination(self, client_with_many_transactions):
        """Test pagination works correctly."""
        response = await client.get("/api/v1/miniapp/transactions?page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) <= 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_transactions_filter_by_type(self, client_with_mixed_transactions):
        """Test filtering by transaction type."""
        response = await client.get("/api/v1/miniapp/transactions?type=package")

        assert response.status_code == 200
        data = response.json()
        for tx in data["transactions"]:
            assert tx["type"] == "package"
```

**Step 3: Run tests**

Run: `uv run pytest tests/miniapp/test_payment_endpoints.py::TestTransactionHistory -v`
Expected: PASS (4/4 tests)

**Step 4: Commit**

```bash
git add infrastructure/api/routes/miniapp_payments.py tests/miniapp/test_payment_endpoints.py
git commit -m "feat: Add transaction history endpoint with pagination
- GET /api/v1/miniapp/transactions
- Supports pagination (page, limit)
- Supports filters (type, status)
- Combines packages, crypto orders, subscriptions
- Sorted by created_at descending"
```

---

## Phase 2: Bot Integration - Detect Mini App Payments

### Task 2.1: Update Bot's successful_payment Handler

**Files:**
- Modify: `telegram_bot/features/buy_gb/handlers_confirmation.py:87-200`
- Test: `tests/telegram_bot/features/buy_gb/test_handlers_confirmation.py`

**Step 1: Add Mini App payment detection logic**

```python
async def successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el pago exitoso y entrega el producto."""
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    if not update.message or not update.message.successful_payment:
        return
    payment = update.message.successful_payment

    try:
        payload = payment.invoice_payload
        parts = payload.split("_")

        # DETECT Mini App payments
        if payload.startswith("miniapp_"):
            logger.info(f"📱 Mini App payment detected: {payload} for user {user_id}")
            await self._handle_miniapp_successful_payment(
                update, context, user_id, payment, payload, parts
            )
            return

        # Handle regular Bot payments (existing logic)
        if len(parts) >= 3 and parts[0] == "key" and parts[1] == "slots":
            # ... existing slots logic ...
            return

        if len(parts) != 4 or parts[0] != "data":
            # ... existing error handling ...
            return

        # ... existing package delivery logic ...

    except Exception as e:
        logger.error(f"Error en successful_payment: {e}")
        if update.message:
            await update.message.reply_text(
                text=BuyGbMessages.Error.PAYMENT_FAILED, parse_mode="Markdown"
            )

async def _handle_miniapp_successful_payment(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    payment,
    payload: str,
    parts: list,
):
    """
    Handle successful payment from Mini App.

    For Mini App payments, we only register the payment in DB.
    The Mini App will handle delivery via polling.
    """
    try:
        # Extract transaction_id from payload
        # Format: miniapp_data_package_TYPE_USERID_TXID or miniapp_key_slots_N_USERID_TXID
        if payload.startswith("miniapp_data_package_"):
            # Parse: miniapp_data_package_basic_12345_abc123
            parts = payload.split("_")
            if len(parts) >= 6:
                package_type = parts[3]
                tx_id = parts[5]

                # Update DataPackage with payment confirmation
                async with get_session_context() as session:
                    package_repo = PostgresDataPackageRepository(session)
                    packages = await package_repo.get_all()

                    for pkg in packages:
                        if pkg.telegram_payment_id == f"miniapp_{tx_id}":
                            # Mark as paid (delivery happens via Mini App polling)
                            logger.info(f"✅ Mini App package payment registered: {tx_id}")
                            break

        elif payload.startswith("miniapp_key_slots_"):
            # Parse: miniapp_key_slots_3_12345_abc123
            parts = payload.split("_")
            if len(parts) >= 7:
                slots = int(parts[3])
                tx_id = parts[6]

                # Update user's max_keys
                async with get_session_context() as session:
                    user_repo = PostgresUserRepository(session)
                    user = await user_repo.get_by_id(user_id, user_id)
                    if user:
                        user.max_keys += slots
                        await user_repo.save(user, user_id)
                        logger.info(f"✅ Mini App slots payment registered: +{slots} slots")

        elif payload.startswith("miniapp_subscription_"):
            # Parse: miniapp_subscription_one_month_12345_abc123
            parts = payload.split("_")
            if len(parts) >= 6:
                plan_type = parts[2]
                tx_id = parts[5]

                # Activate subscription
                from application.services.subscription_service import SubscriptionService
                from application.services.common.container import get_service

                subscription_service = get_service(SubscriptionService)
                async with get_session_context() as session:
                    # Find and activate subscription
                    # ... subscription activation logic ...
                    logger.info(f"✅ Mini App subscription payment registered: {plan_type}")

        # Send confirmation message to user in Telegram
        await update.message.reply_text(
            text=f"✅ *Pago Recibido*\n\n"
                 f"Tu pago ha sido procesado exitosamente.\n\n"
                 f"📱 _Abre la Mini App para activar tu producto._",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🚀 Abrir Mini App",
                    url=f"https://t.me/{settings.BOT_USERNAME}/app"
                )
            ]])
        )

        logger.info(f"📬 Sent confirmation to user {user_id} for Mini App payment")

    except Exception as e:
        logger.error(f"Error in _handle_miniapp_successful_payment: {e}", exc_info=True)
        # Don't show error to user - payment was successful, just delivery failed
```

**Step 2: Add imports at top of file**

```python
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.data_package_repository import PostgresDataPackageRepository
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
```

**Step 3: Run existing tests to ensure no regression**

Run: `uv run pytest tests/telegram_bot/features/buy_gb/test_handlers_confirmation.py -v`
Expected: PASS (all existing tests still pass)

**Step 4: Add test for Mini App payment detection**

```python
class TestMiniAppPayment:
    """Tests for Mini App payment handling."""

    @pytest.mark.asyncio
    async def test_successful_payment_miniapp_package(self):
        """Test handling successful payment from Mini App."""
        # Mock update with Mini App payload
        mock_update = MagicMock()
        mock_update.effective_user.id = 12345
        mock_update.message.successful_payment.invoice_payload = "miniapp_data_package_basic_12345_txn123"
        mock_update.message.successful_payment.telegram_payment_charge_id = "charge_123"

        mock_context = AsyncMock()

        handler = ConfirmationMixin()
        await handler.successful_payment(mock_update, mock_context)

        # Verify confirmation message was sent
        mock_update.message.reply_text.assert_called()
        assert "✅ *Pago Recibido*" in mock_update.message.reply_text.call_args[1]["text"]
```

**Step 5: Commit**

```bash
git add telegram_bot/features/buy_gb/handlers_confirmation.py tests/telegram_bot/features/buy_gb/test_handlers_confirmation.py
git commit -m "feat: Detect and handle Mini App payments in Bot

- Add _handle_miniapp_successful_payment() method
- Detect Mini App payments by payload prefix 'miniapp_'
- Register payment in DB without immediate delivery
- Send confirmation message with Mini App link
- Mini App handles delivery via polling"
```

---

## Phase 3: Frontend - Auto-Polling for Payment Status

### Task 3.1: Update Purchase Page with Auto-Polling

**Files:**
- Modify: `miniapp/templates/purchase.html:260-400` (JavaScript section)
- Create: `miniapp/templates/purchase.html` (update loading overlay)

**Step 1: Add auto-polling logic to purchase.html**

```javascript
// Add after currentTransactionId declaration
let paymentPollingInterval = null;
let paymentCheckTimeout = null;

// Update payWithStars() function - replace the success handler
async function payWithStars() {
    // ... existing code until response ...

    if (!data.success) {
        console.error('[Payment] Server returned error:', data.error);
        Telegram.WebApp.showAlert('Error: ' + (data.error || 'No se pudo crear la factura'));
        return;
    }

    // Store transaction ID for tracking
    currentTransactionId = data.transaction_id;

    // Show success message with instructions
    Telegram.WebApp.showConfirm({
        title: '✅ Factura Enviada',
        message: 'Revisa tu chat de Telegram para completar el pago. La factura aparecerá en tu conversación con el bot.',
        confirmButtonText: 'Entendido',
        cancelButtonText: 'Cancelar'
    }, function(confirm) {
        if (confirm) {
            // Start polling for payment status
            startPaymentPolling(currentTransactionId);
        }
    });
}

// Add new polling function
function startPaymentPolling(transactionId) {
    console.log('[Payment] Starting polling for transaction:', transactionId);

    // Show waiting screen
    showPaymentWaitingScreen(transactionId);

    // Check immediately
    checkPaymentStatus(transactionId);

    // Then poll every 3 seconds
    paymentPollingInterval = setInterval(() => {
        checkPaymentStatus(transactionId);
    }, 3000);

    // Stop polling after 5 minutes (user can manually check later)
    paymentCheckTimeout = setTimeout(() => {
        stopPaymentPolling();
        Telegram.WebApp.showAlert(
            '⏰ Tiempo de espera agotado\\n\\n' +
            'Si completaste el pago pero no se activó automáticamente, ' +
            'puedes verificar el estado en tu perfil o contactar soporte.'
        );
    }, 5 * 60 * 1000); // 5 minutes
}

function stopPaymentPolling() {
    if (paymentPollingInterval) {
        clearInterval(paymentPollingInterval);
        paymentPollingInterval = null;
    }
    if (paymentCheckTimeout) {
        clearTimeout(paymentCheckTimeout);
        paymentCheckTimeout = null;
    }
}

async function checkPaymentStatus(transactionId) {
    try {
        const response = await fetch(`/api/v1/miniapp/api/payment-status/${transactionId}`, {
            headers: {
                'X-Telegram-Init-Data': Telegram.WebApp.initData
            }
        });

        const data = await response.json();
        console.log('[Payment] Status check:', data);

        if (data.success && data.status === 'completed') {
            // Payment detected!
            stopPaymentPolling();
            handlePaymentSuccess(data);
        } else if (data.status === 'failed' || data.status === 'expired') {
            // Payment failed
            stopPaymentPolling();
            handlePaymentFailed(data);
        }
        // Otherwise, keep polling (status is 'pending')

    } catch (error) {
        console.error('[Payment] Error checking status:', error);
        // Continue polling even if check fails
    }
}

function handlePaymentSuccess(data) {
    hidePaymentWaitingScreen();

    // Haptic feedback
    Telegram.WebApp.HapticFeedback.notificationOccurred('success');

    // Show success message
    Telegram.WebApp.showAlert(
        '✅ ¡Pago Completado!\\n\\n' +
        `Tu ${data.type === 'package' ? 'paquete de ' + data.data_gb + ' GB' : 'producto'} ` +
        'ha sido activado exitosamente.\\n\\n' +
        'Puedes verlo en tu perfil o en la sección de Claves.'
    );

    // Redirect to appropriate page after user acknowledges
    setTimeout(() => {
        window.location.href = '/api/v1/miniapp/profile';
    }, 1000);
}

function handlePaymentFailed(data) {
    hidePaymentWaitingScreen();

    // Haptic feedback
    Telegram.WebApp.HapticFeedback.notificationOccurred('error');

    Telegram.WebApp.showAlert(
        '❌ Pago Fallido\\n\\n' +
        'No pudimos detectar tu pago. Por favor:\\n' +
        '1. Verifica que completaste el pago en Telegram\\n' +
        '2. Revisa tu perfil para ver el estado\\n' +
        '3. Contacta soporte si necesitas ayuda'
    );
}

// Add waiting screen functions
function showPaymentWaitingScreen(transactionId) {
    const modal = document.createElement('div');
    modal.id = 'paymentWaitingModal';
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="text-align: center;">
            <div class="modal-header">
                <span class="modal-title">⏳ Esperando Pago</span>
            </div>
            <div class="modal-body">
                <div style="font-size: 48px; margin-bottom: 16px;">🔔</div>
                <div style="font-size: 16px; margin-bottom: 8px;">
                    Revisa tu Telegram para pagar
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 24px;">
                    La factura llegó a tu chat con el bot
                </div>
                <div class="loading"></div>
                <div class="loading-text" id="waitingText">
                    Verificando pago...
                </div>
                <div style="margin-top: 24px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                    <div style="font-size: 11px; color: var(--text-muted);">
                        Transaction ID: <code style="color: var(--accent-cyan);">${transactionId}</code>
                    </div>
                </div>
                <button class="btn btn-ghost btn-full" onclick="stopPaymentPolling(); document.getElementById('paymentWaitingModal').style.display='none';" style="margin-top: 16px;">
                    Cancelar Espera
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function hidePaymentWaitingScreen() {
    const modal = document.getElementById('paymentWaitingModal');
    if (modal) {
        modal.remove();
    }
}

// Cleanup polling when leaving page
window.addEventListener('beforeunload', function() {
    stopPaymentPolling();
});
```

**Step 2: Test manually in browser**

1. Open Mini App purchase page
2. Select a package
3. Click "Pagar con Stars"
4. Verify polling starts
5. Check console logs for status checks

**Step 3: Commit**

```bash
git add miniapp/templates/purchase.html
git commit -m "feat: Add auto-polling for payment status in Mini App

- Poll /api/payment-status/{tx_id} every 3 seconds
- Show waiting screen with instructions
- Auto-detect payment completion
- Redirect to profile on success
- Timeout after 5 minutes
- Cleanup on page unload"
```

---

## Phase 4: Transaction History Page

### Task 4.1: Create Dedicated Transactions Page

**Files:**
- Create: `miniapp/templates/transactions.html`
- Create: `infrastructure/api/routes/miniapp_payments.py:850-900` (HTML route)

**Step 1: Create transactions.html template**

```html
{% extends "base.html" %}

{% block title %}Historial de Transacciones - uSipipo VPN{% endblock %}

{% block content %}
<div class="glitch-title" style="margin-bottom: 20px;">Transacciones</div>

<div class="terminal-output">
    Historial completo de tus compras y pagos
</div>

<!-- Filters -->
<div class="card" style="margin-top: 20px;">
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button class="btn btn-sm btn-primary" onclick="filterTransactions('all')">Todos</button>
        <button class="btn btn-sm btn-secondary" onclick="filterTransactions('package')">Paquetes</button>
        <button class="btn btn-sm btn-secondary" onclick="filterTransactions('slots')">Slots</button>
        <button class="btn btn-sm btn-secondary" onclick="filterTransactions('subscription')">Suscripciones</button>
        <button class="btn btn-sm btn-secondary" onclick="filterTransactions('crypto')">Crypto</button>
    </div>
</div>

<!-- Transaction List -->
<div id="transactionsList" style="margin-top: 20px;">
    <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
        <div class="loading"></div>
        <div style="margin-top: 12px;">Cargando transacciones...</div>
    </div>
</div>

<!-- Pagination -->
<div id="pagination" style="margin-top: 20px; display: flex; justify-content: center; gap: 8px;">
    <!-- Dynamic content -->
</div>
{% endblock %}

{% block extra_js %}
<script>
let currentPage = 1;
let currentFilter = 'all';
let totalPages = 1;

async function loadTransactions(page = 1, filter = 'all') {
    const list = document.getElementById('transactionsList');
    list.innerHTML = `
        <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
            <div class="loading"></div>
            <div style="margin-top: 12px;">Cargando transacciones...</div>
        </div>
    `;

    try {
        let url = `/api/v1/miniapp/transactions?page=${page}&limit=20`;
        if (filter !== 'all') {
            url += `&type=${filter}`;
        }

        const response = await fetch(url, {
            headers: {
                'X-Telegram-Init-Data': Telegram.WebApp.initData
            }
        });

        const data = await response.json();

        if (!data.success || data.transactions.length === 0) {
            list.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                    <div>No tienes transacciones aún</div>
                    <div style="font-size: 12px; margin-top: 8px;">
                        Tus compras aparecerán aquí
                    </div>
                </div>
            `;
            return;
        }

        currentPage = data.pagination.page;
        totalPages = data.pagination.pages;

        let html = '';
        data.transactions.forEach(tx => {
            const statusClass = tx.status === 'completed' ? 'positive' :
                               tx.status === 'failed' ? 'negative' : 'pending';
            const statusText = tx.status === 'completed' ? '✅' :
                              tx.status === 'failed' ? '❌' : '⏳';

            html += `
                <div class="transaction-item" style="
                    background: var(--bg-tertiary);
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 12px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div style="flex: 1;">
                        <div style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">
                            ${tx.description}
                        </div>
                        <div style="font-size: 11px; color: var(--text-muted);">
                            ${new Date(tx.created_at).toLocaleDateString()} •
                            ${tx.payment_method === 'crypto' ? '💰 Crypto' : '⭐ Stars'}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 14px; font-weight: 600; color: ${tx.amount < 0 ? 'var(--accent-cyan)' : 'var(--accent-green)'};">
                            ${tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount)} ${tx.type === 'crypto' ? 'USDT' : '⭐'}
                        </div>
                        <div style="font-size: 11px; color: var(--text-secondary);">
                            ${statusText} ${tx.status}
                        </div>
                    </div>
                </div>
            `;
        });

        list.innerHTML = html;

        // Update pagination
        updatePagination(data.pagination);

    } catch (error) {
        console.error('Error loading transactions:', error);
        list.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                <div>Error al cargar transacciones</div>
                <button class="btn btn-primary" onclick="loadTransactions(${page}, '${filter}')" style="margin-top: 16px;">
                    Reintentar
                </button>
            </div>
        `;
    }
}

function updatePagination(pagination) {
    const container = document.getElementById('pagination');

    if (pagination.pages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';

    if (pagination.page > 1) {
        html += `<button class="btn btn-sm btn-secondary" onclick="loadTransactions(${pagination.page - 1}, '${currentFilter}')">← Anterior</button>`;
    }

    html += `<span style="color: var(--text-secondary); font-size: 12px; align-self: center;">
        Página ${pagination.page} de ${pagination.pages}
    </span>`;

    if (pagination.page < pagination.pages) {
        html += `<button class="btn btn-sm btn-secondary" onclick="loadTransactions(${pagination.page + 1}, '${currentFilter}')">Siguiente →</button>`;
    }

    container.innerHTML = html;
}

function filterTransactions(filter) {
    currentFilter = filter;
    loadTransactions(1, filter);

    // Update button styles
    document.querySelectorAll('.btn-sm').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
    });
    event.target.classList.remove('btn-secondary');
    event.target.classList.add('btn-primary');
}

// Load on page load
loadTransactions();
</script>

<style>
.transaction-item {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.transaction-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 240, 255, 0.1);
}
</style>
{% endblock %}
```

**Step 2: Add HTML route for transactions page**

```python
@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página de historial de transacciones."""
    logger.info(f"💳 User {ctx.user.id} accessed transactions page")
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "user": ctx.user,
            "bot_username": settings.BOT_USERNAME,
        },
    )
```

**Step 3: Add link to transactions page in navigation**

Update `miniapp/templates/base.html` to add transactions link in profile or settings.

**Step 4: Test manually**

1. Navigate to `/api/v1/miniapp/transactions`
2. Verify transactions load
3. Test pagination
4. Test filters

**Step 5: Commit**

```bash
git add miniapp/templates/transactions.html infrastructure/api/routes/miniapp_payments.py miniapp/templates/base.html
git commit -m "feat: Create dedicated transactions history page

- /api/v1/miniapp/transactions HTML page
- Paginated transaction list
- Filter by type (package, slots, subscription, crypto)
- Real-time loading with Telegram theme
- Responsive design"
```

---

## Phase 5: Testing & Documentation

### Task 5.1: Integration Tests

**Files:**
- Create: `tests/miniapp/test_payment_flow_integration.py`

**Step 1: Write end-to-end payment flow test**

```python
"""
Integration tests for complete Mini App payment flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.api.server import create_app
from infrastructure.api.routes.miniapp_common import get_current_user


class TestStarsPaymentFlow:
    """Test complete Stars payment flow."""

    @pytest.mark.asyncio
    async def test_full_stars_payment_flow(self):
        """Test: Select → Invoice → Pay → Detect → Deliver."""
        app = create_app()

        # Step 1: Create Stars invoice
        # Step 2: Verify invoice sent via Bot
        # Step 3: Simulate successful_payment in Bot
        # Step 4: Poll payment status
        # Step 5: Verify delivery

        # Full implementation in test file
        pass


class TestCryptoPaymentFlow:
    """Test complete Crypto payment flow."""

    @pytest.mark.asyncio
    async def test_full_crypto_payment_flow(self):
        """Test: Select → Create Order → Show QR → Webhook → Deliver."""
        pass


class TestTransactionHistory:
    """Test transaction history functionality."""

    @pytest.mark.asyncio
    async def test_transaction_history_pagination(self):
        """Test pagination works correctly."""
        pass

    @pytest.mark.asyncio
    async def test_transaction_history_filters(self):
        """Test filtering by type and status."""
        pass
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/miniapp/test_payment_flow_integration.py -v`
Expected: PASS (all integration tests)

**Step 3: Commit**

```bash
git add tests/miniapp/test_payment_flow_integration.py
git commit -m "test: Add integration tests for payment flow

- Test complete Stars payment flow
- Test complete Crypto payment flow
- Test transaction history pagination
- Test transaction history filters"
```

---

### Task 5.2: Update Documentation

**Files:**
- Modify: `docs/plans/2026-03-17-miniapp-api-migration.md` (add payment flow section)
- Create: `docs/PAYMENT_FLOW.md`

**Step 1: Create payment flow documentation**

```markdown
# Mini App Payment Flow

## Overview

The Mini App Web supports two payment methods:

1. **Telegram Stars** - Instant payments via Telegram
2. **Cryptocurrency (USDT/BSC)** - Blockchain payments via TronDealer

## Payment Flow Diagram

```
User → Select Product → Choose Method → Pay → System Detects → Deliver
```

## Telegram Stars Flow

1. User selects product in Mini App
2. Mini App calls `/api/create-stars-invoice`
3. Backend sends invoice via Telegram Bot
4. User pays in Telegram chat
5. Bot receives `successful_payment`
6. Backend registers payment in DB
7. Mini App polls `/api/payment-status/{tx_id}`
8. Mini App detects completion and delivers product

## Crypto Flow

1. User selects product in Mini App
2. Mini App calls `/api/create-crypto-order`
3. Backend creates CryptoOrder and returns QR code
4. User scans QR and pays USDT (BSC)
5. TronDealer webhook confirms payment
6. Backend updates CryptoOrder status
7. Mini App polls and detects completion
8. Backend delivers product

## Transaction History

- View at: `/api/v1/miniapp/transactions`
- Supports pagination and filtering
- Shows all payment types

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/create-stars-invoice` | Create Stars invoice |
| POST | `/api/create-crypto-order` | Create crypto order |
| GET | `/api/payment-status/{tx_id}` | Check payment status |
| GET | `/api/transactions` | Transaction history |
| POST | `/api/confirm-payment` | Manual confirmation (fallback) |
```

**Step 2: Commit**

```bash
git add docs/PAYMENT_FLOW.md
git commit -m "docs: Add payment flow documentation

- Document Stars payment flow
- Document Crypto payment flow
- Document transaction history
- API endpoint reference"
```

---

## Final Verification

### Task 6.1: Run All Tests

**Command:**
```bash
uv run pytest tests/miniapp/ -v --tb=short
```

**Expected:** All tests pass (53+ tests)

### Task 6.2: Manual Testing Checklist

- [ ] Select package in Mini App
- [ ] Pay with Stars (in Telegram)
- [ ] Verify auto-detection in Mini App
- [ ] Verify transaction appears in history
- [ ] Select package in Mini App
- [ ] Pay with Crypto (QR code)
- [ ] Verify webhook confirmation
- [ ] Verify auto-detection in Mini App
- [ ] Test pagination in transactions
- [ ] Test filters in transactions

### Task 6.3: Deploy to Staging

```bash
# Build and deploy
git push origin feature/miniapp-payment-flow
# Deploy via CI/CD
```

---

## Summary

This plan implements:

1. ✅ Payment status polling API
2. ✅ Transaction history with pagination
3. ✅ Bot integration for Mini App payments
4. ✅ Auto-polling frontend
5. ✅ Dedicated transactions page
6. ✅ Complete test coverage
7. ✅ Documentation

**Total Tasks:** 11
**Estimated Time:** 4-6 hours
**Files Modified:** 12
**Files Created:** 5
