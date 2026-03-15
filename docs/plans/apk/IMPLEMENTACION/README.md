# Planes de Implementación por Fases - APK Android uSipipo

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Estado:** Listo para implementación secuencial

---

## 📋 Cómo Usar Estos Planes

### En una Nueva Sesión de Claude Code

```bash
# 1. Ir a la carpeta de planes
cd docs/plans/apk/IMPLEMENTACION

# 2. Invocar la skill de ejecución de planes
# (Usar la skill "executing-plans" o "writing-plans")

# 3. El agente leerá el plan de la fase actual y ejecutará exactamente lo especificado
```

### Estructura de Cada Plan

Cada archivo de fase contiene:

1. **Contexto** - Qué se está implementando y por qué
2. **Máximo 5 Tareas** - Para evitar errores por sobrecarga
3. **Archivos Específicos** - Solo los que se deben modificar
4. **Comandos de Verificación** - Cómo testear antes de marcar completado
5. **Criterios de Aceptación** - Checklist obligatorio
6. **Rollback** - Cómo revertir si algo sale mal

---

## 🗂️ Estructura de Carpetas

```
IMPLEMENTACION/
├── README.md                      ← Este archivo
├── FASE_00_PREPARACION/
│   ├── plan.md                    ← Crear estructura de carpetas
│   └── checklist.md               ← Verificación pre-implementación
│
├── FASE_01_AUTENTICACION/
│   ├── 01.1_backend_otp_request.md
│   ├── 01.2_backend_otp_verify.md
│   ├── 01.3_backend_jwt.md
│   ├── 01.4_apk_login_screen.md
│   ├── 01.5_apk_otp_screen.md
│   └── 01.6_testing_flujo_completo.md
│
├── FASE_02_DASHBOARD/
│   ├── 02.1_backend_dashboard_endpoint.md
│   ├── 02.2_apk_dashboard_layout.md
│   ├── 02.3_apk_dashboard_cards.md
│   └── 02.4_dashboard_cache.md
│
├── FASE_03_CLAVES_VPN_LISTADO/
│   ├── 03.1_backend_keys_list.md
│   ├── 03.2_backend_keys_detail.md
│   ├── 03.3_apk_keys_list_screen.md
│   └── 03.4_apk_keys_detail_screen.md
│
├── FASE_04_CLAVES_VPN_CREAR/
│   ├── 04.1_backend_keys_create.md
│   ├── 04.2_backend_keys_validations.md
│   ├── 04.3_apk_create_key_paso1.md
│   ├── 04.4_apk_create_key_paso2.md
│   └── 04.5_apk_create_key_paso3.md
│
├── FASE_05_COMPRAS_CATALOGO/
│   ├── 05.1_backend_packages_catalog.md
│   ├── 05.2_apk_shop_screen.md
│   └── 05.3_apk_package_cards.md
│
├── FASE_06_COMPRAS_STARS/
│   ├── 06.1_backend_stars_create.md
│   ├── 06.2_backend_stars_status.md
│   ├── 06.3_apk_stars_payment.md
│   └── 06.4_apk_stars_polling.md
│
├── FASE_07_COMPRAS_USDT/
│   ├── 07.1_backend_crypto_create.md
│   ├── 07.2_backend_crypto_status.md
│   ├── 07.3_apk_usdt_payment.md
│   └── 07.4_apk_usdt_polling.md
│
├── FASE_08_PERFIL/
│   ├── 08.1_backend_user_profile.md
│   ├── 08.2_apk_profile_screen.md
│   ├── 08.3_apk_referrals_screen.md
│   └── 08.4_apk_wallet_screen.md
│
├── FASE_09_TICKETS/
│   ├── 09.1_backend_tickets_crud.md
│   ├── 09.2_apk_tickets_list.md
│   ├── 09.3_apk_tickets_create.md
│   └── 09.4_apk_tickets_detail.md
│
├── FASE_10_NOTIFICACIONES/
│   ├── 10.1_backend_notifications_endpoint.md
│   ├── 10.2_apk_notifications_polling.md
│   └── 10.3_apk_notifications_badges.md
│
├── FASE_11_DISENO_VISUAL/
│   ├── 11.1_colores_cyberpunk.md
│   ├── 11.2_fuentes_jetbrains.md
│   └── 11.3_consistencia_ui.md
│
├── FASE_12_BUILD_DEPLOY/
│   ├── 12.1_buildozer_config.md
│   ├── 12.2_compilar_debug.md
│   ├── 12.3_github_actions.md
│   └── 12.4_release_alpha.md
│
└── FASE_13_INFRAESTRUCTURA/
    ├── 13.1_postgresql_tuning.md
    ├── 13.2_redis_optimization.md
    ├── 13.3_uvicorn_workers.md
    ├── 13.4_systemd_overrides.md
    ├── 13.5_backup_postgresql.md
    ├── 13.6_health_checks.md
    ├── 13.7_firewall_ufw.md
    └── 13.8_fail2ban.md
```

---

## 🎯 Reglas de Implementación

### Regla de Máximo 5 Tareas por Fase
Cada archivo de plan tiene **máximo 5 tareas** para:
- Evitar errores por sobrecarga cognitiva
- Facilitar testing incremental
- Permitir rollback rápido si algo falla
- Mantener sesiones de implementación cortas (<2 horas)

### Regla de Verificación Obligatoria
Antes de marcar una fase como completada:
1. Ejecutar TODOS los comandos de verificación
2. Verificar TODOS los criterios de aceptación
3. Documentar cualquier desviación en `checklist.md`

### Regla de No Retroceso
Una vez completada una fase:
- **NO modificar** archivos de fases anteriores (a menos que sea bug crítico)
- **NO agregar** funcionalidad extra no especificada en el plan
- **NO optimizar** prematuramente (YAGNI)

---

## 📊 Progreso de Implementación

### Plantilla de Tracking

Crear archivo `IMPLEMENTACION/PROGRESO.md`:

```markdown
# Progreso de Implementación

## Fases Completadas

| Fase | Fecha | Estado | Notas |
|------|-------|--------|-------|
| 01.1 | - | ⏳ Pendiente | - |
| 01.2 | - | ⏳ Pendiente | - |

## Issues Encontrados

| Fase | Issue | Solución | Fecha |
|------|-------|----------|-------|
| - | - | - | - |

## Decisiones de Diseño

| Fase | Decisión | Razón | Fecha |
|------|----------|-------|-------|
| - | - | - | - |
```

---

## 🚀 Comenzar Implementación

### Paso 1: Verificar Prerrequisitos

```bash
# Ejecutar script de verificación
bash scripts/verify_prerequisites.sh
```

### Paso 2: Iniciar Fase 01.1

```bash
# Leer el plan
cat IMPLEMENTACION/FASE_01_AUTENTICACION/01.1_backend_otp_request.md

# Invocar skill de ejecución
# (El agente leerá el plan y ejecutará las tareas)
```

### Paso 3: Verificar y Marcar Completada

```bash
# Ejecutar comandos de verificación del plan
# Si todo pasa:
echo "✅ FASE 01.1 COMPLETADA" >> IMPLEMENTACION/PROGRESO.md

# Avanzar a siguiente fase
cat IMPLEMENTACION/FASE_01_AUTENTICACION/01.2_backend_otp_verify.md
```

---

## ⚠️ Importante

**NO saltar fases.** Cada fase depende de la anterior. Si una fase falla:

1. **No continuar** a la siguiente fase
2. **Revertir** cambios usando el rollback del plan
3. **Debuggear** hasta resolver
4. **Reintentar** la fase

---

*Documento versión 1.0 - Fecha: Marzo 2026*
