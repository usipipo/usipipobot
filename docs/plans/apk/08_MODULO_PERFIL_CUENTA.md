# 08 — Módulo Perfil y Cuenta

## Objetivo
Centralizar toda la información y configuración de la cuenta del usuario: datos personales de Telegram, gestión de billetera USDT, sistema de referidos, historial de compras y ajustes de la APK.

---

## Pantalla: Perfil Principal

```
┌─────────────────────────────────────┐
│  ← Mi Cuenta                        │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │
│  │  [Foto/Avatar]              │    │
│  │  Juan Pérez                 │    │
│  │  @juanperez                 │    │
│  │  ID: 123456789              │    │
│  │  Miembro desde: Ene 2026    │    │
│  │  Estado: ● Activo           │    │
│  └─────────────────────────────┘    │
│                                     │
│  ─── Mi Plan ───                    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 📦 Sin paquete activo       │    │
│  │ Datos gratuitos: 3.2/5 GB  │    │
│  │          [Comprar paquete] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ─── Cuenta ───                     │
│                                     │
│  [👥] Referidos            [→]      │
│  [💳] Billetera USDT       [→]      │
│  [📋] Historial de compras  [→]      │
│  [🔑] Mis claves VPN        [→]      │
│  [🎫] Soporte / Tickets     [→]      │
│                                     │
│  ─── Aplicación ───                 │
│                                     │
│  [🔔] Notificaciones        [→]      │
│  [🎨] Tema                  [→]      │
│  [🌐] Idioma (Español)      [→]      │
│  [ℹ️] Acerca de uSipipo     [→]      │
│                                     │
│  ─── Sesión ───                     │
│                                     │
│  [🚪] Cerrar sesión                 │
│                                     │
└─────────────────────────────────────┘
```

---

## Sub-pantalla: Referidos

```
┌─────────────────────────────────────┐
│  ← Programa de Referidos            │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │
│  │  👥 Tus estadísticas        │    │
│  │                             │    │
│  │  Referidos totales: 5       │    │
│  │  Con compra: 3              │    │
│  │  Créditos ganados: 12 ⭐    │    │
│  └─────────────────────────────┘    │
│                                     │
│  Tu código de referido:             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  ABC123XY                   │    │  ← JetBrains Mono
│  │  [📋 Copiar]  [📤 Compartir]│    │
│  └─────────────────────────────┘    │
│                                     │
│  Tu enlace de referido:             │
│  https://t.me/uSipipoBot?start=...  │
│  [📋 Copiar enlace]                 │
│                                     │
│  ─── Cómo funciona ───             │
│                                     │
│  1️⃣  Comparte tu código             │
│  2️⃣  Tu amigo activa el bot        │
│  3️⃣  Cuando hace su primera        │
│      compra, tú ganas créditos      │
│                                     │
│  Con créditos puedes:               │
│  • Eliminar claves VPN              │
│  • Desbloquear funciones extra      │
│                                     │
└─────────────────────────────────────┘
```

---

## Sub-pantalla: Billetera USDT

```
┌─────────────────────────────────────┐
│  ← Mi Billetera USDT                │
├─────────────────────────────────────┤
│                                     │
│  Dirección de pago guardada:        │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │  TXabc...def123             │    │  ← Truncada
│  │                             │    │
│  │  [📋 Copiar] [✏️ Editar]    │    │
│  └─────────────────────────────┘    │
│                                     │
│  ℹ️ Esta es tu dirección de         │
│  pago. Los pagos USDT se            │
│  verifican desde esta dirección.    │
│                                     │
│  ─── Actualizar dirección ───       │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Nueva dirección TRC-20:     │    │
│  │ [                          ]│    │
│  └─────────────────────────────┘    │
│                                     │
│  ⚠️ Asegúrate de que sea una        │
│  dirección TRC-20 (TRON) válida.    │
│  Las direcciones incorrectas        │
│  pueden causar pérdida de fondos.   │
│                                     │
│  [Guardar dirección]                │
└─────────────────────────────────────┘
```

