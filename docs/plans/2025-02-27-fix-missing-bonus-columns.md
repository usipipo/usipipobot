# Fix: Apply Missing Database Migration for Bonus System

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply the pending Alembic migration `4adf62d6a62f_add_user_bonus_tracking_fields.py` to fix the `UndefinedColumnError: column users.purchase_count does not exist` error.

**Architecture:** The migration adds bonus tracking columns (`purchase_count`, `loyalty_bonus_percent`, `welcome_bonus_used`, `referred_users_with_purchase`) to the `users` table. The code models already expect these columns but they don't exist in the production database because the migration was never executed.

**Tech Stack:** PostgreSQL, SQLAlchemy, Alembic, asyncpg

---

## Phase 1: Pre-Execution Verification

### Task 1.1: Verify Migration File Exists

**Files:**
- Verify: `migrations/versions/4adf62d6a62f_add_user_bonus_tracking_fields.py`

**Step 1: Check migration exists**
```bash
ls -la migrations/versions/4adf62d6a62f_add_user_bonus_tracking_fields.py
```
Expected: File exists with upgrade() function that adds the 4 columns

**Step 2: Verify migration contents**
```bash
grep -A 5 "purchase_count" migrations/versions/4adf62d6a62f_add_user_bonus_tracking_fields.py
```
Expected: Shows `op.add_column('users', sa.Column('purchase_count', ...))`

**Step 3: Check current Alembic revision**
```bash
alembic current
```
Expected: Shows current revision (likely `000_initial_consolidated`)

---

### Task 1.2: Backup Database (CRITICAL)

**Step 1: Create database backup**
```bash
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql
```
Expected: Backup file created successfully

---

## Phase 2: Apply Migration

### Task 2.1: Run Alembic Upgrade

**Step 1: Apply migration**
```bash
alembic upgrade head
```
Expected: Migration applies successfully, showing:
```
INFO  [alembic.runtime.migration] Running upgrade 000_initial_consolidated -> 4adf62d6a62f, Add user bonus tracking fields
```

**Step 2: Verify migration applied**
```bash
alembic current
```
Expected: Shows `4adf62d6a62f` (head)

**Step 3: Commit** (no code changes to commit, but document in deployment notes)

---

## Phase 3: Post-Execution Verification

### Task 3.1: Verify Columns in Database

**Step 1: Connect to database and verify columns**
```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\d users"
```
Expected: Shows columns `purchase_count`, `loyalty_bonus_percent`, `welcome_bonus_used`, `referred_users_with_purchase`

**Step 2: Verify with query**
```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name IN ('purchase_count', 'loyalty_bonus_percent', 'welcome_bonus_used', 'referred_users_with_purchase');"
```
Expected: 4 rows returned with the column names

---

### Task 3.2: Test Application Startup

**Step 1: Start the bot and verify no errors**
```bash
python main.py &
```
Expected: Bot starts without `UndefinedColumnError`

**Step 2: Test user registration**
- Send `/start` to the bot
- Check logs for successful user creation
- Expected: No errors about missing columns

**Step 3: Stop test instance**
```bash
pkill -f "python main.py"
```

---

## Phase 4: Documentation Update

### Task 4.1: Update Deployment Notes

**Files:**
- Create: `docs/deployment/migration_notes.md`

**Step 1: Document the migration**
```markdown
# Migration Notes - v3.4.0

## Applied Migrations
- `4adf62d6a62f_add_user_bonus_tracking_fields.py` - Added bonus tracking columns

## Columns Added
- `purchase_count` (Integer, default 0)
- `loyalty_bonus_percent` (Integer, default 0)  
- `welcome_bonus_used` (Boolean, default false)
- `referred_users_with_purchase` (Integer, default 0)

## Verification
Run: `alembic current` should show `4adf62d6a62f`
```

**Step 2: Commit**
```bash
git add docs/deployment/migration_notes.md
git commit -m "docs: add migration notes for v3.4.0 bonus system"
```

---

## Phase 5: Issue Resolution

### Task 5.1: Close GitHub Issue

**Step 1: Close issue with comment**
```bash
gh issue close <issue_number> --comment "Migration applied successfully. Columns verified in database."
```

---

## Checkpoints

| Phase   | Checkpoint SHA | Date | Status  |
|---------|----------------|------|---------|
| Phase 1 | -              | 2025-02-27 | completed |
| Phase 2 | -              | 2025-02-27 | completed |
| Phase 3 | -              | 2025-02-27 | completed |
| Phase 4 | -              | 2025-02-27 | completed |
| Phase 5 | -              | 2025-02-27 | pending |

---

## Rollback Plan

If issues occur during migration:

```bash
# Rollback to previous revision
alembic downgrade 000_initial_consolidated

# Restore from backup
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_YYYYMMDD_HHMMSS.sql
```
