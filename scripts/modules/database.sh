#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# database.sh - PostgreSQL installation and configuration for uSipipo
# ==============================================================================

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
readonly DB_NAME="${DB_NAME:-usipipo}"
readonly DB_USER="${DB_USER:-usipipo}"
readonly DB_HOST="${DB_HOST:-localhost}"
readonly DB_PORT="${DB_PORT:-5432}"
readonly DB_PASSWORD_LENGTH=24

# ------------------------------------------------------------------------------
# PostgreSQL Installation
# ------------------------------------------------------------------------------

install_postgresql() {
    log "Installing PostgreSQL..."

    if command -v psql &>/dev/null; then
        log_ok "PostgreSQL client already installed"
    else
        log "Installing postgresql and postgresql-contrib..."
        run_sudo apt update
        run_sudo apt install -y postgresql postgresql-contrib
        log_ok "PostgreSQL installed successfully"
    fi

    if ! run_sudo systemctl is-active --quiet postgresql; then
        log "Starting PostgreSQL service..."
        run_sudo systemctl start postgresql
        run_sudo systemctl enable postgresql
        log_ok "PostgreSQL service started and enabled"
    else
        log_ok "PostgreSQL service is running"
    fi
}

# ------------------------------------------------------------------------------
# Database and User Creation
# ------------------------------------------------------------------------------

