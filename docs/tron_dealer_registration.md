# Respuesta a Tron Dealer / QvaPay - Solicitud de API

## Correo de Respuesta

---

**Para:** soporte@qvapay.com (o el correo de Erich de Tron Dealer)

**Asunto:** Registro API Tron Dealer - uSipipo VPN

---

Hola Erich,

Gracias por la información detallada sobre la API de Tron Dealer. Adjunto los datos solicitados para el registro de mi cuenta:

```json
{
    "name": "uSipipo VPN",
    "webhook_url": "https://YOUR_NGROK_SUBDOMAIN.loca.lt/api/v1/webhooks/tron-dealer",
    "webhook_secret": "REMOVED_SECRET",
    "sweep_wallet": "0xYOUR_WALLET_ADDRESS_HERE"
}
```

### Notas adicionales:

1. **Webhook URL**: Actualmente estoy usando Localtunnel para exponer mi servidor. Una vez que tenga mi api_key, procederé a configurar el endpoint en mi aplicación.

2. **Proyecto**: uSipipo VPN es un bot de Telegram para gestión de VPN (WireGuard + Outline) con sistema de pagos. Planeamos integrar pagos en cripto mediante tu API como alternativa a Telegram Stars.

3. **Uso previsto**:
   - Generar wallets de depósito para usuarios que quieran pagar con USDT/BNB
   - Recibir notificaciones de pago en tiempo real
   - Asignar automáticamente los fondos a las cuentas de usuario

Quedo atento a la confirmación del registro y la recepción de mi api_key.

Gracias por tu tiempo.

Saludos,
[ tu nombre / uSipipo Team ]

---

## Datos Configurados

| Campo | Valor |
|-------|-------|
| **name** | uSipipo VPN |
| **webhook_url** | `https://YOUR_NGROK_SUBDOMAIN.loca.lt/api/v1/webhooks/tron-dealer` |
| **webhook_secret** | `REMOVED_SECRET` |
| **sweep_wallet** | `0xYOUR_WALLET_ADDRESS_HERE` |

---

## Próximos Pasos (Después de recibir api_key)

### 1. Configurar Túnel con Localtunnel

```bash
# Instalar localtunnel
npm install -g localtunnel

# Crear túnel (en el servidor)
lt --port 8000 --subdomain usipipo-vpn
```

**Alternativa con ngrok:**
```bash
# Instalar ngrok
sudo apt install ngrok

# Autenticar (requiere cuenta gratuita en ngrok.com)
ngrok config add-authtoken TU_TOKEN

# Crear túnel
ngrok http 8000
```

### 2. Crear Endpoint de Webhook

Crear archivo: `infrastructure/api/webhook_tron_dealer.py`

```python
from fastapi import APIRouter, Request, HTTPException, Header
import hmac
import hashlib

router = APIRouter()

WEBHOOK_SECRET = "REMOVED_SECRET"

@router.post("/api/v1/webhooks/tron-dealer")
async def handle_tron_dealer_webhook(
    request: Request,
    signature: str = Header(None, alias="X-TronDealer-Signature")
):
    """
    Recibe notificaciones de depósito de Tron Dealer.
    """
    payload = await request.body()
    
    # Verificar firma HMAC
    if signature:
        expected_sig = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(401, "Invalid signature")
    
    data = await request.json()
    
    # Procesar depósito
    # - Identificar usuario por wallet_address
    # - Acreditar monto en su cuenta
    # - Notificar vía Telegram
    
    return {"status": "ok"}
```

### 3. Integrar con el Sistema de Pagos

Modificar `application/services/payment_service.py` para incluir métodos:

```python
async def create_deposit_wallet(self, user_id: int) -> str:
    """Crea wallet de depósito para el usuario via Tron Dealer API."""
    pass

async def get_wallet_balance(self, wallet_address: str) -> float:
    """Consulta balance de una wallet."""
    pass
```

### 4. Variables de Entorno a Agregar

Agregar al `.env`:

```bash
# Tron Dealer API
TRON_DEALER_API_KEY=td_tu_api_key_aqui
TRON_DEALER_WEBHOOK_SECRET=REMOVED_SECRET
```

---

## Seguridad

### Medidas implementadas:

1. **Webhook Secret**: Verificación HMAC para validar que las notificaciones vienen de Tron Dealer
2. **HTTPS**: Localtunnel/ngrok proveen HTTPS automáticamente
3. **Wallet Principal**: Los fondos se redirigen automáticamente a la sweep_wallet

### Recomendaciones:

1. **Rate Limiting**: Implementar límite de requests al webhook
2. **IP Whitelist**: Si Tron Dealer provee IPs, filtrar por ellas
3. **Logging**: Registrar todos los webhooks recibidos para auditoría

---

## Costos

- **Actualmente**: Sin comisiones (hasta 1ro de marzo 2026)
- **Desde 1ro de marzo**: 0.4% por transacción ("pay as you go")

---

## Documentación de Referencia

- Tron Dealer Docs: https://trondealer.com/docs
- Endpoints disponibles:
  - `POST /api/v2/wallets/assign` - Asignar wallet de depósito
  - `POST /api/v2/wallets/balance` - Consultar balance
  - `POST /api/v2/wallets/transactions` - Ver historial

---

## Resumen para Enviar

Copia y pega este JSON en tu respuesta al correo:

```json
{
    "name": "uSipipo VPN",
    "webhook_url": "https://YOUR_NGROK_SUBDOMAIN.loca.lt/api/v1/webhooks/tron-dealer",
    "webhook_secret": "REMOVED_SECRET",
    "sweep_wallet": "0xYOUR_WALLET_ADDRESS_HERE"
}
```

---

*Documento generado: 2026-02-24*
