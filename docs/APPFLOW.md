# Application Flow (APPFLOW)

Este documento describe los flujos principales de la aplicación uSipipo Bot.

---

## 1. Diagrama de Flujo General

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO INICIA BOT                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     COMANDO /start                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              ¿Usuario ya está registrado?                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │ Sí                      │ No
              ▼                         ▼
┌──────────────────────┐    ┌───────────────────────────────┐
│ Mostrar Menú         │    │ Crear nuevo usuario en BD     │
│ Principal            │    │ Enviar mensaje de bienvenida  │
└──────────┬───────────┘    └───────────────┬───────────────┘
           │                                │
           └────────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MENÚ PRINCIPAL                           │
│  [Crear Nueva] [Mis Claves] [Comprar GB] [Soporte]          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Selección de acción  │
              └───────────┬────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ FLUJO CREAR  │  │ FLUJO MIS    │  │ FLUJO COMPRAR│
│ CLAVE VPN    │  │ CLAVES       │  │ GB           │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 2. Estados del Usuario

### 2.1 Estados Principales
| Estado | Descripción | Transiciones |
|--------|-------------|--------------|
| `IDLE` | Estado inicial/default | Cualquier comando |
| `SELECT_TYPE` | Seleccionando tipo de VPN (WireGuard/Outline) | Nombre/Cancelar |
| `INPUT_NAME` | Ingresando nombre para la clave | Confirmar/Cancelar |
| `VIEWING_KEYS` | Viendo lista de claves | Eliminar/Detalles/Volver |
| `BUYING_GB` | En proceso de compra | Confirmar/Cancelar |
| `DEPOSIT_AMOUNT` | Seleccionando monto de depósito | Confirmar/Cancelar |
| `SELECTING_AMOUNT` | Seleccionando cantidad | Método/Cancelar |
| `SELECTING_METHOD` | Seleccionando método de pago | Confirmar/Cancelar |
| `CONFIRMING_PAYMENT` | Confirmando pago | Pagar/Cancelar |
| `ADMIN_MENU` | En menú de administración | Ver usuarios/Ver claves/Volver |
| `VIEWING_USERS` | Viendo lista de usuarios | Detalles/Volver |
| `VIEWING_KEYS` | Viendo claves de usuario | Eliminar/Volver |
| `DELETING_KEY` | Confirmando eliminación de clave | Confirmar/Cancelar |

> **Nota:** Los estados `SUPPORT_CHAT`, `PLAYING_GAME`, `REFERRAL_VIEW` están planificados para futuras versiones.

### 2.2 Diagrama de Estados

```
                    ┌──────────┐
           ┌───────│   IDLE   │◄─────────────────┐
           │       └────┬─────┘                  │
           │            │                        │
    ┌──────▼─────┐ ┌────▼─────┐ ┌──────────┐  ┌─┴──────────┐
    │  SELECT    │ │ INPUT    │ │ VIEWING  │  │   BUYING   │
    │   TYPE     │ │  NAME    │ │  KEYS    │  │    GB      │
    └──────┬─────┘ └────┬─────┘ └────┬─────┘  └─────┬──────┘
           │            │            │              │
           └────────────┴────────────┴──────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │  Return  │
                        │  to IDLE │
                        └──────────┘
```

---

## 3. Flujo de Compra de GB

### 3.1 Diagrama de Secuencia

```
Usuario          Bot              Sistema          Telegram API
  │                │                  │                  │
  │───"Comprar GB"──>│                  │                  │
  │                │                  │                  │
  │                │───Validar user──>│                  │
  │                │<───User data─────│                  │
  │                │                  │                  │
  │<──Mostrar packs──│                │                  │
  │                │                  │                  │
  │──Seleccionar pack─>│              │                  │
  │                │                  │                  │
  │                │──Crear invoice───│                  │
  │                │─────────────────────────────────────>│
  │                │                  │                  │
  │                │<─────────────────────────────────────│
  │                │    Invoice URL                      │
  │                │                  │                  │
  │<──Mostrar pago──│                │                  │
  │   (Stars)      │                  │                  │
  │                │                  │                  │
  │═══════════════════════════════════════════════════════│
  │           [USUARIO PAGA EN TELEGRAM]                  │
  │═══════════════════════════════════════════════════════│
  │                │                  │                  │
  │                │<─────────────────────────────────────│
  │                │    Payment Success Webhook          │
  │                │                  │                  │
  │                │───Update balance─>│                  │
  │                │                  │                  │
  │<──Confirmación──│                │                  │
```

### 3.2 Paquetes de GB Disponibles

| Paquete | GB | Precio (Stars) | Bonificación |
|---------|----|----------------|--------------|
| Básico | 5 | 50 | - |
| Estándar | 10 | 90 | 1 GB gratis |
| Premium | 25 | 200 | 5 GB gratis |
| Ultra | 50 | 350 | 10 GB gratis |

---

## 4. Flujo de Creación de Clave VPN

### 4.1 Diagrama de Secuencia