create_database_and_user() {
    local db_name="${1:-${DB_NAME}}"
    local db_user="${2:-${DB_USER}}"
    local db_password="${3:-}"
    local db_exists user_exists

    if [[ -z "${db_password}" ]]; then
        db_password=$(generate_random_string "${DB_PASSWORD_LENGTH}" "false")
    fi

    log "Creating database and user..."
    log "  Database: ${db_name}"
    log "  User: ${db_user}"

    db_exists=$(run_sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${db_name}'" 2>/dev/null || echo "")
    if [[ "${db_exists}" == "1" ]]; then
        log_warn "Database '${db_name}' already exists"
    else
        run_sudo -u postgres psql -c "CREATE DATABASE ${db_name};" 2>&1 | grep -v "could not change directory" >&2 || true
        log_ok "Database '${db_name}' created"
    fi

    user_exists=$(run_sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${db_user}'" 2>/dev/null || echo "")
    if [[ "${user_exists}" == "1" ]]; then
        log_warn "User '${db_user}' already exists, updating password..."
        run_sudo -u postgres psql -c "ALTER USER ${db_user} WITH PASSWORD '${db_password}';" 2>&1 | grep -v "could not change directory" >&2 || true
        log_ok "Password updated for user '${db_user}'"
    else
        run_sudo -u postgres psql -c "CREATE USER ${db_user} WITH PASSWORD '${db_password}';" 2>&1 | grep -v "could not change directory" >&2 || true
        log_ok "User '${db_user}' created"
    fi

    run_sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${db_user};" 2>&1 | grep -v "could not change directory" >&2 || true
    run_sudo -u postgres psql -d "${db_name}" -c "GRANT ALL ON SCHEMA public TO ${db_user};" 2>&1 | grep -v "could not change directory" >&2 || true
    run_sudo -u postgres psql -d "${db_name}" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${db_user};" 2>&1 | grep -v "could not change directory" >&2 || true
    log_ok "Privileges granted to user '${db_user}' on database '${db_name}'"

    echo "${db_password}"
}

# ------------------------------------------------------------------------------
# Save Credentials to .env
# ------------------------------------------------------------------------------

save_db_credentials() {
    local env_file="${1:-.env}"
    local db_user="${2:-${DB_USER}}"
    local db_password="${3:-}"
    local db_name="${4:-${DB_NAME}}"
    local db_host="${5:-${DB_HOST}}"
    local db_port="${6:-${DB_PORT}}"
    local database_url encoded_password

    if [[ -z "${db_password}" ]]; then
        log_err "Password is required to save credentials"
        return 1
    fi

    encoded_password=$(printf '%s' "${db_password}" | jq -sRr @uri 2>/dev/null || printf '%s' "${db_password}" | sed 's/%/%25/g; s/@/%40/g; s/:/%3A/g; s/\//%2F/g; s/\?/%3F/g; s/#/%23/g; s/\[/%5B/g; s/\]/%5D/g')
    database_url="postgresql+asyncpg://${db_user}:${encoded_password}@${db_host}:${db_port}/${db_name}"

    log "Saving database credentials to ${env_file}..."
    ensure_env_exists "${env_file}"

    env_set "${env_file}" "DATABASE_URL" "${database_url}"
    env_set "${env_file}" "DB_PASSWORD" "${db_password}"
    env_set "${env_file}" "DB_NAME" "${db_name}"
    env_set "${env_file}" "DB_USER" "${db_user}"
    env_set "${env_file}" "DB_HOST" "${db_host}"
    env_set "${env_file}" "DB_PORT" "${db_port}"

    log_ok "Database credentials saved to ${env_file}"
    log "  DATABASE_URL: postgresql+asyncpg://${db_user}:****@${db_host}:${db_port}/${db_name}"
}

# ------------------------------------------------------------------------------
# PostgreSQL Configuration
# ------------------------------------------------------------------------------

configure_postgresql() {
    local pg_hba_conf pg_version pg_data_dir

    log "Configuring PostgreSQL authentication..."

    pg_version=$(run_sudo -u postgres psql -tAc "SHOW server_version" | cut -d. -f1)
    pg_data_dir="/var/lib/postgresql/${pg_version}/main"
    pg_hba_conf="${pg_data_dir}/pg_hba.conf"

    if [[ ! -f "${pg_hba_conf}" ]]; then
        pg_hba_conf="/etc/postgresql/${pg_version}/main/pg_hba.conf"
    fi

    if [[ ! -f "${pg_hba_conf}" ]]; then
        log_err "Could not find pg_hba.conf"
        return 1
    fi

    if grep -q "^host.*all.*all.*127.0.0.1/32.*md5" "${pg_hba_conf}" 2>/dev/null; then
        log_ok "pg_hba.conf already configured for md5 authentication"
    else
        log "Updating pg_hba.conf for md5 authentication..."
        run_sudo sed -i 's/^host.*all.*all.*127.0.0.1\/32.*peer/host    all             all             127.0.0.1\/32            md5/' "${pg_hba_conf}"
        run_sudo sed -i 's/^host.*all.*all.*::1\/128.*peer/host    all             all             ::1\/128                 md5/' "${pg_hba_conf}"
        log_ok "pg_hba.conf updated"

        log "Reloading PostgreSQL configuration..."
        run_sudo systemctl reload postgresql
        log_ok "PostgreSQL configuration reloaded"
    fi
}

# ------------------------------------------------------------------------------
# PostgreSQL Status Check
# ------------------------------------------------------------------------------

check_postgresql_status() {
    log "PostgreSQL Status:"
    echo ""

    if ! command -v psql &>/dev/null; then
        log_err "PostgreSQL is not installed"
        return 1
    fi

    echo -e "${CYAN}Service Status:${NC}"
    run_sudo systemctl status postgresql --no-pager || true
    echo ""

    echo -e "${CYAN}PostgreSQL Version:${NC}"
    PAGER= run_sudo -u postgres psql -tAc "SELECT version();" 2>&1 | grep -v "could not change directory" || log_warn "Could not retrieve version"
    echo ""

    echo -e "${CYAN}Databases:${NC}"
    PAGER= run_sudo -u postgres psql -tAc "\l" 2>&1 | grep -v "could not change directory" | head -20 || log_warn "Could not list databases"
    echo ""

    echo -e "${CYAN}Users:${NC}"
    PAGER= run_sudo -u postgres psql -tAc "\du" 2>&1 | grep -v "could not change directory" | head -20 || log_warn "Could not list users"

    echo ""
    echo -e "${CYAN}Connection Test:${NC}"
    if PAGER= run_sudo -u postgres psql -c "SELECT 1;" 2>&1 | grep -v "could not change directory" &>/dev/null; then
        log_ok "PostgreSQL is accepting connections"
    else
        log_err "PostgreSQL is not accepting connections"
        return 1
    fi
}

# ------------------------------------------------------------------------------
# Main Setup Function
# ------------------------------------------------------------------------------

setup_database() {
    local project_dir="${1:-.}"
    local env_file="${project_dir}/.env"
    local db_name db_user db_password

    db_name="${DB_NAME}"
    db_user="${DB_USER}"

    echo -e "${HEADER_ICON} ${CYAN}PostgreSQL Setup for uSipipo${NC}"
    echo -e "${GRAY}${SEPARATOR}${NC}"
    echo ""

    install_postgresql
    echo ""

    configure_postgresql
    echo ""

    db_password=$(create_database_and_user "${db_name}" "${db_user}")
    echo ""

    save_db_credentials "${env_file}" "${db_user}" "${db_password}" "${db_name}" "${DB_HOST}" "${DB_PORT}"
    echo ""

    check_postgresql_status
    echo ""

    echo -e "${GRAY}${SEPARATOR}${NC}"
    log_ok "Database setup complete!"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Run database migrations: alembic upgrade head"
    echo "  2. Verify connection: python -c \"from sqlalchemy import create_engine; ...\""
}

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    setup_database "${PROJECT_DIR}"
fi
