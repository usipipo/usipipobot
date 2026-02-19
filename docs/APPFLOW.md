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
| `CREATING_KEY` | Creando nueva clave VPN | Seleccionar protocolo/servidor |
| `SELECTING_SERVER` | Eligiendo servidor | Confirmar/Cancelar |
| `VIEWING_KEYS` | Viendo lista de claves | Eliminar/Detalles/Volver |
| `BUYING_GB` | En proceso de compra | Confirmar/Cancelar |
| `SUPPORT_CHAT` | En chat de soporte | Enviar mensaje/Salir |
| `PLAYING_GAME` | Jugando mini-juego | Finalizar/Volver |
| `REFERRAL_VIEW` | Viendo programa referidos | Copiar enlace/Volver |

### 2.2 Diagrama de Estados

```
                    ┌──────────┐
           ┌───────│   IDLE   │◄─────────────────┐
           │       └────┬─────┘                  │
           │            │                        │
    ┌──────▼─────┐ ┌────▼─────┐ ┌──────────┐  ┌─┴──────────┐
    │  CREATING  │ │ SELECTING│ │ VIEWING  │  │    BUYING  │
    │    KEY     │ │  SERVER  │ │   KEYS   │  │     GB     │
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
