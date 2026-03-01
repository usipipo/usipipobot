# TronDealer V2 — Acepta pagos en stablecoins en minutos

Guia paso a paso para integrar pagos automaticos en USDT y USDC en BSC, Ethereum y Polygon.

---

## Que es TronDealer?

TronDealer es una pasarela de pagos crypto para negocios B2B. Genera wallets unicas por cliente, detecta depositos automaticamente, te notifica via webhook y consolida los fondos en tu wallet principal. Sin intermediarios, sin custodia prolongada, sin friccion.

**Flujo resumido:**

```
Tu cliente deposita USDT/USDC → TronDealer lo detecta → Tu servidor recibe un webhook → Los fondos llegan a tu wallet
```

---

## Paso 1: Registra tu negocio

Ve a [trondealer.com/onboard](https://trondealer.com/onboard) y completa el formulario:

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| **Business Name** | Nombre de tu empresa | `Mi Tienda Online` |
| **Webhook URL** | Endpoint HTTPS donde recibiras notificaciones | `https://mi-tienda.com/api/webhooks/crypto` |
| **Destination Wallet** | Wallet EVM donde se consolidaran tus fondos (opcional) | `0xABC...123` |
| **Webhook Secret** | Clave para verificar la firma HMAC de los webhooks (opcional) | `mi-secreto-super-seguro` |
| **Min Confirmations** | Bloques de confirmacion antes de notificar (default segun red) | `15` |
| **Networks** | Redes a monitorear (opcional, default: las 3) | `["bsc","eth","pol"]` |

Completa el CAPTCHA y haz clic en **Registrar**.

Al registrarte recibiras dos credenciales:

- **Business ID** — UUID que identifica tu cuenta (ej: `550e8400-e29b-41d4-a716-446655440000`)
- **API Key** — Clave de acceso con prefijo `td_` (ej: `td_a1b2c3d4e5f6...`)

> **IMPORTANTE:** Guarda tu API Key en un lugar seguro. No se mostrara de nuevo.

---

## Paso 2: Configura tu entorno

Guarda tus credenciales como variables de entorno:

```bash
export TRONDEALER_BUSINESS_ID="550e8400-e29b-41d4-a716-446655440000"
export TRONDEALER_API_KEY="td_a1b2c3d4e5f6..."
```

Todas las llamadas a la API se autentican con el header `x-api-key`:

```bash
curl -H "x-api-key: $TRONDEALER_API_KEY" \
     -H "Content-Type: application/json" \
     https://trondealer.com/api/v2/clients/me
```

---

## Paso 3: Genera wallets de deposito

Cada vez que un cliente necesite pagar, genera una wallet unica para el:

```bash
curl -X POST https://trondealer.com/api/v2/clients/me/wallets/assign \
  -H "x-api-key: $TRONDEALER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"label": "order-4521"}'
```

**Respuesta:**

```json
{
  "success": true,
  "wallet": {
    "id": "660e8400-e29b-41d4-a716-446655440111",
    "address": "0x7F2a3B4c5D6e7F8a9B0c1D2e3F4a5B6c7D8e9F0a",
    "label": "order-4521",
    "status": "active",
    "created_at": "2025-02-25T10:35:00Z"
  }
}
```

Muestra la direccion `address` a tu cliente para que deposite USDT o USDC. La misma direccion funciona en las 3 redes soportadas (BSC, Ethereum, Polygon).

> Puedes crear hasta **50 wallets** por cuenta. El campo `label` es opcional pero util para asociar la wallet a un pedido o usuario.

---

## Paso 4: Tu cliente deposita

Tu cliente envia USDT o USDC a la direccion generada desde cualquier wallet compatible con EVM (MetaMask, Trust Wallet, Binance, etc) por cualquiera de las redes habilitadas: BSC, Ethereum o Polygon.

No necesitas hacer nada. TronDealer escanea las blockchains automaticamente.

---

## Paso 5: Recibe el webhook

Cuando el deposito alcanza las confirmaciones configuradas, tu endpoint recibe un POST:

```
POST https://mi-tienda.com/api/webhooks/crypto
Content-Type: application/json
X-Signature-256: sha256=abc123def456...
```

```json
{
  "event": "transaction.confirmed",
  "timestamp": "2025-02-25T10:40:00Z",
  "data": {
    "tx_hash": "0xabc123def456789...",
    "block_number": 45123456,
    "from_address": "0x...",
    "to_address": "0x7F2a3B4c5D6e7F8a9B0c1D2e3F4a5B6c7D8e9F0a",
    "asset": "USDT",
    "amount": "100.00",
    "confirmations": 15,
    "wallet_label": "order-4521",
    "network": "bsc"
  }
}
```

### Verifica la firma (recomendado)

Si configuraste un `webhook_secret`, verifica el header `X-Signature-256` para asegurarte de que la notificacion es autentica:

```javascript
const crypto = require('crypto');

function verifyWebhook(req, webhookSecret) {
  const payload = JSON.stringify(req.body);
  const signature = crypto
    .createHmac('sha256', webhookSecret)
    .update(payload)
    .digest('hex');

  const expected = `sha256=${signature}`;
  const received = req.headers['x-signature-256'];

  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(received)
  );
}
```

```python
import hmac, hashlib, json

def verify_webhook(payload: bytes, header: str, secret: str) -> bool:
    signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    expected = f"sha256={signature}"
    return hmac.compare_digest(expected, header)
```

### Ejemplo de handler en Node.js

```javascript
app.post('/api/webhooks/crypto', (req, res) => {
  // 1. Verificar firma
  if (!verifyWebhook(req, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }

  // 2. Procesar el pago
  const { tx_hash, amount, asset, wallet_label, network } = req.body.data;
  console.log(`Pago recibido: ${amount} ${asset} en ${network} para ${wallet_label}`);

  // 3. Marcar el pedido como pagado en tu base de datos
  // await db.orders.update({ id: wallet_label }, { status: 'paid' });

  // 4. Responder 200 para confirmar recepcion
  res.status(200).send('OK');
});
```

> TronDealer reintenta hasta **5 veces** si tu endpoint no responde con HTTP 2xx. Timeout: 10 segundos por intento.

---

## Paso 6: Los fondos se consolidan automaticamente

Despues de la notificacion, TronDealer mueve automaticamente los fondos a tu wallet de destino (la que configuraste como `sweep_wallet`, o la wallet principal del sistema si no configuraste una).

No necesitas intervenir. El proceso incluye:
1. Fondeo automatico de gas (BNB/ETH/POL segun la red) si la wallet no tiene suficiente
2. Transferencia de USDT/USDC a tu wallet de destino
3. Recuperacion del token nativo restante

---

## Consultas utiles

### Ver tus wallets

```bash
curl https://trondealer.com/api/v2/clients/me/wallets \
  -H "x-api-key: $TRONDEALER_API_KEY"
```

### Consultar balance en tiempo real

```bash
curl -X POST https://trondealer.com/api/v2/clients/me/wallets/balance \
  -H "x-api-key: $TRONDEALER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address": "0x7F2a3B4c5D6e7F8a9B0c1D2e3F4a5B6c7D8e9F0a"}'
```

```json
{
  "success": true,
  "balances": {
    "bsc": { "BNB": "0.0042", "USDT": "150.50", "USDC": "0.00" },
    "eth": { "ETH": "0.001", "USDT": "0.00", "USDC": "0.00" },
    "pol": { "POL": "0.5", "USDT": "10.00", "USDC": "0.00" }
  }
}
```

### Listar transacciones

Puedes filtrar por `status` y por `network`:

```bash
curl -X POST https://trondealer.com/api/v2/wallets/transactions \
  -H "x-api-key: $TRONDEALER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"address": "0x7F2a3B4c...", "status": "confirmed", "network": "eth"}'
```

### Ver estadisticas generales

```bash
curl https://trondealer.com/api/v2/clients/me/stats \
  -H "x-api-key: $TRONDEALER_API_KEY"
```

```json
{
  "success": true,
  "stats": {
    "total_wallets": 12,
    "total_transactions": 89,
    "total_by_asset": {
      "USDT": 45230.50,
      "USDC": 12875.00
    },
    "total_by_network": {
      "bsc": 38100.00,
      "eth": 15005.50,
      "pol": 5000.00
    },
    "transactions_by_status": {
      "detected": 2,
      "confirmed": 5,
      "notified": 8,
      "swept": 74
    }
  }
}
```

### Actualizar configuracion

```bash
curl -X PATCH https://trondealer.com/api/v2/clients/me \
  -H "x-api-key: $TRONDEALER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://nueva-url.com/webhook",
    "min_confirmations": 20,
    "sweep_wallet": "0xNUEVA_WALLET...",
    "networks": ["bsc", "eth"]
  }'
```

---

## Dashboard

Tambien puedes gestionar todo desde el panel web:

1. Inicia sesion en [trondealer.com/login](https://trondealer.com/login) con tu Business ID y API Key
2. Desde el dashboard puedes:
   - Ver wallets activas y sus balances
   - Monitorear transacciones en tiempo real
   - Revisar el historial de webhooks enviados
   - Actualizar tu configuracion (webhook URL, wallet de destino, confirmaciones)

---

## Ciclo de vida de una transaccion

```
DEPOSITO ──→ DETECTED ──→ CONFIRMED ──→ NOTIFIED ──→ SWEPT
               │              │             │           │
          Se detecta     Se alcanzan    Webhook      Fondos
          el tx en la    las confir-    enviado a    movidos a
          blockchain     maciones       tu servidor  tu wallet
```

Tiempos estimados hasta confirmacion segun red:

| Red | Confirmaciones default | Tiempo aprox. |
|-----|----------------------|---------------|
| BSC | 15 | ~45 segundos |
| Ethereum | 12 | ~2.5 minutos |
| Polygon | 30 | ~1 minuto |

| Estado | Significado |
|--------|-------------|
| `detected` | Deposito encontrado, esperando confirmaciones |
| `confirmed` | Confirmaciones suficientes, listo para notificar |
| `notified` | Webhook enviado exitosamente a tu endpoint |
| `swept` | Fondos transferidos a tu wallet de destino |

---

## Redes y tokens soportados

| Token | BSC (BNB Chain) | Ethereum | Polygon |
|-------|----------------|----------|---------|
| USDT | BEP-20 (18 dec) | ERC-20 (6 dec) | ERC-20 (6 dec) |
| USDC | BEP-20 (18 dec) | ERC-20 (6 dec) | ERC-20 (6 dec) |

Una misma wallet funciona en las 3 redes (son direcciones EVM compatibles). Solo necesitas generar la wallet una vez.

---

## Seguridad

- **Sin custodia prolongada**: los fondos se consolidan automaticamente despues de cada notificacion
- **Firma HMAC**: cada webhook puede llevar firma SHA-256 para verificar autenticidad
- **HTTPS obligatorio**: las webhook URLs deben ser HTTPS
- **API Keys seguras**: 64 bytes de entropia, nunca almacenadas en cookies
- **Sesiones seguras**: tokens HMAC con comparacion de tiempo constante

---

## Preguntas frecuentes

**Puedo usar la misma wallet para varios pagos?**
Si, pero se recomienda generar una wallet por transaccion para identificar facilmente quien pago.

**Que pasa si mi webhook endpoint esta caido?**
TronDealer reintenta hasta 5 veces. Puedes ver los intentos fallidos en el dashboard o via la API `/clients/me/webhooks`.

**Mi cliente puede pagar por cualquier red?**
Si. La misma direccion de wallet funciona en BSC, Ethereum y Polygon. TronDealer detecta el deposito en cualquiera de las redes que tengas habilitadas y te notifica con el campo `network` indicando por donde llego.

**Cuanto tardan las confirmaciones?**
Depende de la red: ~45s en BSC (15 bloques), ~2.5 min en Ethereum (12 bloques), ~1 min en Polygon (30 bloques).

**Puedo elegir en que redes operar?**
Si. Al registrarte o via `PATCH /clients/me` puedes configurar el campo `networks` con las redes que quieras: `["bsc"]`, `["bsc","eth"]`, `["bsc","eth","pol"]`, etc.

**Puedo cambiar mi wallet de destino?**
Si, en cualquier momento via la API (`PATCH /clients/me`) o desde el dashboard. La misma wallet de destino se usa para el sweep en todas las redes.

**Hay limite de wallets?**
Maximo 50 wallets por cuenta.

**Cuanto cuesta?**
El gas (BNB) para el sweep se fondea automaticamente. Contactanos para planes y pricing.
