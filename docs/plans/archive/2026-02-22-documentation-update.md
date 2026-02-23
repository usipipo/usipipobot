# Documentation Update Post v2.0 Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Actualizar toda la documentación para reflejar el modelo de negocio v2.0 (eliminación VIP, roles simplificados, sistema de créditos).

**Architecture:** Actualización de 4 documentos clave: PRD.md, database_schema_v3.md, README.md, y verificación de TECHNOLOGY.md. Los cambios son de documentación sin impacto en código.

**Tech Stack:** Markdown documentation

---

## Resumen de Cambios del Modelo v2.0

| Elemento | Estado | Descripción |
|----------|--------|-------------|
| Sistema VIP | ELIMINADO | Removido completamente |
| Roles especiales | ELIMINADO | TASK_MANAGER, ANNOUNCER eliminados |
| balance_stars | ELIMINADO | Sistema de balance removido |
| total_deposited | ELIMINADO | Tracking de depósitos removido |
| UserRole | SIMPLIFICADO | Solo USER y ADMIN |
| referral_credits | NUEVO | Sistema de créditos por referidos |
| Compra de slots | NUEVO | +1/+3/+5 claves con Stars |

---

### Task 1: Actualizar docs/PRD.md

**Files:**
- Modify: `docs/PRD.md`

**Step 1: Actualizar sección 2.3 Sistema de Pagos**

Cambiar la tabla de pagos para eliminar VIP:

```markdown
### 2.3 Sistema de Pagos
| Funcionalidad | Descripción | Prioridad |
|--------------|-------------|-----------|
| Telegram Stars | Pagar con la moneda nativa de Telegram | Alta |
| Planes Gratis | Cuota mensual de 10GB gratuitos | Alta |
| Paquetes de Datos | 10/25/50/100 GB con Stars | Alta |
| Slots de Claves | Comprar claves adicionales | Alta |
| Historial de transacciones | Ver movimientos de estrellas | Media |
```

**Step 2: Actualizar sección 2.2 Sistema de Usuarios**

```markdown
### 2.2 Sistema de Usuarios
| Funcionalidad | Descripción | Prioridad |
|--------------|-------------|-----------|
| Registro automático | Crear cuenta al iniciar `/start` | Alta |
| Perfil de usuario | Ver información y estadísticas | Alta |
| Sistema de referidos | Invitar amigos y ganar créditos | Alta |
| Canje de créditos | Cambiar créditos por GB o slots | Alta |
| Soporte al usuario | Chat directo con administradores | Media |
```

**Step 3: Actualizar sección 3.5 Flujo de Referidos**

```markdown
### 3.5 Flujo de Referidos
```
Menú Principal → /referir → Ver código y link → Compartir
→ Amigo se registra → Recibir 100 créditos
→ Canjear por GB (100 créditos) o +1 slot (500 créditos)
```
```

**Step 4: Actualizar Roadmap (sección 6)**

```markdown
### Fase 3: Sistema de Pagos ✅
- [x] Integración Telegram Stars
- [x] Paquetes de Datos (10/25/50/100 GB)
- [x] Sistema de créditos por referidos
- [x] Compra de slots de claves
```

**Step 5: Actualizar versión del documento**

```markdown
*Documento versión 2.0 - Fecha: 2026-02-22*
```

**Step 6: Commit**

```bash
git add docs/PRD.md
git commit -m "docs: update PRD for business model v2.0"
```

---

### Task 2: Actualizar docs/database_schema_v3.md

**Files:**
- Modify: `docs/database_schema_v3.md`

**Step 1: Actualizar tabla users**

```markdown
### users

| Columna | Tipo | Default | Descripción |
|---------|------|---------|-------------|
| telegram_id | BigInteger | PK | ID de Telegram del usuario |
| username | String | NULL | Nombre de usuario de Telegram |
| full_name | String | NULL | Nombre completo del usuario |
| status | String | 'active' | Estado: active, suspended, blocked |
| role | String | 'user' | Rol: user, admin |
| max_keys | Integer | 2 | Límite de claves VPN |
| referral_code | String | NULL | Código único de referido |
| referred_by | BigInteger | NULL | Telegram ID del referidor |
| referral_credits | Integer | 0 | Créditos ganados por referidos |
| free_data_limit_bytes | BigInteger | 10737418240 (10GB) | Límite de datos gratuitos |
| free_data_used_bytes | BigInteger | 0 | Datos gratuitos consumidos |
| created_at | DateTime(TZ) | now() | Fecha de creación |
| updated_at | DateTime(TZ) | now() | Fecha de última actualización |
```

**Step 2: Actualizar enums**

```markdown
## Enums

### package_type_enum
| Valor | Descripción |
|-------|-------------|
| basic | 10 GB por 50 Stars |
| standard | 25 GB por 65 Stars |
| advanced | 50 GB por 85 Stars |
| premium | 100 GB por 110 Stars |

### key_type_enum
| Valor | Descripción |
|-------|-------------|
| wireguard | Clave VPN WireGuard |
| outline | Clave VPN Outline (Shadowsocks) |

### user_status_enum
| Valor | Descripción |
|-------|-------------|
| active | Usuario activo |
| suspended | Usuario suspendido |
| blocked | Usuario bloqueado |

### user_role_enum
| Valor | Descripción |
|-------|-------------|
| user | Usuario regular (máx 2 claves) |
| admin | Administrador (claves ilimitadas) |
```

