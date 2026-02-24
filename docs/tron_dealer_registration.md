# Respuesta a Tron Dealer / QvaPay - Solicitud de API

## ✅ WEBHOOK IMPLEMENTADO Y FUNCIONAL

---

## Correo de Respuesta

**Para:** soporte@qvapay.com (o el correo de Erich de Tron Dealer)

**Asunto:** Registro API Tron Dealer - uSipipo VPN

---

Hola Erich,

Gracias por la información detallada sobre la API de Tron Dealer. He implementado el webhook endpoint en mi servidor y está listo para recibir notificaciones.

Adjunto los datos solicitados para el registro de mi cuenta:

```json
{
    "name": "uSipipo VPN",
    "webhook_url": "https://YOUR_NGROK_SUBDOMAIN.loca.lt/api/v1/webhooks/tron-dealer",
    "webhook_secret": "GENERAR_CON_OPENSSL_RAND_HEX_32",
    "sweep_wallet": "0xYOUR_WALLET_ADDRESS_HERE"
}
```

### Sobre el webhook

El endpoint está implementado con las siguientes capas de seguridad:

1. **Verificación HMAC** - Valida firma de los webhooks entrantes
2. **Protección contra replay attacks** - Nonce tracking con expiración
3. **Validación de timestamp** - Rechaza requests con drift > 5 minutos
4. **Rate limiting** - 60 requests/min por IP
5. **Security headers** - HSTS, X-Frame-Options, X-Content-Type-Options

### Información adicional

- **Webhook URL**: Usaré ngrok para exponer el servidor localmente
- **Proyecto**: uSipipo VPN es un bot de Telegram para gestión de VPN con pagos integrados
- **Uso**: Integrar pagos en cripto como alternativa a Telegram Stars

Quedo atento a la confirmación del registro y la recepción de mi api_key.

Gracias,
uSipipo Team

---

## Datos Configurados

| Campo | Valor |
|-------|-------|
| **name** | uSipipo VPN |
| **webhook_url** | `https://YOUR_NGROK_SUBDOMAIN.loca.lt/api/v1/webhooks/tron-dealer` |
| **webhook_secret** | `GENERAR_CON_OPENSSL_RAND_HEX_32` |
| **sweep_wallet** | `0xYOUR_WALLET_ADDRESS_HERE` |

---

## Para iniciar el webhook

```bash
# 1. Agregar NGROK_AUTH_TOKEN al .env (obtener en ngrok.com)

# 2. Iniciar el bot (incluye API server en puerto 8000)
python main.py

# El bot iniciará automáticamente el túnel ngrok si NGROK_AUTH_TOKEN está configurado
```

---

## Tests de Seguridad Pasados

```
✅ Health check OK
✅ HMAC signature verification OK
✅ Invalid signature rechazado (401)
✅ Invalid payload rechazado (422)
✅ SQL Injection bloqueado
✅ XSS bloqueado
✅ Rate limiting funcionando
✅ Security headers presentes
```

---

## Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/tron-dealer` | Recibe webhooks de Tron Dealer |
| GET | `/api/v1/webhooks/tron-dealer/health` | Health check del webhook |
| GET | `/health` | Health check general de la API |

---

## Variables de entorno configuradas

```bash
# .env
TRON_DEALER_API_KEY=              # Se completará al recibir api_key
TRON_DEALER_WEBHOOK_SECRET=GENERAR_CON_OPENSSL_RAND_HEX_32
TRON_DEALER_SWEEP_WALLET=0xYOUR_WALLET_ADDRESS_HERE
NGROK_AUTH_TOKEN=                 # Tu token de ngrok.com
NGROK_SUBDOMAIN=usipipo-vpn
```

---

## Documentación de Referencia

- Tron Dealer Docs: https://trondealer.com/docs
- Endpoints disponibles:
  - `POST /api/v2/wallets/assign` - Asignar wallet de depósito
  - `POST /api/v2/wallets/balance` - Consultar balance
  - `POST /api/v2/wallets/transactions` - Ver historial

---

## Costos

- **Actualmente**: Sin comisiones (hasta 1ro de marzo 2026)
- **Desde 1ro de marzo**: 0.4% por transacción ("pay as you go")

---

*Documento actualizado: 2026-02-24 - Webhook implementado y probado*
