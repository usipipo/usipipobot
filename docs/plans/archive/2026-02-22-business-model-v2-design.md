# Modelo de Negocio uSipipo v2.0 - Design Document

> **Fecha:** 2026-02-22
> **Estado:** Aprobado
> **Reemplaza:** Modelo híbrido anterior (VIP + Stars + Referidos con comisiones)

---

## Resumen Ejecutivo

Refactorización del modelo de negocio del bot VPN uSipipo para simplificar y unificar la monetización a través de Telegram Stars, eliminando el sistema VIP heredado y los roles especiales, mientras se mantiene un sistema de referidos basado en puntos/créditos canjeables.

---

## Modelo de Negocio Final

### 1. USUARIOS

```
┌─────────────────────────────────────────────────────────────┐
│ User Entity (simplificado)                                  │
├─────────────────────────────────────────────────────────────┤
│ telegram_id: int          # Identificador único             │
│ username: Optional[str]   # Username de Telegram            │
│ full_name: Optional[str]  # Nombre completo                 │
│ status: UserStatus        # ACTIVE | SUSPENDED | BLOCKED    │
│ role: UserRole            # USER | ADMIN (solo 2 roles)     │
│ max_keys: int             # Límite de claves (2 default)    │
│ referral_code: str        # Código único para invitar       │
│ referred_by: Optional[int] # Telegram ID del referidor      │
│ referral_credits: int     # Créditos ganados por referidos  │
│ free_data_limit_bytes: int # Cuota gratuita (10GB)          │
│ free_data_used_bytes: int  # Datos consumidos               │
│ created_at: datetime                                       │
└─────────────────────────────────────────────────────────────┘
```

### 2. MONETIZACIÓN UNIFICADA (Telegram Stars)

**Paquetes de Datos:**
| Paquete | Datos | Stars | Bonus | Duración |
|---------|-------|-------|-------|----------|
| Básico | 10 GB | 50 | 0% | 35 días |
| Estándar | 25 GB | 65 | 30% | 35 días |
| Avanzado | 50 GB | 85 | 30% | 35 días |
| Premium | 100 GB | 110 | 30% | 35 días |

**Slots de Claves Adicionales:**
| Producto | Slots Extra | Stars |
|----------|-------------|-------|
| +1 Clave | 1 | 25 |
| +3 Claves | 3 | 60 |
| +5 Claves | 5 | 90 |

### 3. SISTEMA DE REFERIDOS (Puntos/Créditos)

```
┌─────────────────────────────────────────────────────────────┐
│ Mecánica de Referidos                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Usuario comparte su código de referido                   │
│ 2. Nuevo usuario se registra con el código                  │
│ 3. Referidor gana CREDITOS_POR_REFERIDO (ej: 100 créditos)  │
│ 4. Créditos canjeables por:                                 │
│    - Datos gratis (100 créditos = 1 GB)                     │
│    - Slots de clave (500 créditos = +1 slot)                │
│ 5. Nuevo usuario también recibe BONUS_NUEVO (ej: 50 créditos)│
└─────────────────────────────────────────────────────────────┘
```

### 4. ROLES SIMPLIFICADOS

```
UserRole:
  - USER: Usuario regular (máximo 2 claves por defecto)
  - ADMIN: Administrador (claves ilimitadas, acceso a panel admin)
```

---

## Cambios Requeridos

### FASE 1: Corrección de Bugs Críticos

| Issue | Descripción | Prioridad |
|-------|-------------|-----------|
| #110 | UserModel incompleto (ya resuelto) | ✅ Done |
| NEW-1 | VpnKeyModel faltan campos: data_limit_bytes, billing_reset_at, expires_at | CRÍTICO |
| NEW-2 | VpnKeyModel: last_used_at vs last_seen_at (AttributeError) | CRÍTICO |

### FASE 2: Eliminación de VIP

| Issue | Archivos Afectados |
|-------|-------------------|
| VIP-1 | Entity: Remover is_vip, vip_expires_at de User |
| VIP-2 | Model: Remover columnas VIP de UserModel |
| VIP-3 | Repository: Remover lógica VIP de user_repository.py |
| VIP-4 | Services: Remover activate_vip, upgrade_to_vip, _get_user_data_limit VIP |
| VIP-5 | Handlers: Remover comandos/mensajes relacionados con VIP |
| VIP-6 | Migration: Crear migración para eliminar columnas |

### FASE 3: Eliminación de Roles Especiales