**Step 3: Actualizar diagrama ER**

```markdown
## Diagrama ER

```
┌─────────────────────────────────────┐
│               users                 │
├─────────────────────────────────────┤
│ PK telegram_id      BigInteger      │
│    username         String          │
│    full_name        String          │
│    status           String          │
│    role             String          │
│    max_keys         Integer         │
│    referral_code    String          │
│    referred_by      BigInteger      │
│    referral_credits Integer         │
│    free_data_limit_bytes  BigInt    │
│    free_data_used_bytes   BigInt    │
│    created_at       DateTime(TZ)    │
│    updated_at       DateTime(TZ)    │
└───────────────┬─────────────────────┘
                │
                │ 1:N
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌───────────────┐ ┌─────────────────────┐
│   vpn_keys    │ │   data_packages     │
├───────────────┤ ├─────────────────────┤
│ PK id         │ │ PK id               │
│ FK user_id    │ │ FK user_id          │
│    key_type   │ │    package_type     │
│    name       │ │    data_limit_bytes │
│    key_data   │ │    data_used_bytes  │
│    external_id│ │    stars_paid       │
│    is_active  │ │    purchased_at     │
│    created_at │ │    expires_at       │
│    used_bytes │ │    is_active        │
│    last_used_at││    telegram_payment_id│
└───────────────┘ └─────────────────────┘
```
```

**Step 4: Agregar nota sobre sistema de créditos**

```markdown
## Notas de Implementación

1. **Eliminación en Cascada**: Al eliminar un usuario, se eliminan automáticamente todas sus claves VPN y paquetes de datos.

2. **Datos Gratuitos**: Cada usuario tiene un límite de 10GB de datos gratuitos por defecto, configurable en `free_data_limit_bytes`.

3. **Paquetes de Datos**: Los usuarios pueden comprar paquetes adicionales que se almacenan en `data_packages` con fecha de expiración.

4. **Tipos de VPN**: El sistema soporta dos tipos de VPN: WireGuard y Outline, diferenciados por el enum `key_type_enum`.

5. **Sistema de Créditos**: Los usuarios ganan créditos por referidos (100 créditos por referido). Pueden canjear:
   - 100 créditos = 1 GB extra
   - 500 créditos = +1 slot de clave

6. **Límite de Claves**: Por defecto 2 claves por usuario. Se pueden comprar slots adicionales con Stars:
   - +1 clave = 25 Stars
   - +3 claves = 60 Stars
   - +5 claves = 90 Stars
```

**Step 5: Actualizar fecha**

```markdown
> **Fecha:** 2026-02-22
> **Issue:** #127
> **Versión:** 4.0
```

**Step 6: Commit**

```bash
git add docs/database_schema_v3.md
git commit -m "docs: update database schema for v2.0 model"
```

---

### Task 3: Actualizar README.md

**Files:**
- Modify: `README.md`

**Step 1: Actualizar sección de características**

```markdown
## Características

- Creación de claves VPN (WireGuard y Outline)
- Sistema de planes con datos gratuitos (10GB)
- Pagos con Telegram Stars
- Paquetes de datos (10/25/50/100 GB)
- Compra de slots de claves adicionales
- Sistema de referidos con créditos
- Panel de administración
```

**Step 2: Agregar comando /referir**

```markdown
## Comandos del Bot

- `/start` - Iniciar bot
- `/help` - Ayuda
- `/keys` - Mis claves VPN
- `/buy` - Comprar GB o slots
- `/data` - Ver consumo de datos
- `/newkey` - Crear nueva clave
- `/referir` - Sistema de referidos y créditos
- `/admin` - Panel de administración (admins)
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for business model v2.0"
```

---

### Task 4: Verificar docs/TECHNOLOGY.md

**Files:**
- Check: `docs/TECHNOLOGY.md`

**Step 1: Leer archivo y verificar contenido obsoleto**

Run: Leer el archivo completo para identificar referencias a VIP, roles especiales, o balance.

**Step 2: Si hay contenido obsoleto, actualizar**

Si se encuentra contenido obsoleto, actualizar según el modelo v2.0.

**Step 3: Commit si hubo cambios**

```bash
git add docs/TECHNOLOGY.md
git commit -m "docs: update TECHNOLOGY for v2.0 model"
```

---

### Task 5: Verificar tests y finalizar

**Step 1: Ejecutar tests**

Run: `pytest -v --tb=short`
Expected: 94 passed

**Step 2: Commit final si hay cambios pendientes**

```bash
git status
git add -A
git commit -m "docs: complete documentation update for v2.0"
```

**Step 3: Push a origin**

```bash
git push origin develop
```

---

## Resumen de Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| docs/PRD.md | Eliminar VIP, actualizar referidos, agregar slots |
| docs/database_schema_v3.md | Actualizar tabla users, agregar enums, notas |
| README.md | Actualizar características y comandos |
| docs/TECHNOLOGY.md | Verificar y actualizar si es necesario |

## Checklist Final

- [ ] PRD.md actualizado
- [ ] database_schema_v3.md actualizado
- [ ] README.md actualizado
- [ ] TECHNOLOGY.md verificado
- [ ] Tests pasando (94/94)
- [ ] Commits realizados
- [ ] Push a origin
- [ ] Issue #127 cerrado
- [ ] Issue #124 actualizado
