# 09 — Módulo de Tickets y Soporte

## Objetivo
Permitir al usuario crear tickets de soporte, ver el historial de sus tickets y recibir respuestas del equipo, todo desde la APK, integrado con el sistema de tickets existente en el bot y backend.

---

## Pantalla: Lista de Tickets

```
┌─────────────────────────────────────┐
│  ← Soporte                  [+]     │  ← [+] crea nuevo ticket
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🟡 Ticket #TK-0042          │    │
│  │ "No puedo conectarme..."    │    │
│  │ Abierto · Hace 2 horas      │    │
│  │ Sin respuesta               │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🟢 Ticket #TK-0038          │    │
│  │ "Pregunta sobre paquetes"   │    │
│  │ Resuelto · 5 feb 2026       │    │
│  │ 2 mensajes                  │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🔴 Ticket #TK-0031          │    │
│  │ "Pago no procesado"         │    │
│  │ Cerrado · 20 ene 2026       │    │
│  │ 4 mensajes                  │    │
│  └─────────────────────────────┘    │
│                                     │
│  ── Sin más tickets ──              │
│                                     │
└─────────────────────────────────────┘
```

### Colores de Estado de Tickets
- 🟡 Amarillo: Abierto, esperando respuesta del equipo
- 🔵 Azul: En revisión, el equipo está trabajando
- 🟢 Verde: Resuelto
- 🔴 Rojo: Cerrado

---

## Pantalla: Crear Nuevo Ticket

```
┌─────────────────────────────────────┐
│  ← Nuevo Ticket de Soporte          │
├─────────────────────────────────────┤
│                                     │
│  Categoría del problema:            │
│                                     │
│  ○ Conexión VPN                     │
│  ○ Problema con pago                │
│  ○ Clave no funciona                │
│  ○ Error en la aplicación           │
│  ○ Pregunta general                 │
│  ○ Otro                             │
│                                     │
│  ────────────────────────────       │
│                                     │
│  Describe tu problema:              │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │ Escribe aquí...             │    │  ← MDTextField multiline
│  │                             │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│  (20/500 caracteres)                │
│                                     │
│  ℹ️ Incluye:                        │
│  • Qué intentaste hacer            │
│  • Qué pasó exactamente            │
│  • Tu tipo de dispositivo          │
│                                     │
│  [Cancelar]        [Enviar Ticket] │
└─────────────────────────────────────┘
```

---

## Flujo de Creación de Ticket

```
[Completa formulario]
        │
[Tap "Enviar Ticket"]
        │
        ▼
[Validaciones locales:]
- Categoría seleccionada
- Descripción mínimo 20 caracteres
- Descripción máximo 500 caracteres
        │
        ▼
[POST /api/v1/tickets/create]
{
  "category": "vpn_connection",
  "description": "No puedo conectarme...",
  "device_info": {
    "android_version": "13",
    "app_version": "1.0.0"
  }
}
        │
        ▼
[Backend crea ticket en DB]
[Backend notifica a admins por bot]
        │
        ▼
[Snackbar: "✅ Ticket #TK-0043 creado"]
[Navega al detalle del ticket nuevo]
```

El campo `device_info` se incluye automáticamente para ayudar al equipo de soporte a diagnosticar problemas. Se obtiene de las APIs de Android disponibles en Python-for-Android.

---

## Pantalla: Detalle de Ticket (conversación)

```
┌─────────────────────────────────────┐
│  ← Ticket #TK-0042                  │
│  🟡 Abierto                         │
├─────────────────────────────────────┤
│                                     │
│  Conexión VPN · 10 feb 2026         │
│                                     │
│  ────────────────────────────       │
│                                     │
│  [👤 TÚ]  hace 2 horas              │
│  ┌─────────────────────────────┐    │
│  │ No puedo conectarme a la    │    │
│  │ VPN desde esta mañana.      │    │
│  │ Antes funcionaba bien.      │    │
│  │ Tengo Outline instalado.    │    │
│  └─────────────────────────────┘    │
│                                     │
│  [🛡️ SOPORTE]  hace 1 hora          │
│  ┌─────────────────────────────┐    │
│  │ Hola! Vimos tu ticket.      │    │
│  │ ¿Puedes indicarnos qué      │    │
│  │ versión de Android tienes?  │    │
│  │ Gracias.                    │    │
│  └─────────────────────────────┘    │
│                                     │
│  ─────────────────────────────      │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Escribe tu respuesta...     │    │
│  └─────────────────────────────┘    │
│  [Enviar]                           │
│                                     │
│  [Marcar como resuelto]             │
└─────────────────────────────────────┘
```

---

## Flujo de Respuesta a Ticket

```
[Escribe respuesta]
[Tap "Enviar"]
        │
        ▼
[POST /api/v1/tickets/{ticket_id}/reply]
{message: "Tengo Android 13..."}
        │
        ▼
[Mensaje aparece en la conversación]
[Auto-scroll al final]
[Campo de texto se limpia]
```

---

## Flujo de Cerrar Ticket

```
[Tap "Marcar como resuelto"]
        │
        ▼
[MDDialog: "¿Marcar como resuelto?
  Esto cerrará el ticket.
  Podrás ver el historial pero
  no podrás responder más."]
[Cancelar]  [Resolver]
        │
        ▼
[PUT /api/v1/tickets/{ticket_id}/resolve]
        │
        ▼
[Estado cambia a 🟢 Resuelto]
[Snackbar: "Ticket marcado como resuelto"]
[Campo de respuesta se deshabilita]
```

---

## Notificación de Respuesta a Ticket

Cuando un admin responde un ticket, el sistema del bot de Telegram ya envía una notificación al chat del usuario. Adicionalmente, la APK detecta respuestas nuevas mediante polling:

```
Cada 30 segundos (si la APK está activa):
GET /api/v1/tickets/unread-count

Si count > 0:
→ Muestra badge rojo en el ícono de Soporte del menú
→ Notificación local de Android: "Nueva respuesta en tu ticket #TK-0042"
```

---

## Integración con el Sistema de Tickets Existente

El backend ya tiene el módulo completo de tickets (`ticket_service.py`, `ticket_repository.py`, modelos, etc.). La APK simplemente consume los endpoints REST del módulo `/api/v1/tickets/` que se construirá sobre esa infraestructura existente. No se duplica lógica.

Los tickets creados desde la APK son visibles para los admins exactamente igual que los creados desde el bot de Telegram o el mini app web, ya que todos comparten la misma tabla `tickets` en PostgreSQL.
