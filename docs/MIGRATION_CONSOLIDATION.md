# Migración Consolidada - Alembic

## Resumen

Todas las migraciones de Alembic han sido consolidadas en una única migración inicial: **`001_consolidated_schema`**

## Migraciones Anteriores (Consolidadas)

Las siguientes migraciones fueron reemplazadas por la migración consolidada:

| Migration ID | Description | Fecha |
|--------------|-------------|-------|
| `000_initial_consolidated` | Initial consolidated schema | 2025-02-20 |
| `4adf62d6a62f` | Add user bonus tracking fields | 2026-03-15 |
| `5c8f2a9b1d3e` | Add consumption billing tables | 2026-03-15 |
| `remove_tickets_table` | Remove tickets table | 2026-03-15 |
| `20260302_add_tickets_tables` | Add tickets tables | 2026-03-15 |
| `add_subscriptions_001` | Add subscription plans tables | 2026-03-16 |
| `fix_crypto_int32_001` | Fix crypto user_id int32 overflow | 2026-03-17 |

## Nueva Migración Consolidada

**Archivo**: `migrations/versions/001_consolidated_schema.py`

**Revision ID**: `001_consolidated_schema`

**Revises**: `None` (primera migración)

### Tablas Incluidas

1. **users** - Usuarios del sistema con bonus tracking y consumption billing
2. **vpn_keys** - Llaves VPN (WireGuard y Outline)
3. **data_packages** - Paquetes de datos comprados
4. **transactions** - Transacciones de estrellas
5. **tickets** - Tickets de soporte
6. **ticket_messages** - Mensajes de tickets
7. **consumption_billings** - Facturación por consumo
8. **consumption_invoices** - Facturas de consumo
9. **subscription_plans** - Planes de suscripción
10. **crypto_orders** - Órdenes de pago crypto (con BIGINT user_id)
11. **crypto_transactions** - Transacciones crypto (con BIGINT user_id)
12. **webhook_tokens** - Tokens para webhooks

### Cambios Clave Incluidos

- ✅ User bonus tracking fields (purchase_count, loyalty_bonus_percent, etc.)
- ✅ Consumption billing tables (consumption_billings, consumption_invoices)
- ✅ Subscription plans table
- ✅ Tickets system (tickets, ticket_messages)
- ✅ **FIX**: crypto_orders.user_id como BIGINT (fix int32 overflow)
- ✅ **FIX**: crypto_transactions.user_id como BIGINT (fix int32 overflow)

## Proceso de Consolidación

### 1. Generar Migración Consolidada

La migración consolidada se generó manualmente basada en el esquema actual de la base de datos.

### 2. Reemplazar Migraciones Antiguas

```bash
# Backup de migraciones antiguas
cd migrations/versions
mkdir backup_old_migrations
mv *.py backup_old_migrations/

# Mantener solo la consolidada
cp backup_old_migrations/001_consolidated_schema.py .
```

### 3. Resetear Alembic Version

```sql
-- Resetear tabla alembic_version
DELETE FROM alembic_version;

-- Marcar migración consolidada como aplicada
INSERT INTO alembic_version (version_num)
VALUES ('001_consolidated_schema');
```

### 4. Verificar

```bash
# Verificar migración actual
uv run alembic current
# Debe mostrar: 001_consolidated_schema (head)

# Verificar historial
uv run alembic history
# Debe mostrar: <base> -> 001_consolidated_schema (head)
```

## Comandos Útiles

### Ver estado actual
```bash
uv run alembic current
```

### Ver historial
```bash
uv run alembic history
```

### Ver detalles de la migración
```bash
uv run alembic history -r 001_consolidated_schema --verbose
```

### Ver esquema de la base de datos
```bash
PGPASSWORD=<password> psql -h localhost -U <user> -d <database> -c "\dt"
```

## Rollback (Solo Testing)

La migración consolidada incluye una función `downgrade()` que elimina todas las tablas:

```python
def downgrade() -> None:
    """Drop all tables (NOT RECOMMENDED - use only for testing)."""
    op.drop_table('webhook_tokens')
    op.drop_table('crypto_transactions')
    # ... (resto de tablas en orden inverso)
```

**ADVERTENCIA**: No ejecutar `alembic downgrade base` en producción.

## Beneficios de la Consolidación

1. **Simplicidad**: Una sola migración en lugar de 7+
2. **Claridad**: El esquema completo en un solo archivo
3. **Performance**: Menos migraciones para aplicar en nuevos deployments
4. **Mantenimiento**: Más fácil de entender y modificar
5. **Clean Slate**: Elimina migraciones intermedias que ya no son necesarias

## Próximos Pasos

Para futuras migraciones:

1. Crear nuevo archivo en `migrations/versions/`
2. Usar naming convention: `YYYYMMDD_description.py` o `002_next_feature.py`
3. Actualizar `down_revision` correctamente
4. Probar en staging antes de producción

## Referencias

- Documentación original: `docs/CRYPTO_PAYMENT_INT32_FIX.md`
- Archivo de migración: `migrations/versions/001_consolidated_schema.py`
- Configuración Alembic: `alembic.ini`
- Environment Alembic: `migrations/env.py`

---

**Fecha de Consolidación**: 2026-03-17
**Versión**: 3.9.1
**Estado**: ✅ Completado
