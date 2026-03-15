# uSipipo VPN — Plan Maestro APK Android

> **Versión:** 2.0.0
> **Fecha:** Marzo 2026
> **Stack:** Python · Kivy + KivyMD · Buildozer · FastAPI (backend existente)
> **Ecosistema:** Bot Telegram + Mini App Web + **APK Android**
> **Infraestructura:** Single VPS (2GB RAM) optimizado para máximo rendimiento

---

## 🏗️ Decisiones de Arquitectura (Recomendaciones del experto)

### Framework APK: Kivy + KivyMD (recomendado)

**¿Por qué Kivy sobre BeeWare?**

- Kivy es 100% Python, maduro (10+ años), con comunidad activa masiva.
- KivyMD provee componentes Material Design 3 listos: cards, bottom navigation, dialogs, progress bars — todo gratuito y sin licencia.
- Buildozer compila el proyecto a APK con un solo comando. Es la herramienta estándar del ecosistema Kivy.
- BeeWare (Toga) aún es experimental en Android en 2026; su soporte de widgets es limitado y los builds frecuentemente fallan.
- Kivy tiene soporte nativo de OpenGL ES para animaciones — permite replicar los efectos neon/cyberpunk del mini app web.

**Compensación:** Kivy no produce UI nativa Android (no usa widgets del sistema). Esto es aceptable porque el diseño de uSipipo es una identidad visual propia (cyberpunk), no Android stock.

### Login: OTP via Bot (recomendado sobre Telegram OAuth Widget)

**¿Por qué OTP via bot?**

- Telegram Login Widget requiere WebView + JavaScript bridge. En Kivy esto es complejo y agrega dependencias pesadas.
- El flujo OTP es más simple: el usuario escribe su `@username` o `telegram_id`, el bot le manda un código de 6 dígitos, la APK lo valida contra el backend. Este mecanismo ya existe parcialmente en el backend.
- Elimina dependencia de servicios externos de OAuth.
- El backend ya conoce los `telegram_id` de todos los usuarios registrados en el bot.

### Pagos: Telegram Stars (via Deep Link al Bot) + USDT TronDealer

- Telegram Stars no puede procesarse directamente desde una APK nativa (requiere el cliente Telegram). El flujo correcto es: la APK abre un Deep Link a Telegram que lleva directamente al flujo de pago del bot. El backend confirma el pago y notifica a la APK vía polling o WebSocket.
- USDT ya tiene infraestructura completa con TronDealer en el backend (ver `crypto_payment_service.py`). La APK simplemente muestra la dirección de billetera y hace polling del estado de la orden.

---

## 📁 Estructura Completa de Documentos

### Parte 1: Diseño e Implementación de la APK (Documentos 01-15)

```
docs/plans/apk/
├── 00_INDEX.md                    ← Este archivo (índice maestro)
├── 01_ARQUITECTURA_GLOBAL.md      ← Visión del ecosistema + diagramas de flujo
├── 02_STACK_Y_TECNOLOGIAS.md      ← Stack técnico, dependencias, Buildozer
├── 03_MODULO_AUTH.md              ← Login OTP Telegram + JWT + seguridad
├── 04_MODULO_DASHBOARD.md         ← Pantalla principal, cards, resumen
├── 05_MODULO_CLAVES_VPN.md        ← Listado, detalle, copiar, QR, uso
├── 06_MODULO_CREAR_CLAVE.md       ← Flujo de creación paso a paso
├── 07_MODULO_COMPRAS.md           ← Paquetes, Stars, USDT, confirmación
├── 08_MODULO_PERFIL_CUENTA.md     ← Configuración, referidos, wallet
├── 09_MODULO_TICKETS.md           ← Soporte, crear ticket, historial
├── 10_MODULO_NOTIFICACIONES.md    ← Polling, notificaciones push, badges
├── 11_API_ANDROID_LAYER.md        ← Endpoints REST del backend para APK
├── 12_SEGURIDAD_INTEGRAL.md       ← Security: APK, API, DDoS, JWT
├── 13_DISENO_VISUAL.md            ← Sistema de diseño cyberpunk, colores
├── 14_ESTRUCTURA_PROYECTO.md      ← Árbol de carpetas, integración repo
└── 15_BUILDOZER_Y_DEPLOY.md       ← Compilación, firma, GitHub Actions
```

