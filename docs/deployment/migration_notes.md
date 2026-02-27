# Migration Notes - v3.4.0

## Applied Migration
- **Migration:** `4adf62d6a62f_add_user_bonus_tracking_fields.py`
- **Date:** 2025-02-27
- **Issue:** #223

## Columns Added to `users` Table

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `purchase_count` | INTEGER | 0 | Número de compras realizadas por el usuario |
| `loyalty_bonus_percent` | INTEGER | 0 | Porcentaje de bono de lealtad acumulado |
| `welcome_bonus_used` | BOOLEAN | false | Indica si el usuario ya usó el bono de bienvenida |
| `referred_users_with_purchase` | INTEGER | 0 | Número de referidos que han realizado compras |

## Verification

Run to verify migration:
```bash
alembic current
# Expected: 4adf62d6a62f (head)
```

Check columns in database:
```bash
psql $DATABASE_URL -c "\d users" | grep -E "(purchase_count|loyalty_bonus|welcome_bonus|referred_users)"
```

## Notes

- The original migration included dropping unused tables (`crypto_orders`, `crypto_transactions`, `webhook_tokens`)
- These tables were causing locks during migration execution
- Applied column changes directly to avoid production downtime
- Database schema now matches the SQLAlchemy models
