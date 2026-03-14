# 07 — Módulo de Compras

## Objetivo
Permitir al usuario comprar paquetes de datos (GB) usando Telegram Stars o USDT, con un flujo claro, seguro y que nunca deje al usuario sin saber en qué estado está su pago.

---

## Pantalla: Catálogo de Paquetes

```
┌─────────────────────────────────────┐
│  ← Comprar GB                       │
├─────────────────────────────────────┤
│                                     │
│  Elige tu paquete:                  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ⚡ BÁSICO                   │    │
│  │ 5 GB · 30 días              │    │
│  │ ⭐ 50 Stars · $0.90 USDT   │    │
│  │                  [Comprar] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🚀 ESTÁNDAR    ★ POPULAR   │    │  ← Badge "popular"
│  │ 15 GB · 30 días             │    │
│  │ ⭐ 130 Stars · $2.50 USDT  │    │
│  │                  [Comprar] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 💎 AVANZADO                │    │
│  │ 30 GB · 30 días             │    │
│  │ ⭐ 250 Stars · $4.80 USDT  │    │
│  │                  [Comprar] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 👑 PREMIUM                 │    │
│  │ 50 GB · 30 días             │    │
│  │ ⭐ 400 Stars · $7.50 USDT  │    │
│  │                  [Comprar] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ∞  SIN LÍMITE               │    │
│  │ Ilimitado · 30 días         │    │
│  │ ⭐ 900 Stars · $16.00 USDT │    │
│  │                  [Comprar] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ── Información ──                  │
│  • Los paquetes se acumulan         │
│  • Sin vencimiento anticipado       │
│  • Soporte 24/7 incluido            │
│                                     │
└─────────────────────────────────────┘
```

---

## Pantalla: Selección de Método de Pago

Al tocar "Comprar" en cualquier paquete:

```
┌─────────────────────────────────────┐
│  Paquete Estándar · 15 GB           │
│                                     │
│  ¿Cómo quieres pagar?               │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ⭐ TELEGRAM STARS           │    │
│  │ 130 Stars                   │    │
│  │ Pago instantáneo desde      │    │
│  │ tu billetera de Telegram    │    │
│  │                  [Pagar ⭐] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 💵 USDT (TRC-20 / TRON)     │    │
│  │ $2.50 USDT                  │    │
│  │ Transferencia cripto        │    │
│  │ Confirmación: ~1-3 min      │    │
│  │                  [Pagar 💵] │    │
│  └─────────────────────────────┘    │
│                                     │
│  [Cancelar]                         │
└─────────────────────────────────────┘
```

---

## Flujo de Pago con Telegram Stars

```
[Tap "Pagar ⭐ Stars"]
        │
        ▼
[POST /api/v1/payments/stars/create]
{
  "package_type": "estandar",
  "telegram_id": 123456789
}
        │
        ▼
Backend genera:
{
  "deep_link": "tg://resolve?domain=uSipipoBot&start=pay_estandar_uuid",
  "order_id": "uuid",
  "stars_amount": 130
}
        │
        ▼
[MDDialog de instrucciones]
┌─────────────────────────────────────┐
│ Pagar con Telegram Stars            │
│                                     │
│ Se abrirá Telegram para completar   │
│ el pago de 130 Stars.               │
│                                     │
│ ✓ Tu paquete se activará           │
│   automáticamente al pagar         │
│                                     │
│ [Cancelar]    [Abrir Telegram →]   │
└─────────────────────────────────────┘
        │
[Tap "Abrir Telegram →"]
        │
        ▼
[Abre Deep Link: tg://...]
(Android abre Telegram app)
        │
        ▼
[APK queda en background]
[Inicia polling de estado]

POLLING cada 3 segundos:
GET /api/v1/payments/stars/status/{order_id}

┌────────────────┐
│ Loop (max 5min)│
└───────┬────────┘
        │
        ▼
[Estado: "pending"] → Continúa polling
[Estado: "paid"]    → Éxito
[Estado: "expired"] → Error
        │
[APK vuelve al foreground]
        │
        ▼
[Pantalla de confirmación de pago]
```

---

## Pantalla: Esperando Pago Stars

