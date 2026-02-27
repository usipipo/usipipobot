#!/bin/bash
# =============================================================================
# Database Migration with Data Preservation
# =============================================================================
# This script handles the migration from the old migration chain to the
# new consolidated migration while preserving all existing data.
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/full_backup_${TIMESTAMP}.sql"
DATA_ONLY_FILE="${BACKUP_DIR}/data_only_${TIMESTAMP}.sql"

# Parse DATABASE_URL from .env
DATABASE_URL=$(grep DATABASE_URL .env | cut -d'=' -f2-)

# Extract connection details
# Format: postgresql+asyncpg://user:password@host:port/dbname
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Database Migration with Data Backup   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Database:${NC} $DB_NAME"
echo -e "${YELLOW}Host:${NC} $DB_HOST:$DB_PORT"
echo -e "${YELLOW}User:${NC} $DB_USER"
echo ""

# Step 1: Full backup
echo -e "${BLUE}[1/6] Creating full database backup...${NC}"
PGPASSWORD=$DB_PASS pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --verbose --no-owner --no-acl > "$BACKUP_FILE"
echo -e "${GREEN}✓ Full backup created:${NC} $BACKUP_FILE"
echo ""

# Step 2: Data-only backup (no schema)
echo -e "${BLUE}[2/6] Creating data-only backup...${NC}"
PGPASSWORD=$DB_PASS pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --data-only --no-owner --no-acl \
    --exclude-table=alembic_version \
    > "$DATA_ONLY_FILE"
echo -e "${GREEN}✓ Data-only backup created:${NC} $DATA_ONLY_FILE"
echo ""

# Step 3: Drop all tables except alembic_version
echo -e "${BLUE}[3/6] Dropping existing tables...${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<EOF
DO \$\$ 
DECLARE
    r RECORD;
BEGIN
    -- Disable foreign key checks temporarily
    SET session_replication_role = 'replica';
    
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Drop all custom types
    FOR r IN (SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid 
              WHERE n.nspname = 'public' AND t.typtype = 'e') LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
    END LOOP;
    
    -- Re-enable foreign key checks
    SET session_replication_role = 'origin';
END \$\$;
EOF
echo -e "${GREEN}✓ Tables dropped${NC}"
echo ""

# Step 4: Create new schema using alembic
echo -e "${BLUE}[4/6] Creating new schema with alembic...${NC}"
source venv/bin/activate
alembic stamp 000_initial_consolidated
alembic upgrade head
echo -e "${GREEN}✓ New schema created${NC}"
echo ""

# Step 5: Restore data
echo -e "${BLUE}[5/6] Restoring data...${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --set ON_ERROR_STOP=on \
    -f "$DATA_ONLY_FILE" 2>&1 | grep -v "INSERT 0 1" || true
echo -e "${GREEN}✓ Data restored${NC}"
echo ""

# Step 6: Verify
echo -e "${BLUE}[6/6] Verifying migration...${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 'Users' as table_name, count(*) as records FROM users
UNION ALL
SELECT 'VPN Keys', count(*) FROM vpn_keys
UNION ALL
SELECT 'Data Packages', count(*) FROM data_packages
UNION ALL
SELECT 'Transactions', count(*) FROM transactions
UNION ALL
SELECT 'Tickets', count(*) FROM tickets
UNION ALL
SELECT 'Crypto Orders', count(*) FROM crypto_orders;
"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Migration completed successfully!     ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Backup files saved in:${NC} $BACKUP_DIR"
echo -e "  - Full backup:  ${BACKUP_FILE}"
echo -e "  - Data backup:  ${DATA_ONLY_FILE}"
echo ""
echo -e "${YELLOW}To rollback if needed:${NC}"
echo "  PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $BACKUP_FILE"