```
Usuario              Bot               Servicio VPN        Base de Datos
  │                    │                     │                    │
  │──"Crear Nueva"────>│                     │                    │
  │                    │                     │                    │
  │<──Elegir protocolo──│                   │                    │
  │                    │                     │                    │
  │──WireGuard/Outline─>│                   │                    │
  │                    │                     │                    │
  │<──Elegir servidor───│                   │                    │
  │                    │                     │                    │
  │──Seleccionar SV───>│                    │                    │
  │                    │                     │                    │
  │                    │────Generar clave────>│                   │
  │                    │                     │                    │
  │                    │<─────Config─────────│                    │
  │                    │                     │                    │
  │                    │────Guardar en BD─────────────────────────>│
  │                    │                     │                    │
  │<──Mostrar config───│                   │                    │
  │   QR + Texto       │                     │                    │
```

### 4.2 Límites de Claves

| Tipo Usuario | WireGuard | Outline | Total |
|--------------|-----------|---------|-------|
| Gratis | 1 | 1 | 2 |
| VIP Básico | 3 | 3 | 6 |
| VIP Pro | 5 | 5 | 10 |
| VIP Ultra | 10 | 10 | 20 |

---

## 5. Flujo de Admin

### 5.1 Estados del Panel Admin

```
┌─────────────────────────────────────────────────────────────┐
│                    PANEL ADMINISTRADOR                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Usuarios    │  │   Servidores  │  │   Broadcast   │
│  - Listar     │  │  - Estado     │  │  - Mensaje    │
│  - Buscar     │  │  - Agregar    │  │  - Preview    │
│  - Ban/Unban  │  │  - Eliminar   │  │  - Enviar     │
└───────────────┘  └───────────────┘  └───────────────┘
           │               │               │
           ▼               ▼               ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Tickets     │  │  Estadísticas │  │   Claves      │
│  - Ver        │  │  - Usuarios   │  │  - Eliminar   │
│  - Responder  │  │  - Ventas     │  │  - Buscar     │
│  - Cerrar     │  │  - Uso VPN    │  │  - Ver logs   │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## 6. Secuencia de Comandos

### 6.1 Comandos Principales

| Comando | Descripción | Acceso |
|---------|-------------|--------|
| `/start` | Iniciar bot/registro | Todos |
| `/help` | Mostrar ayuda | Todos |
| `/profile` | Ver perfil | Registrados |
| `/keys` | Listar claves VPN | Registrados |
| `/buy` | Comprar GB | Registrados |
| `/ref` | Programa referidos | Registrados |
| `/support` | Contactar soporte | Registrados |
| `/admin` | Panel admin | Solo admins |

### 6.2 Flujo de Comandos

```
Comando recibido
       │
       ▼
┌─────────────────┐
│  Pre-middleware │ (Rate limiting, logging)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Router/Handler │ (Identificar comando)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Authentication │ (¿Usuario registrado?)
└────────┬────────┘
         │
    ┌────┴────┐
    │Sí       │No
    ▼         ▼
┌────────┐ ┌──────────────┐
│Handler │ │Redirect to   │
│Específico│ /start       │
└───┬────┘ └──────────────┘
    │
    ▼
┌─────────────────┐
│ Business Logic  │ (Servicios, Domain)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │ (Enviar mensaje/keyboard)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Post-middleware │ (Logging, analytics)
└─────────────────┘
```

---

## 7. Manejo de Errores

### 7.1 Tipos de Errores

| Código | Tipo | Descripción | Acción |
|--------|------|-------------|--------|
| E001 | Network | Error de conexión a API Telegram | Retry + mensaje |
| E002 | Database | Error de base de datos | Log + mensaje error |
| E003 | VPN | Error creando clave VPN | Log + retry |
| E004 | Payment | Error en pago Telegram | Notificar usuario |
| E005 | Auth | Usuario no autorizado | Redirect /start |
| E006 | Validation | Input inválido | Mensaje de ayuda |

### 7.2 Flujo de Recuperación

```
Error detectado
       │
       ▼
┌─────────────────┐
│  Log Error      │ (Loguru)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Classify       │ (Tipo de error)
└────────┬────────┘
         │
    ┌────┴────┬───────────┐
    ▼         ▼           ▼
┌───────┐ ┌───────┐ ┌───────────┐
│Retry  │ │Notify │ │Fallback   │
│Logic  │ │User   │ │Response   │
└───────┘ └───────┘ └───────────┘
```

---

## 8. Eventos del Sistema

### 8.1 Eventos Programados (Cron Jobs)

| Evento | Frecuencia | Acción |
|--------|------------|--------|
| Expirar claves | Cada hora | Desactivar claves expiradas |
| Limpiar logs | Diario | Archivar logs antiguos |
| Backup BD | Diario | Backup de base de datos |
| Reporte admin | Semanal | Enviar métricas a admin |

### 8.2 Eventos Asíncronos

| Evento | Trigger | Handler |
|--------|---------|---------|
| `user_registered` | Nuevo usuario | Enviar bienvenida |
| `key_created` | Clave generada | Notificar usuario |
| `payment_completed` | Pago exitoso | Actualizar balance |
| `key_expired` | Clave expirada | Notificar usuario |
| `ticket_created` | Nuevo ticket | Notificar admin |

---

*Documento versión 1.0 - Fecha: 2026-02-18*