### Parte 2: Infraestructura y Optimización (Documentos 16-21) ⭐ NUEVO

```
docs/plans/apk/
├── 16_PLAN_MAESTRO_INFRAESTRUCTURA.md  ← Optimización VPS único (2GB RAM)
│   ├── PostgreSQL tuning (128MB shared_buffers)
│   ├── Redis con límites estrictos (128MB max)
│   ├── Backend FastAPI optimizado (uvicorn workers)
│   ├── Aislamiento de fallos (systemd overrides)
│   ├── Background jobs separados
│   └── Traffic shaping (TC)
│
├── 17_SEGURIDAD_REFORZADA.md           ← Seguridad de grado militar
│   ├── Firewall UFW ultra-restrictivo
│   ├── SSH hardening (solo llaves, no root)
│   ├── Fail2Ban con jails personalizados
│   ├── Sysctl kernel hardening
│   ├── PostgreSQL HBA (solo localhost)
│   ├── Encriptación de datos sensibles
│   ├── Gestión de secrets (rotación 90 días)
│   └── Certificate pinning para APK
│
├── 18_RENDIMIENTO_VELOCIDAD.md         ← Objetivos: <100ms p95
│   ├── Índices estratégicos en PostgreSQL
│   ├── Query optimization (JOINs, single query)
│   ├── Caché multi-nivel (memoria + Redis)
│   ├── Uvicorn con httptools + uvloop
│   ├── GZip compression
│   ├── Parallel query execution
│   └── Frontend caching (Caddy)
│
├── 19_MONITOREO_ALERTAS.md             ← Detección en <2 minutos
│   ├── Health checks por servicio (cada 2 min)
│   ├── Monitoreo de recursos (RAM, CPU, disco)
│   ├── Endpoints de health del backend
│   ├── Monitoreo de VPN (WireGuard, Outline)
│   ├── Dashboard web de métricas
│   └── Matriz de alertas por Telegram
│
├── 20_BACKUP_RECUPERACION.md           ← RTO <4h, RPO <24h
│   ├── Backup diario de PostgreSQL (3 AM)
│   ├── Backup semanal de configuraciones
│   ├── Backup mensual de secrets (encriptado)
│   ├── Sync off-site a Backblaze B2/AWS S3
│   ├── Plan de recuperación documentado
│   └── Test de restauración mensual
│
└── 21_APK_INTEGRACION_SEGURA.md        ← Integración progresiva
    ├── Endpoints backend para APK
    ├── Autenticación OTP con JWT
    ├── Rate limiting específico
    ├── Notificaciones cruzadas con el bot
    ├── Feature flags para alpha/beta
    └── Launch progresivo (10 → 50 → 200 → ∞)
```

---

## 🔗 Relación con el Ecosistema Existente

```
┌─────────────────────────────────────────────────────────────┐
│                    ECOSISTEMA uSipipo                       │
│                                                             │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────┐ │
│  │ Telegram Bot │   │  Mini App Web    │   │ APK Android │ │
│  │  (python-    │   │ (Flask + Jinja2) │   │ (Kivy +     │ │
│  │  telegram-   │   │  cyberpunk.css   │   │  KivyMD)    │ │
│  │  bot)        │   │                  │   │             │ │
│  └──────┬───────┘   └────────┬─────────┘   └──────┬──────┘ │
│         │                   │                     │        │
└─────────┼───────────────────┼─────────────────────┼────────┘
          │                   │                     │
          └───────────────────┼─────────────────────┘
                              │
                              ▼
          ┌─────────────────────────────────┐
          │   BACKEND CENTRAL (FastAPI)     │
          │   - PostgreSQL (optimizado)     │
          │   - Redis (caché + rate limit)  │
          │   - Clean Architecture          │
          │   - WireGuard Server            │
          │   - Outline Server              │
          └─────────────────────────────────┘
                              │
                              ▼
          ┌─────────────────────────────────┐
          │   INFRAESTRUCTURA               │
          │   - Single VPS (2GB RAM)        │
          │   - Caddy (HTTPS + reverse proxy)│
          │   - Systemd (servicios)         │
          │   - Backup diario → Cloud       │
          └─────────────────────────────────┘
```