### Flujo de Actualización de Wallet

```
[Ingresa nueva dirección]
        │
        ▼
[Validación local: formato TRC-20]
¿Empieza con "T"? ¿Tiene 34 caracteres?
        │
  ┌─────┴─────┐
  │ Inválida  │ Válida
  ▼           ▼
[Error     [MDDialog: "¿Confirmar
 inline]    cambio de billetera?
            Nueva: TXabc...
            [Cancelar] [Confirmar]"]
                │
                ▼
        [PUT /api/v1/user/wallet]
        {wallet_address: "TX..."}
                │
                ▼
        [Snackbar: "Billetera actualizada"]
```

---

## Sub-pantalla: Historial de Compras

```
┌─────────────────────────────────────┐
│  ← Historial de Compras             │
├─────────────────────────────────────┤
│                                     │
│  Febrero 2026                       │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ✅ Paquete Estándar         │    │
│  │ 15 GB · 30 días             │    │
│  │ ⭐ 130 Stars                │    │
│  │ 10 feb 2026 · 14:23        │    │
│  └─────────────────────────────┘    │
│                                     │
│  Enero 2026                         │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ✅ Paquete Básico           │    │
│  │ 5 GB · 30 días              │    │
│  │ 💵 0.90 USDT                │    │
│  │ 15 ene 2026 · 09:10        │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ❌ Pago cancelado           │    │
│  │ Paquete Avanzado            │    │
│  │ 💵 4.80 USDT (no pagado)    │    │
│  │ 12 ene 2026 · 20:05        │    │
│  └─────────────────────────────┘    │
│                                     │
│         [Cargar más]                │
└─────────────────────────────────────┘
```

---

## Sub-pantalla: Configuración de Notificaciones

```
┌─────────────────────────────────────┐
│  ← Notificaciones                   │
├─────────────────────────────────────┤
│                                     │
│  Notificaciones push:               │
│                                     │
│  Datos casi agotados (90%)  [  ●  ] │
│  Paquete próximo a vencer   [  ●  ] │
│  Pago confirmado            [  ●  ] │
│  Tickets respondidos        [  ●  ] │
│  Referido realizó compra    [  ●  ] │
│                                     │
│  ─── Polling de fondo ───           │
│                                     │
│  Actualización automática:  [  ●  ] │
│  Cada: [15 min ▼]                   │
│                                     │
│  ℹ️ El polling consume batería.     │
│  Recomendado: 15 o 30 minutos.      │
│                                     │
└─────────────────────────────────────┘
```

---

## Sub-pantalla: Acerca de uSipipo

```
┌─────────────────────────────────────┐
│  ← Acerca de uSipipo                │
├─────────────────────────────────────┤
│                                     │
│       [Logo uSipipo]                │
│       uSipipo VPN                   │
│       Versión 1.0.0                 │
│                                     │
│  [📜] Términos de servicio  [→]     │
│  [🔒] Política de privacidad [→]    │
│  [📞] Contactar soporte     [→]     │
│  [⭐] Calificar la app      [→]     │
│                                     │
│  ── Ecosistema ──                   │
│  [🤖] Bot en Telegram       [→]     │
│  [🌐] Mini App Web          [→]     │
│                                     │
│  ── Legal ──                        │
│  © 2026 uSipipo. Todos los         │
│  derechos reservados.               │
│                                     │
└─────────────────────────────────────┘
```

---

## Flujo de Cierre de Sesión

```
[Tap "Cerrar sesión"]
        │
        ▼
[MDDialog de confirmación]
"¿Cerrar sesión?"
"Tendrás que ingresar tu código
 de Telegram para volver a entrar."
[Cancelar]   [Cerrar sesión]
        │
        ▼
[POST /api/v1/auth/logout]
{Authorization: Bearer <jwt>}
        │
        ▼
[Backend: agrega jti a blacklist en Redis]
        │
        ▼
[APK: elimina JWT del keystore]
[APK: limpia cache local]
        │
        ▼
[Navega a Splash Screen]
```