```
┌─────────────────────────────────────┐
│  ⭐ Esperando confirmación...       │
│                                     │
│  [Animación circular pulsante]      │
│                                     │
│  Completa el pago en Telegram       │
│  y vuelve aquí automáticamente      │
│                                     │
│  Paquete: Estándar · 15 GB          │
│  Monto: 130 Stars                   │
│                                     │
│  ⏱️ Tiempo restante: 4:47           │
│                                     │
│  ─────────────────────────────      │
│                                     │
│  [Abrir Telegram de nuevo]          │
│  [Cancelar pago]                    │
└─────────────────────────────────────┘
```

---

## Flujo de Pago con USDT

```
[Tap "Pagar 💵 USDT"]
        │
        ▼
[POST /api/v1/payments/crypto/create]
{
  "package_type": "estandar",
  "telegram_id": 123456789
}
        │
        ▼
Backend responde:
{
  "order_id": "uuid",
  "wallet_address": "TXx...ABC",
  "amount_usdt": "2.50",
  "amount_exact": "2.500000",
  "network": "TRC-20 (TRON)",
  "expires_at": "2026-02-15T15:30:00Z",
  "qr_data": "tron:TXx...ABC?amount=2.5"
}
```

---

## Pantalla: Pago USDT

```
┌─────────────────────────────────────┐
│  💵 Pago con USDT                   │
├─────────────────────────────────────┤
│                                     │
│  Envía exactamente:                 │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │  2.500000 USDT              │    │  ← JetBrains Mono, grande
│  │  Red: TRC-20 (TRON)         │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
│  A esta dirección:                  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │     [QR CODE]               │    │
│  └─────────────────────────────┘    │
│                                     │
│  TXx...ABC123def456             │    │
│  [📋 Copiar dirección]              │
│                                     │
│  ⚠️ IMPORTANTE:                     │
│  • Envía el monto EXACTO           │
│  • Solo red TRC-20 (TRON)          │
│  • No envíes ERC-20 (Ethereum)     │
│                                     │
│  ⏱️ Pago válido por: 14:32         │
│                                     │
│  Estado: 🟡 Esperando transferencia │
│                                     │
│  [Cancelar pago]                    │
└─────────────────────────────────────┘
```

### Estados del Pago USDT

```
POLLING cada 5 segundos:
GET /api/v1/payments/crypto/status/{order_id}

Estados posibles:
─────────────────────────────────────
"pending"     → 🟡 Esperando transferencia
"detected"    → 🔵 Transferencia detectada, confirmando...
"confirmed"   → 🟢 Confirmado en blockchain
"paid"        → ✅ ¡Pago exitoso! (activa paquete)
"expired"     → ❌ Expirado (15 minutos sin pago)
"failed"      → ❌ Error (monto incorrecto, red incorrecta)
```

---

## Pantalla: Confirmación de Pago Exitoso (ambos métodos)

```
┌─────────────────────────────────────┐
│                                     │
│         🎉                          │
│   ¡Pago exitoso!                    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  Paquete ESTÁNDAR activado  │    │
│  │                             │    │
│  │  📊 15 GB disponibles       │    │
│  │  📅 Válido por 30 días      │    │
│  │  ✅ Activo ahora            │    │
│  └─────────────────────────────┘    │
│                                     │
│  Tu VPN ya tiene más datos.         │
│  ¡Disfruta la navegación!           │
│                                     │
│  [Ver mis datos]  [Ir al inicio]    │
└─────────────────────────────────────┘
```

La pantalla tiene una animación de confetti o partículas neon para celebrar el pago.

---

## Flujo de Cancelación de Pago

Si el usuario toca "Cancelar pago" en cualquiera de los flujos:

```
[MDDialog de confirmación]
"¿Cancelar el pago?"

Stars: "El proceso de pago se cancelará."
USDT: "¿Ya enviaste el USDT? Si ya enviaste
       el dinero, espera la confirmación.
       ¿Seguro que quieres cancelar?"

[No, seguir esperando]   [Sí, cancelar]
        │
        ▼
[POST /api/v1/payments/cancel/{order_id}]
[Vuelve al catálogo de paquetes]
```

---

## Historial de Compras

Accessible desde el menú de Perfil. Muestra todas las transacciones con:
- Fecha
- Tipo de paquete
- Método de pago (Stars / USDT)
- Estado (exitoso / expirado / cancelado)
- Monto pagado

Endpoint: `GET /api/v1/payments/history?page=1&limit=20`
