# Mini App Payment Flow Fix - Telegram Bot Integration

## Problem

The Telegram Mini App was failing when processing payments (both Stars and Crypto) because:

1. **Stars Payments**: The Mini App was trying to generate `tg://invoice` URLs directly, which don't work in a web context within a Mini App.

2. **Crypto Payments**: No notifications were sent to users in Telegram when crypto orders were created or confirmed.

3. **User Experience**: Users had no confirmation in Telegram when purchasing from the Mini App.

## Solution

Implemented a **Bot-Centric Payment Flow** where all payment notifications and confirmations are sent through the Telegram Bot.

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Mini App   │────▶│  FastAPI     │────▶│  Telegram   │
│  (Web UI)   │     │  Backend     │     │  Bot        │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │                    │
       │                   ▼                    ▼
       │            ┌──────────────┐     ┌─────────────┐
       │            │ Notification │     │   User      │
       │            │ Service      │     │   Chat      │
       │            └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  Payment    │
│  Confirmed  │
│  in Bot     │
└─────────────┘
```

## Changes Made

### 1. New Service: `MiniAppNotificationService`

**File**: `miniapp/services/miniapp_notification_service.py`

Service for sending notifications from Mini App to Telegram users via the Bot.

```python
class MiniAppNotificationService:
    async def send_stars_invoice(...) -> bool
    async def send_crypto_payment_notification(...) -> bool
    async def send_payment_confirmation(...) -> bool
    async def send_payment_pending(...) -> bool
```

### 2. API Server Initialization

**File**: `infrastructure/api/server.py`

Initialize the notification service with a Telegram Bot instance on API startup:

```python
bot = Bot(token=settings.TELEGRAM_TOKEN)
init_notification_service(bot)
```

### 3. Updated Payment Routes

**File**: `miniapp/routes_payments.py`

#### Stars Invoice Creation
- **Before**: Generated `tg://invoice` URL and returned to Mini App
- **After**: Sends invoice via Telegram Bot, returns success message

```python
# Send invoice via Telegram Bot
invoice_sent = await notification_service.send_stars_invoice(
    user_id=ctx.user.id,
    title=title,
    description=description,
    payload=payload,
    amount=amount,
)
```

#### Crypto Order Creation
- **Before**: Created order and returned QR code data only
- **After**: Creates order + sends notification with QR code to Telegram

```python
await notification_service.send_crypto_payment_notification(
    user_id=ctx.user.id,
    order_id=order_data.get("order_id"),
    wallet_address=wallet_address,
    amount_usdt=amount_usdt,
    qr_code_url=qr_code_url,
    product_name=product_name,
)
```

#### Payment Confirmation
- **Added**: Telegram notification after successful payment confirmation
- Sends confirmation message with product details to user

### 4. Bot Handler Updates

**File**: `telegram_bot/features/buy_gb/handlers_confirmation.py`

#### Pre-Checkout Handler
- Added support for Mini App payment payloads (`data_package_*`, `key_slots_*`)

#### Successful Payment Handler
- Routes Mini App payments to dedicated handler
- Separate confirmation messages for Mini App vs regular bot payments

#### New: `_handle_miniapp_payment`
Dedicated handler for Mini App payments:
- Parses payload format: `data_package_TYPE_USERID_TXID` or `key_slots_N_USERID_TXID`
- Processes package or slots purchase
- Sends formatted confirmation message

### 5. Crypto Payment Service Updates

**File**: `application/services/crypto_payment_service.py`

#### New Method: `_send_crypto_confirmation_notification`
Sends confirmation message when crypto payment is processed:

```python
async def _send_crypto_confirmation_notification(
    self,
    user_id: int,
    product_name: str,
    amount_usdt: float,
) -> bool
```

#### Updated: `_credit_user`
- Calls notification method after successful slots purchase
- Calls notification method after successful package purchase

### 6. Mini App UI Updates

**File**: `miniapp/templates/purchase.html`

#### Stars Payment Flow
```javascript
async function payWithStars() {
    // 1. Call API to create invoice
    const response = await fetch('/miniapp/api/create-stars-invoice', ...);
    
    // 2. Show confirmation dialog
    Telegram.WebApp.showConfirm({
        title: '✅ Factura Enviada',
        message: 'Revisa tu chat de Telegram para completar el pago...'
    });
    
    // 3. User opens Telegram to pay
}
```