La APK **no tiene lógica de negocio propia**. Toda la lógica vive en el backend. La APK es un cliente REST que consume los mismos endpoints del mini app web más nuevos endpoints específicos para Android.

---

## ⚡ Principios Rectores

### Seguridad
> **"Defense in Depth" + "Zero Trust" + "Minimal Surface"**

- 6 capas de seguridad documentadas
- Certificate pinning en la APK
- JWT con blacklist en Redis
- Rate limiting por IP y usuario
- Firewall ultra-restrictivo
- Fail2Ban con jails personalizados

### Rendimiento
> **"Cada MB cuenta. Cada ms importa."**

- Objetivo: <100ms para el 95% de las peticiones
- PostgreSQL optimizado (128MB shared_buffers)
- Redis con límite de 128MB
- Caché multi-nivel (memoria + Redis)
- Uvicorn con httptools + uvloop
- Índices estratégicos en todas las tablas

### Disponibilidad
> **"Detectar en <2 min. Recuperar en <4h."**

- Health checks cada 2 minutos
- Alertas por Telegram inmediatas
- Auto-restart de servicios caídos
- Backup diario a cloud (off-site)
- RTO <4 horas, RPO <24 horas

---

## 📊 Roadmap de Implementación

### Fase 1: Optimización de Infraestructura (Semanas 1-6)
| Semana | Foco | Entregables |
|--------|------|-------------|
| 1 | PostgreSQL tuning | Config optimizada, índices estratégicos |
| 2 | Redis + Backend | Redis límites, uvicorn workers, connection pooling |
| 3 | Seguridad SO | Firewall UFW, SSH hardening, Fail2Ban |
| 4 | Seguridad DB | pg_hba, usuario con privilegios mínimos |
| 5 | Monitoreo | Health checks, alertas por Telegram |
| 6 | Backup | Scripts de backup, sync a cloud |

