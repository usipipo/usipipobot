#!/bin/bash
# Script para ejecutar migraciones de base de datos
# Issue #73 - Rediseñar esquema de base de datos

set -e

echo "=== Database Migration Script ==="
echo "Issue #73 - Rediseñar esquema de base de datos"
echo ""

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "ERROR: alembic not found. Please install with: pip install alembic"
    exit 1
fi

# Show current migration status
echo "=== Current Migration Status ==="
alembic current
echo ""

# Show migration history
echo "=== Migration History ==="
alembic history
echo ""

# Confirm before proceeding
read -p "Proceed with migration? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

# Run migrations
echo ""
echo "=== Running Migrations ==="
alembic upgrade head

# Verify
echo ""
echo "=== Verification ==="
alembic current

echo ""
echo "=== Migration Complete ==="
echo "Tables should now be: users, vpn_keys, data_packages"
echo "Run: psql -c '\\dt' to verify table structure"
