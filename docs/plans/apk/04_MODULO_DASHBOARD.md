# 04 — Módulo Dashboard

## Objetivo
Pantalla principal post-login. Debe dar al usuario una visión rápida del estado de su cuenta: datos disponibles, claves activas, saldo de referidos y acceso rápido a las funciones más usadas.

---

## Layout de la Pantalla

```
┌─────────────────────────────────────┐
│  [≡]  uSipipo VPN      [@username]  │  ← TopBar con menú y avatar
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │
│  │  👋 Hola, [nombre]          │    │  ← Card de bienvenida
│  │  Último acceso: hace 2h     │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌──────────────┐  ┌─────────────┐  │
│  │ 📊 DATOS     │  │ 🔑 CLAVES  │  │  ← Cards de resumen
│  │ 3.2 GB       │  │ 2 activas  │  │
│  │ de 5 GB      │  │ max: 2     │  │
│  │ [====    ]   │  │            │  │
│  └──────────────┘  └─────────────┘  │
│                                     │
│  ┌──────────────┐  ┌─────────────┐  │
│  │ ⭐ REFERIDOS │  │ 💳 PAQUETE │  │
│  │ 12 créditos  │  │ Estándar   │  │
│  │              │  │ Vence: 15d │  │
│  └──────────────┘  └─────────────┘  │
│                                     │
│  ─── Acciones Rápidas ───           │
│                                     │
│  ┌────────┐ ┌────────┐ ┌─────────┐  │
│  │ Nueva  │ │Comprar │ │ Soporte │  │
│  │ Clave  │ │  GB    │ │        │  │
│  └────────┘ └────────┘ └─────────┘  │
│                                     │
│  ─── Últimas Claves ───             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🔵 Mi iPhone · Outline     │    │
│  │ 1.2 GB usados · Activa     │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🟣 Mi PC · WireGuard        │    │
│  │ 450 MB usados · Activa     │    │
│  └─────────────────────────────┘    │
│                                     │
├─────────────────────────────────────┤
│  [🏠]    [🔑]    [💰]    [👤]      │  ← BottomNavigation
│  Inicio  Claves  Comprar  Perfil    │
└─────────────────────────────────────┘
```

---

## Componentes del Dashboard

### TopBar
- Botón menú hamburguesa (izquierda): abre NavigationDrawer con opciones secundarias
- Logo "uSipipo VPN" centrado con efecto neon cyan
- Avatar del usuario (derecha): foto de Telegram si disponible, sino iniciales con fondo magenta. Al tocarlo va al módulo de Perfil.

### Card de Bienvenida
- Saludo personalizado con nombre de Telegram
- Último acceso formateado en relativo ("hace 2 horas", "ayer", etc.)
- Si el usuario tiene deuda pendiente (`has_pending_debt = True`), esta card se reemplaza por una alerta roja: "⚠️ Tienes una deuda pendiente. Tu servicio puede suspenderse."

### Cards de Resumen (Grid 2x2)

**Card Datos:**
- Muestra el consumo total sumado de todas las claves activas
- Barra de progreso con color que cambia: cyan (< 60%), ámbar (60-85%), rojo (> 85%)
- Si tiene paquete activo, muestra los datos del paquete. Si no, muestra datos gratuitos (5 GB)
- Al tocar: navega a la pantalla de Claves

**Card Claves:**
- Número de claves activas vs máximo permitido
- Indicador visual: puntos de colores por cada clave
- Al tocar: navega a Claves VPN

**Card Referidos:**
- Créditos de referidos acumulados
- Número de referidos con compra completada
- Al tocar: navega a la pantalla de Referidos en Perfil

**Card Paquete:**
- Si tiene paquete activo: tipo (Básico/Estándar/Avanzado/Premium), días restantes
- Si no tiene paquete: "Sin paquete activo" con botón "Comprar"
- Días en rojo si quedan menos de 3 días
- Al tocar: navega a Compras

### Sección Acciones Rápidas
Tres botones con ícono y texto corto:
- **Nueva Clave** → Módulo Crear Clave
- **Comprar GB** → Módulo Compras
- **Soporte** → Módulo Tickets

### Lista Últimas Claves
- Muestra máximo 3 claves (las más recientes)
- Cada item: ícono de tipo (azul=Outline, morado=WireGuard), nombre, uso, estado
- Enlace "Ver todas →" al final si hay más de 3
- Al tocar una clave: navega al Detalle de Clave

### BottomNavigation
Barra fija en la parte inferior con 4 tabs:
- 🏠 Inicio (Dashboard)
- 🔑 Claves (Lista de claves VPN)
- 💰 Comprar (Catálogo de paquetes)
- 👤 Perfil (Cuenta y configuración)

---

## Flujo de Carga del Dashboard

```
[Entra al Dashboard]
        │
        ▼
[Muestra skeleton loader]
(placeholders con animación shimmer)
        │
        ▼
[GET /api/v1/dashboard/summary]
Respuesta:
{
  "user": {name, username, photo_url},
  "data_usage": {used_bytes, limit_bytes},
  "active_keys": [{id, name, type, used_bytes, is_active}],
  "active_package": {type, expires_at} | null,
  "referral_credits": int,
  "has_pending_debt": bool,
  "last_login": datetime
}
        │
        ▼
[Renderiza todas las cards]
[Oculta skeleton loader]
        │
        ▼
[Pull-to-refresh habilitado]
[Auto-refresh cada 60 segundos en background]
```

---

## Estados Especiales del Dashboard

### Estado: Usuario Suspendido
Si `user.status == "suspended"`, se muestra un overlay sobre el dashboard con:
- Ícono de candado rojo
- Mensaje: "Cuenta suspendida. Contacta soporte."
- Botón único: "Ir a Soporte"
- El BottomNavigation queda deshabilitado excepto Perfil

### Estado: Sin Conexión a Internet
- Banner rojo en la parte superior: "Sin conexión. Los datos pueden no estar actualizados."
- Las cards muestran los últimos datos cacheados (si existen)
- Ícono de refresh parpadeante

### Estado: Modo Consumo Activo
Si `consumption_mode_enabled == True`:
- La card de datos muestra un ícono especial ⚡ y el texto "Modo Pay-as-you-go activo"
- El color de la barra de datos cambia a ámbar permanentemente
- Se muestra el balance actual del ciclo de consumo

---

## Cache Local del Dashboard

Para mejorar la experiencia cuando hay conexión lenta, se cachea la última respuesta del dashboard en un archivo JSON local encriptado. Al abrir la APK, se muestran los datos cacheados inmediatamente mientras se carga la versión fresca del servidor. El cache tiene un TTL de 15 minutos.