| Issue | Archivos Afectados |
|-------|-------------------|
| ROLE-1 | Entity: Remover TASK_MANAGER, ANNOUNCER de UserRole enum |
| ROLE-2 | Entity: Remover task_manager_expires_at, announcer_expires_at de User |
| ROLE-3 | Services: Remover assign_role() para roles eliminados |
| ROLE-4 | Handlers: Remover cualquier funcionalidad de roles especiales |

### FASE 4: Eliminación de Sistema de Balance/Stars Directo

| Issue | Archivos Afectados |
|-------|-------------------|
| BAL-1 | Entity: Remover balance_stars, total_deposited de User |
| BAL-2 | Entity: Remover total_referral_earnings (reemplazar por referral_credits) |
| BAL-3 | Model: Remover columnas de balance |
| BAL-4 | Repository: Remover update_balance() |
| BAL-5 | Services: Refactorizar PaymentService (pagos directos, sin balance) |
| BAL-6 | Migration: Eliminar columnas de balance |

### FASE 5: Sistema de Créditos por Referidos

| Issue | Archivos Afectados |
|-------|-------------------|
| REF-1 | Entity: Agregar referral_credits a User |
| REF-2 | Model: Agregar columna referral_credits |
| REF-3 | Repository: Agregar update_referral_credits() |
| REF-4 | Services: Crear ReferralService con lógica de créditos |
| REF-5 | Handlers: Implementar comando /referir y canje de créditos |
| REF-6 | Migration: Agregar columna referral_credits |

### FASE 6: Compra de Slots de Claves

| Issue | Archivos Afectados |
|-------|-------------------|
| SLOT-1 | Services: Crear lógica de compra de slots en DataPackageService |
| SLOT-2 | Handlers: Agregar opción en /buy para comprar slots |
| SLOT-3 | Repository: Agregar update_max_keys() |
| SLOT-4 | Migration: No requerida (max_keys ya existe) |

---

## Arquitectura Final

### Entidades

```python
# User Entity (final)
@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.USER
    max_keys: int = 2
    referral_code: Optional[str] = None
    referred_by: Optional[int] = None
    referral_credits: int = 0
    free_data_limit_bytes: int = 10 * 1024**3
    free_data_used_bytes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    keys: List = field(default_factory=list)

# UserRole Enum (final)
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# UserStatus Enum (final)
class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
```

### Modelo de Base de Datos

```sql
-- users table (final)
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR,
    full_name VARCHAR,
    status VARCHAR DEFAULT 'active',
    role VARCHAR DEFAULT 'user',
    max_keys INTEGER DEFAULT 2,
    referral_code VARCHAR UNIQUE,
    referred_by BIGINT,
    referral_credits INTEGER DEFAULT 0,
    free_data_limit_bytes BIGINT DEFAULT 10737418240,
    free_data_used_bytes BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_users_referral_code ON users(referral_code);
CREATE INDEX ix_users_referred_by ON users(referred_by);
```

---

## Estimación de Esfuerzo

| Fase | Issues | Tiempo Estimado | Complejidad |
|------|--------|-----------------|-------------|
| Fase 1: Bugs | 2 | 1-2 horas | Media |
| Fase 2: VIP | 6 | 3-4 horas | Alta |
| Fase 3: Roles | 4 | 1-2 horas | Media |
| Fase 4: Balance | 6 | 3-4 horas | Alta |
| Fase 5: Créditos | 6 | 4-5 horas | Alta |
| Fase 6: Slots | 4 | 2-3 horas | Media |
| **TOTAL** | **28** | **14-20 horas** | |

---

## Orden de Implementación Recomendado

1. **Fase 1** (Bugs críticos) - Permite que el bot funcione correctamente
2. **Fase 3** (Roles) - Menor impacto, fácil de implementar
3. **Fase 2** (VIP) - Mayor impacto, requiere más cambios
4. **Fase 4** (Balance) - Eliminar sistema de balance
5. **Fase 5** (Créditos) - Implementar nuevo sistema de referidos
6. **Fase 6** (Slots) - Nueva funcionalidad de compra de slots

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Datos existentes de VIP | Usuarios con VIP activo perderían beneficios | Migrar VIP restante a créditos equivalentes |
| Referidos existentes | Datos de referred_by se mantienen | Compatible con nuevo sistema |
| Balance existente | Usuarios con balance perderían stars | Convertir balance a créditos (1:1) |

---

## Próximos Pasos

1. Crear issues en GitHub para cada tarea
2. Implementar en orden de fases
3. Tests automatizados por cada cambio
4. Documentación actualizada