### Fase 2: Desarrollo de APK (Semanas 7-12)
| Semana | Foco | Entregables |
|--------|------|-------------|
| 7  | Backend para APK | Endpoints /api/v1/*, autenticación OTP |
| 8  | APK: Auth + Dashboard | Login OTP, pantalla principal |
| 9  | APK: Claves VPN | Listado, detalle, creación |
| 10 | APK: Compras | Pagos Stars, USDT, confirmación |
| 11 | APK: Perfil + Tickets | Configuración, soporte |
| 12 | Testing interno | Alpha con 10 usuarios |

### Fase 3: Launch Progresivo (Semanas 13-16)
| Semana | Foco | Entregables |
|--------|------|-------------|
| 13 | Alpha testing | 10 usuarios, feedback, bug fixes |
| 14 | Beta cerrado | 50 usuarios, ajustes de UX |
| 15 | Beta abierto | 200 usuarios, performance tuning |
| 16 | Launch público | GitHub Releases, documentación |

---

## 🎯 Métricas de Éxito del Ecosistema

| Categoría | Métrica | Objetivo | Actual |
|-----------|---------|----------|--------|
| **Rendimiento** | Latencia API (p95) | <100ms | 300ms (baseline) |
| | Throughput backend | 150 req/s | 50 req/s (baseline) |
| | Cache hit rate | >80% | 0% (baseline) |
| **Seguridad** | Intentos brute force bloqueados | 100% | - |
| | Rate limits aplicados | 100% | - |
| | Secrets rotados (90 días) | 100% | - |
| **Disponibilidad** | Uptime | >99.5% | - |
| | Detección de incidentes | <2 min | - |
| | Recuperación (RTO) | <4 horas | - |
| **Usuarios** | Usuarios activos (mes 1) | 500-1000 | 200-300 (actual) |
| | APK installs (mes 1) | 200 | 0 (nuevo) |
| | Crash rate APK | <2% | - |

---

## 📚 Documentos Relacionados del Ecosistema

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| PRD | `docs/PRD.md` | Product Requirements Document |
| APPFLOW | `docs/APPFLOW.md` | Flujos de aplicación |
| TECHNOLOGY | `docs/TECHNOLOGY.md` | Stack tecnológico |
| Database Schema | `docs/database_schema_v3.md` | Esquema de base de datos |
| AGENTS | `AGENTS.md` | Guías de desarrollo |
| QWEN | `QWEN.md` | Contexto del proyecto |

---

## ✅ Checklist Maestro de Implementación

### Infraestructura (Documentos 16-20)
- [ ] **16:** PostgreSQL optimizado (shared_buffers=128MB)
- [ ] **16:** Redis con maxmemory=128MB
- [ ] **16:** Uvicorn con 2 workers + httptools + uvloop
- [ ] **16:** Systemd overrides para todos los servicios
- [ ] **17:** Firewall UFW configurado
- [ ] **17:** SSH hardening aplicado
- [ ] **17:** Fail2Ban con jails personalizados
- [ ] **17:** Sysctl hardening aplicado
- [ ] **18:** Índices estratégicos creados
- [ ] **18:** Caché multi-nivel implementado
- [ ] **19:** Health checks configurados (cron)
- [ ] **19:** Alertas por Telegram funcionando
- [ ] **20:** Backup diario de PostgreSQL (3 AM)
- [ ] **20:** Sync a Backblaze B2/AWS S3
- [ ] **20:** Test de restauración ejecutado

### APK Android (Documentos 01-15, 21)
- [ ] **03:** Autenticación OTP implementada
- [ ] **04:** Dashboard con caché
- [ ] **05:** Listado de claves VPN
- [ ] **06:** Flujo de creación de claves
- [ ] **07:** Pagos con Stars y USDT
- [ ] **08:** Perfil de usuario completo
- [ ] **09:** Sistema de tickets
- [ ] **10:** Notificaciones con polling
- [ ] **11:** Endpoints backend implementados
- [ ] **12:** Certificate pinning en APK
- [ ] **13:** Diseño cyberpunk aplicado
- [ ] **14:** Proyecto integrado al repo
- [ ] **15:** Buildozer configurado
- [ ] **21:** Alpha testing con 10 usuarios
- [ ] **21:** Beta testing con 50 usuarios
- [ ] **21:** Launch público en GitHub Releases

---

## 🚀 Comenzar Ahora

### Para Implementación de Infraestructura
```bash
# 1. Leer el documento 16
cat docs/plans/apk/16_PLAN_MAESTRO_INFRAESTRUCTURA.md

# 2. Comenzar con PostgreSQL tuning
sudo nano /etc/postgresql/15/main/postgresql.conf
# (aplicar configuración optimizada del documento 16)

# 3. Reiniciar PostgreSQL
sudo systemctl restart postgresql

# 4. Verificar mejora
curl http://localhost:8000/metrics/performance
```

### Para Desarrollo de APK
```bash
# 1. Leer el documento 01
cat docs/plans/apk/01_ARQUITECTURA_GLOBAL.md

# 2. Crear estructura de carpetas
mkdir -p android_app/{src/{screens,components,services,storage,utils},assets/{fonts,images},tests}

# 3. Comenzar con autenticación
# (seguir documento 03_MODULO_AUTH.md)
```

---

*Documento versión 2.0 - Fecha: Marzo 2026*
*Índice maestro actualizado con todos los planes de implementación*
