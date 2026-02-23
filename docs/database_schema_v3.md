# Esquema de Base de Datos v4.0

> **Fecha:** 2026-02-22
> **Issue:** #127
> **Actualizado para:** Modelo de Negocio v2.0

## Resumen de Cambios

### Tablas Eliminadas
- `achievements` - Sistema de logros descontinuado
- `user_achievements` - Relación usuario-logros
- `user_stats` - Estadísticas de usuario (redundante)
- `tasks` - Sistema de tareas descontinuado
- `user_tasks` - Relación usuario-tareas
- `tickets` - Sistema de tickets descontinuado
- `ai_conversations` - Conversaciones AI descontinuadas
- `transactions` - Histórico de transacciones (simplificado)

### Tablas Modificadas
- `users`: Agregados campos `free_data_limit_bytes` y `free_data_used_bytes`
- `vpn_keys`: Campo `key_type` convertido de String a Enum

### Tablas Nuevas
- `data_packages`: Almacena paquetes de datos pagados

## Esquema Actual

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

### vpn_keys

| Columna | Tipo | Default | Descripción |
|---------|------|---------|-------------|
| id | UUID | gen_random_uuid() | ID único de la clave |
| user_id | BigInteger | FK | Referencia a users.telegram_id |
| key_type | key_type_enum | - | Tipo de VPN (wireguard/outline) |
| name | String | - | Nombre descriptivo de la clave |
| key_data | String | - | Datos de conexión (ss:// o config WG) |
| external_id | String | NULL | ID asignado por el servidor VPN |
| is_active | Boolean | true | Estado activo de la clave |
| created_at | DateTime(TZ) | now() | Fecha de creación |
| used_bytes | BigInteger | 0 | Tráfico consumido en bytes |
| last_used_at | DateTime(TZ) | NULL | Última actividad del cliente |

### data_packages

| Columna | Tipo | Default | Descripción |
|---------|------|---------|-------------|
| id | UUID | gen_random_uuid() | ID único del paquete |
| user_id | BigInteger | FK | Referencia a users.telegram_id |
| package_type | package_type_enum | - | Tipo de paquete |
| data_limit_bytes | BigInteger | - | Límite de datos en bytes |
| data_used_bytes | BigInteger | 0 | Datos consumidos en bytes |
| stars_paid | Integer | - | Estrellas Telegram pagadas |
| purchased_at | DateTime(TZ) | now() | Fecha de compra |
| expires_at | DateTime(TZ) | - | Fecha de expiración |
| is_active | Boolean | true | Estado activo del paquete |
| telegram_payment_id | String | NULL | ID del pago en Telegram |

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

## Migraciones

| Revisión | Nombre | Descripción |
|----------|--------|-------------|
| 001 | remove_unused_tables | Elimina tablas obsoletas: achievements, user_achievements, user_stats, tasks, user_tasks, tickets, ai_conversations, transactions |
| 002 | add_data_packages | Crea tabla data_packages, agrega campos free_data a users, crea enum package_type_enum |
| 003 | add_key_type_enum | Convierte key_type de String a enum, crea key_type_enum |

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

Leyenda:
  PK = Primary Key
  FK = Foreign Key
  1:N = Relación uno a muchos
```

## Índices

### data_packages
- `ix_data_packages_user_id` - Índice en user_id para búsquedas por usuario
- `ix_data_packages_is_active` - Índice en is_active para filtrado de paquetes activos

## Relaciones

| Tabla Padre | Tabla Hija | Relación | ON DELETE |
|-------------|------------|----------|-----------|
| users | vpn_keys | 1:N | CASCADE |
| users | data_packages | 1:N | CASCADE |

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
