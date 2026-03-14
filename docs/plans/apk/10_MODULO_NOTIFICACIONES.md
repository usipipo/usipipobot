# 10 — Módulo de Notificaciones

## Objetivo
Mantener al usuario informado sobre eventos importantes de su cuenta (datos agotándose, pagos confirmados, tickets respondidos) sin depender de servicios de push externos de pago como Firebase FCM, usando un sistema de polling inteligente y notificaciones locales de Android.

---

## Decisión de Arquitectura: Polling vs Push

### ¿Por qué polling y no Firebase FCM (Push)?
Firebase Cloud Messaging es gratuito pero requiere:
- Una cuenta Google con proyecto Firebase configurado
- Integrar el SDK de Firebase en Python-for-Android (complejo, pesado)
- El servidor backend necesita credenciales de servicio de Google para enviar notificaciones

Para la versión inicial de la APK, el polling inteligente es suficiente y más sencillo de implementar. Se puede migrar a FCM en una versión futura si el volumen de usuarios lo justifica.

### Estrategia de Polling
- **Activo** (APK en foreground): polling cada 30 segundos
- **Background** (APK minimizada): Android WorkManager con período de 15 minutos
- **Inactivo** (APK cerrada): notificación push vía bot de Telegram (ya implementado)

---

## Eventos que Generan Notificaciones

### Nivel CRÍTICO (notificación inmediata, sonido + vibración)
- Pago confirmado exitosamente (Stars o USDT)
- Datos al 100% - límite alcanzado
- Cuenta suspendida

### Nivel IMPORTANTE (notificación normal, solo vibración)
- Datos al 90% del límite
- Paquete vence en menos de 3 días
- Nueva respuesta en ticket de soporte
- Referido completó su primera compra

### Nivel INFORMATIVO (solo badge, sin sonido)
- Datos al 75% del límite
- Paquete vence en menos de 7 días

---

## Diagrama de Flujo del Sistema de Notificaciones

```
APK en FOREGROUND:
┌────────────────────────────────────────┐
│  Timer cada 30 segundos                │
│         │                              │
│         ▼                              │
│  GET /api/v1/notifications/pending     │
│         │                              │
│  [Lista de eventos pendientes]         │
│         │                              │
│  ¿Hay eventos?                         │
│  ├── NO → Espera 30s → Repite          │
│  └── SÍ → Procesa cada evento:         │
│         │                              │
│         ├── Muestra Snackbar en UI     │
│         ├── Genera notificación local  │
│         └── POST /notifications/ack    │
│             {ids: [1,2,3]}             │
└────────────────────────────────────────┘

APK en BACKGROUND (Android WorkManager):
┌────────────────────────────────────────┐
│  WorkManager: PeriodicWorkRequest      │
│  Período: 15 minutos                   │
│         │                              │
│         ▼                              │
│  GET /api/v1/notifications/pending     │
│         │                              │
│  ¿Hay eventos críticos/importantes?    │
│  ├── NO → Termina el worker            │
│  └── SÍ → Muestra notificación nativa │
│           Android (status bar)         │
│         │                              │
│         └── POST /notifications/ack    │
└────────────────────────────────────────┘
```

---

## Estructura de Notificación desde el Backend

El endpoint `GET /api/v1/notifications/pending` retorna:

```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "data_warning",
      "level": "important",
      "title": "Datos casi agotados",
      "body": "Tu clave 'Mi iPhone' tiene solo 500 MB restantes",
      "created_at": "2026-02-15T14:00:00Z",
      "data": {
        "key_id": "uuid",
        "used_bytes": 4831838208,
        "limit_bytes": 5368709120
      }
    },
    {
      "id": "uuid",
      "type": "payment_confirmed",
      "level": "critical",
      "title": "¡Pago confirmado!",
      "body": "Tu paquete Estándar (15 GB) ya está activo",
      "created_at": "2026-02-15T13:55:00Z",
      "data": {
        "package_type": "estandar",
        "order_id": "uuid"
      }
    }
  ]
}
```

---

## Notificaciones Locales de Android

La APK usa el sistema de notificaciones nativo de Android a través de Python-for-Android. Las notificaciones se agrupan por canal:

### Canales de Notificación Android

**Canal: "Pagos" (ID: payments)**
- Importancia: IMPORTANCE_HIGH
- Sonido: Sí
- Vibración: Sí
- Ejemplos: pago confirmado, pago fallido

**Canal: "Datos VPN" (ID: data_usage)**
- Importancia: IMPORTANCE_DEFAULT
- Sonido: Solo para críticos (100%)
- Vibración: Sí
- Ejemplos: 75%, 90%, 100% de datos usados

**Canal: "Soporte" (ID: support)**
- Importancia: IMPORTANCE_DEFAULT
- Sonido: Sí
- Vibración: Sí
- Ejemplos: respuesta en ticket

**Canal: "Referidos" (ID: referrals)**
- Importancia: IMPORTANCE_LOW
- Sonido: No
- Vibración: No
- Ejemplos: referido hizo compra

---

## Configuración de Notificaciones por el Usuario

El usuario puede ajustar qué notificaciones recibe desde la sub-pantalla de Notificaciones del Perfil (ver `08_MODULO_PERFIL_CUENTA.md`). Estas preferencias se guardan localmente en la APK (no en el servidor, son preferencias de UI).

---

## Badges de Notificación en la UI

En la barra de navegación inferior, los ítems pueden mostrar badges numéricos:

- **Tab "Claves":** muestra badge rojo si alguna clave tiene datos al 90%+
- **Tab "Comprar":** muestra badge si el paquete vence en menos de 3 días
- **Tab "Perfil":** muestra badge si hay tickets sin leer

Los badges se actualizan en cada ciclo de polling.

---

## Notificaciones del Bot de Telegram (Canal Paralelo)

El bot de Telegram ya envía notificaciones directamente al chat del usuario para varios eventos. La APK y el bot **no se duplican notificaciones**. La estrategia es:

- Si la APK tiene la notificación pendiente y la lee primero → la marca como leída en el backend → el backend no la envía por bot
- Si la APK está inactiva por más de 30 minutos → el backend envía la notificación por bot como fallback

Esto requiere que el backend marque las notificaciones con `source: "apk_pending"` y tenga un job que envíe por bot las que llevan más de 30 minutos sin ser leídas.