#### Crypto Payment Flow
```javascript
async function payWithCrypto() {
    // 1. Call API to create crypto order
    const response = await fetch('/miniapp/api/create-crypto-order', ...);
    
    // 2. Show confirmation with option to view in Telegram
    Telegram.WebApp.showConfirm({
        title: '💰 Orden Crypto Creada',
        message: 'La información de pago ha sido enviada a tu Telegram...'
    });
}
```

## Payment Flows

### Stars Payment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User selects package in Mini App                             │
│    └─> Clicks "Comprar Ahora"                                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Mini App calls POST /api/create-stars-invoice                │
│    Body: { product_type: "package", product_id: "basic" }       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Backend sends invoice via Telegram Bot                       │
│    Bot.send_invoice(chat_id=user_id, ...)                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Backend returns success message                              │
│    { success: true, message: "Factura enviada...", ... }        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Mini App shows confirmation dialog                           │
│    "Revisa tu chat de Telegram para completar el pago"          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. User opens Telegram and sees invoice                         │
│    └─> Clicks "Pay" button                                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Bot processes successful_payment handler                     │
│    └─> Calls _handle_miniapp_payment()                          │
│    └─> Purchases package/slots                                  │
│    └─> Sends confirmation message                               │
└─────────────────────────────────────────────────────────────────┘
```

### Crypto Payment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User selects package in Mini App                             │
│    └─> Clicks "Pagar con Crypto"                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Mini App calls POST /api/create-crypto-order                 │
│    Body: { product_type: "package", product_id: "basic" }       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Backend creates crypto order                                 │
│    └─> Assigns wallet to user                                   │
│    └─> Creates order in database                                │
│    └─> Generates QR code                                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Backend sends notification to Telegram                       │
│    Bot.send_photo(chat_id=user_id,                              │
│                     photo=qr_code,                              │
│                     caption=payment_info)                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Backend returns order data to Mini App                       │
│    { success: true,                                             │
│      wallet_address: "...",                                     │
│      amount_usdt: 1.25,                                         │
│      qr_code_url: "/miniapp/static/qr/..." }                    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Mini App shows confirmation                                  │
│    "La información de pago ha sido enviada a tu Telegram"       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. User opens Telegram and sees QR code + wallet info           │
│    └─> Sends USDT to wallet                                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. TronDealer webhook notifies backend                          │
│    └─> process_webhook_payment()                                │
│    └─> Credits user account                                     │
│    └─> Sends confirmation message                               │
└─────────────────────────────────────────────────────────────────┘
```

## Testing

All tests pass:

```bash
# Mini App payment endpoint tests
pytest tests/miniapp/test_payment_endpoints.py -v
# Result: 19 passed

# Bot payment handler tests
pytest tests/telegram_bot/features/buy_gb/ -v -k payment
# Result: All passed
```

## Files Modified

| File | Changes |
|------|---------|
| `miniapp/services/miniapp_notification_service.py` | **NEW** - Notification service |
| `miniapp/routes_payments.py` | Updated payment routes to use notification service |
| `infrastructure/api/server.py` | Initialize notification service on startup |
| `telegram_bot/features/buy_gb/handlers_confirmation.py` | Added Mini App payment handlers |
| `application/services/crypto_payment_service.py` | Added crypto confirmation notifications |
| `miniapp/templates/purchase.html` | Updated UI flow for Telegram payments |
| `tests/miniapp/test_payment_endpoints.py` | Updated tests to mock notification service |

## Benefits

1. **Reliable Payments**: Uses proven bot payment infrastructure
2. **Better UX**: Users receive all payment info in Telegram chat
3. **Consistent Flow**: Same payment experience across bot and Mini App
4. **Notifications**: Users get notified at every payment stage
5. **Error Handling**: Bot can handle payment errors gracefully

## Migration Notes

- **No breaking changes** for existing bot payments
- Mini App payments now use payload format: `data_package_TYPE_USERID_TXID`
- Regular bot payments continue using: `data_package_TYPE_USERID`

## Future Enhancements

1. Add payment status polling endpoint for Mini App
2. Implement webhook for real-time payment status updates
3. Add payment history view in Mini App
4. Support multiple payment methods (PayPal, etc.)
