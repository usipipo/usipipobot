# Setup Script Modular Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear un sistema de instalación modular para uSipipo VPN Bot con menú interactivo que configure VPN, PostgreSQL, Python, Systemd y Bot.

**Architecture:** Script principal `setup.sh` que orquesta módulos independientes en `scripts/modules/`. Cada módulo es responsable de un componente específico con funciones bien definidas.

**Tech Stack:** Bash, PostgreSQL, Python 3.11+, systemd, Docker, WireGuard, Outline

---

## Task 1: Crear estructura de directorios y módulo common.sh

**Files:**
- Create: `scripts/modules/common.sh`
- Create: `scripts/modules/` directory

**Step 1: Crear directorio de módulos**

Run: `mkdir -p scripts/modules`

**Step 2: Crear common.sh con funciones compartidas**

```bash
#!/bin/bash
# =============================================================================
# common.sh - Funciones compartidas para scripts de setup
# =============================================================================

# Strict mode
set -Eeuo pipefail

# =============================================================================
# UI / Colors
# =============================================================================
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly GRAY='\033[0;90m'
readonly NC='\033[0m'

readonly SEPARATOR="═══════════════════════════════════════════════════════════════════════════════"
readonly HEADER_ICON="🛡️"
readonly SUCCESS_ICON="✓"
readonly ERROR_ICON="✗"
readonly INFO_ICON="ℹ"

# =============================================================================
# Logging Functions
# =============================================================================
log() { echo -e "${BLUE}${INFO_ICON} [INFO]${NC} ${GRAY}$(date '+%F %T')${NC} │ $*"; }
log_ok() { echo -e "${GREEN}${SUCCESS_ICON} [OK]${NC} ${GRAY}$(date '+%F %T')${NC} │ $*"; }
log_warn() { echo -e "${YELLOW}${INFO_ICON} [WARN]${NC} ${GRAY}$(date '+%F %T')${NC} │ $*"; }
log_err() { echo -e "${RED}${ERROR_ICON} [ERR]${NC} ${GRAY}$(date '+%F %T')${NC} │ $*"; }

# =============================================================================
# Sudo Wrapper
# =============================================================================
run_sudo() {
    if [ "$(id -u)" = "0" ]; then
        "$@"
    else
        sudo -E "$@"
    fi
}

# =============================================================================
# Confirmation Dialog
# =============================================================================
confirm() {
    local prompt="${1:-Are you sure?}"
    read -r -p "${YELLOW}${prompt} [y/N]: ${NC}" ans
    [[ "$ans" =~ ^[Yy]$ ]]
}

# =============================================================================
# Generate Random String
# =============================================================================
generate_random_string() {
    local length="${1:-32}"
    tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "$length"
}

# =============================================================================
# Dependency Checking
# =============================================================================
check_dependencies() {
    local -a missing_deps=()
    local -a required=("curl" "ip" "sed" "grep" "awk" "systemctl")

    for cmd in "${required[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_err "Missing required commands: ${missing_deps[*]}"
        return 1
    fi

    log_ok "All required dependencies found."
    return 0
}

# =============================================================================
# Public IP Detection
# =============================================================================
get_public_ip() {
    # 1) Cloud metadata (works on many VPS providers)
    local ip
    ip=$(curl -4 -s --max-time 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
    if [[ -n "$ip" ]]; then
        echo "$ip"
        return 0
    fi

    # 2) Direct IP-based endpoints
    ip=$(curl -4 -s --max-time 3 http://4.icanhazip.com 2>/dev/null || true)
    if [[ -n "$ip" ]]; then
        echo "$ip"
        return 0
    fi

    # 3) Regular external services
    ip=$(curl -4 -s --max-time 3 https://api.ipify.org 2>/dev/null || true)
    if [[ -n "$ip" ]]; then
        echo "$ip"
        return 0
    fi

    # 4) Fallback: detect from primary network interface
    local iface
    iface=$(ip route 2>/dev/null | awk '/default/ {print $5; exit}' || true)
    iface=${iface:-eth0}
    ip=$(ip -4 addr show dev "$iface" 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1 || true)
    if [[ -n "$ip" ]]; then
        echo "$ip"
        return 0
    fi

    echo ""
    return 1
}

# =============================================================================
# .env Helpers
# =============================================================================
ensure_env_exists() {
    local env_file="${1:-$PROJECT_DIR/.env}"
    local example_env="${2:-$PROJECT_DIR/example.env}"
    
    if [ ! -f "$env_file" ]; then
        log_warn ".env not found — creating from example if available."
        if [ -f "$example_env" ]; then
            cp "$example_env" "$env_file"
        else
            touch "$env_file"
        fi
    fi
}

env_set() {
    local key="$1"
    local value="$2"
    local env_file="${3:-$PROJECT_DIR/.env}"

    if [[ -z "$key" ]]; then
        log_err "env_set: key argument is required"
        return 1
    fi

    ensure_env_exists "$env_file"
    local esc_value
    esc_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')
    if grep -qE "^${key}=" "$env_file"; then
        sed -i "s/^${key}=.*/${key}=${esc_value}/" "$env_file"
    else
        echo "${key}=${value}" >> "$env_file"
    fi
}

env_get() {
    local key="$1"
    local env_file="${2:-$PROJECT_DIR/.env}"
    
    if [[ -f "$env_file" ]]; then
        grep "^${key}=" "$env_file" 2>/dev/null | cut -d= -f2- || true
    fi
}
```

**Step 3: Verificar sintaxis**

Run: `bash -n scripts/modules/common.sh`

Expected: No output (success)

**Step 4: Commit**

```bash
git add scripts/modules/common.sh
git commit -m "feat(scripts): add common.sh module with shared functions"
```

---

## Task 2: Crear módulo database.sh

**Files:**
- Create: `scripts/modules/database.sh`

**Step 1: Crear database.sh**

```bash
#!/bin/bash
# =============================================================================
# database.sh - PostgreSQL installation and configuration
# =============================================================================

set -Eeuo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# =============================================================================
# PostgreSQL Installation
# =============================================================================
install_postgresql() {
    log "📦 Installing PostgreSQL..."
    
    if command -v psql &>/dev/null; then
        log_ok "PostgreSQL already installed: $(psql --version)"
        return 0
    fi

    # Install PostgreSQL
    run_sudo apt-get update -qq
    run_sudo apt-get install -y postgresql postgresql-contrib

    # Start and enable service
    run_sudo systemctl enable --now postgresql

    if command -v psql &>/dev/null; then
        log_ok "PostgreSQL installed: $(psql --version)"
    else
        log_err "PostgreSQL installation failed"
        return 1
    fi
}

# =============================================================================
# Create Database and User
# =============================================================================
create_database_and_user() {
    local db_name="${1:-usipipo}"
    local db_user="${2:-usipipo}"
    local db_password="${3:-}"
    
    # Generate random password if not provided
    if [[ -z "$db_password" ]]; then
        db_password=$(generate_random_string 24)
        log "🔑 Generated database password"
    fi

    log "🗄️ Creating database: $db_name"
    log "👤 Creating user: $db_user"

    # Check if database exists
    if run_sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db_name"; then
        log_warn "Database '$db_name' already exists. Skipping creation."
    else
        run_sudo -u postgres psql -c "CREATE DATABASE $db_name;" 2>/dev/null || {
            log_err "Failed to create database"
            return 1
        }
        log_ok "Database '$db_name' created"
    fi

    # Check if user exists
    if run_sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'" 2>/dev/null | grep -q 1; then
        log_warn "User '$db_user' already exists. Updating password..."
        run_sudo -u postgres psql -c "ALTER USER $db_user WITH PASSWORD '$db_password';" 2>/dev/null
    else
        run_sudo -u postgres psql -c "CREATE USER $db_user WITH PASSWORD '$db_password';" 2>/dev/null || {
            log_err "Failed to create user"
            return 1
        }
        log_ok "User '$db_user' created"
    fi

    # Grant privileges
    run_sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;" 2>/dev/null
    run_sudo -u postgres psql -d "$db_name" -c "GRANT ALL ON SCHEMA public TO $db_user;" 2>/dev/null
    
    log_ok "Privileges granted"

    # Save credentials
    save_db_credentials "$db_name" "$db_user" "$db_password"
    
    echo ""
    log "📋 Database Credentials:"
    echo "   Database: $db_name"
    echo "   User: $db_user"
    echo "   Password: [saved to .env]"
    echo ""
}

# =============================================================================
# Save Database Credentials to .env
# =============================================================================
save_db_credentials() {
    local db_name="$1"
    local db_user="$2"
    local db_password="$3"
    
    local db_host="localhost"
    local db_port="5432"
    
    # Construct DATABASE_URL
    local database_url="postgresql+asyncpg://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}"

    log "💾 Saving database credentials to .env..."
    
    env_set "DB_NAME" "$db_name"
    env_set "DB_USER" "$db_user"
    env_set "DB_PASSWORD" "$db_password"
    env_set "DB_HOST" "$db_host"
    env_set "DB_PORT" "$db_port"
    env_set "DATABASE_URL" "$database_url"
    
    log_ok "Database credentials saved to .env"
}

# =============================================================================
# Configure PostgreSQL (pg_hba.conf)
# =============================================================================
configure_postgresql() {
    log "⚙️ Configuring PostgreSQL..."
    
    # Find pg_hba.conf location
    local pg_hba_conf
    pg_hba_conf=$(run_sudo -u postgres psql -tAc "SHOW hba_file" 2>/dev/null | head -1)
    
    if [[ -z "$pg_hba_conf" ]]; then
        log_warn "Could not find pg_hba.conf, using default location"
        pg_hba_conf="/etc/postgresql/$(pg_config --version | grep -oP '\d+' | head -1)/main/pg_hba.conf"
    fi

    # Ensure local connections use md5
    if run_sudo grep -q "^local.*all.*all.*peer" "$pg_hba_conf" 2>/dev/null; then
        log "Updating pg_hba.conf to use md5 authentication..."
        run_sudo sed -i 's/^local\s*all\s*all\s*peer/local all all md5/' "$pg_hba_conf"
        
        # Restart PostgreSQL
        run_sudo systemctl restart postgresql
        log_ok "PostgreSQL configured and restarted"
    else
        log "pg_hba.conf already configured correctly"
    fi
}

# =============================================================================
# Check PostgreSQL Status
# =============================================================================
check_postgresql_status() {
    log "📊 PostgreSQL Status:"
    
    if run_sudo systemctl is-active --quiet postgresql; then
        echo "   Status: ✅ Running"
        echo "   Version: $(psql --version)"
        echo "   Port: $(run_sudo -u postgres psql -tAc "SHOW port" 2>/dev/null || echo '5432')"
    else
        echo "   Status: ❌ Not running"
    fi
}

# =============================================================================
# Full Database Setup
# =============================================================================
setup_database() {
    log_header="🗄️ DATABASE SETUP"
    log "$log_header"
    
    install_postgresql || return 1
    create_database_and_user || return 1
    configure_postgresql || return 1
    
    log_ok "Database setup complete!"
}

# =============================================================================
# Main entry point if run directly
# =============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    setup_database
fi
```

**Step 2: Verificar sintaxis**

Run: `bash -n scripts/modules/database.sh`

**Step 3: Commit**

```bash
git add scripts/modules/database.sh
git commit -m "feat(scripts): add database.sh module for PostgreSQL setup"
```

---

## Task 3: Crear módulo python.sh

**Files:**
- Create: `scripts/modules/python.sh`

**Step 1: Crear python.sh**

```bash
#!/bin/bash
# =============================================================================
# python.sh - Python environment setup
# =============================================================================

set -Eeuo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# =============================================================================
# Verify Python Version
# =============================================================================
verify_python_version() {
    local min_major=3
    local min_minor=11
    
    if ! command -v python3 &>/dev/null; then
        log_err "Python3 not found. Please install Python ${min_major}.${min_minor}+"
        return 1
    fi
    
    local version
    version=$(python3 --version 2>&1 | awk '{print $2}')
    local major minor
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)
    
    log "🐍 Python version: $version"
    
    if [[ "$major" -lt "$min_major" ]] || { [[ "$major" -eq "$min_major" ]] && [[ "$minor" -lt "$min_minor" ]]; }; then
        log_err "Python ${min_major}.${min_minor}+ required, found $version"
        return 1
    fi
    
    log_ok "Python version satisfies requirements (>= ${min_major}.${min_minor})"
    return 0
}

# =============================================================================
# Install System Python Dependencies
# =============================================================================
install_python_system_deps() {
    log "📦 Installing Python system dependencies..."
    
    run_sudo apt-get update -qq
    run_sudo apt-get install -y python3-venv python3-pip python3-dev
    
    log_ok "Python system dependencies installed"
}

# =============================================================================
# Create Virtual Environment
# =============================================================================
create_venv() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    
    log "🔧 Creating virtual environment at: $venv_path"
    
    if [[ -d "$venv_path" ]]; then
        log_warn "Virtual environment already exists at $venv_path"
        if ! confirm "Delete and recreate?"; then
            log "Keeping existing virtual environment"
            return 0
        fi
        rm -rf "$venv_path"
    fi
    
    python3 -m venv "$venv_path"
    
    log_ok "Virtual environment created"
    
    # Upgrade pip
    log "📦 Upgrading pip..."
    "$venv_path/bin/pip" install --upgrade pip --quiet
    
    log_ok "Pip upgraded"
}

# =============================================================================
# Install Requirements
# =============================================================================
install_requirements() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    local requirements_file="${2:-$PROJECT_DIR/requirements.txt}"
    
    if [[ ! -d "$venv_path" ]]; then
        log_err "Virtual environment not found at $venv_path"
        return 1
    fi
    
    if [[ ! -f "$requirements_file" ]]; then
        log_err "Requirements file not found at $requirements_file"
        return 1
    fi
    
    log "📦 Installing Python dependencies from $requirements_file..."
    
    "$venv_path/bin/pip" install -r "$requirements_file"
    
    log_ok "Python dependencies installed"
    
    # Show installed packages count
    local count
    count=$("$venv_path/bin/pip" list --format=freeze 2>/dev/null | wc -l)
    log "📊 Total packages installed: $count"
}

# =============================================================================
# Verify Installation
# =============================================================================
verify_installation() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    
    log "🔍 Verifying Python installation..."
    
    # Check key packages
    local -a packages=("telegram" "sqlalchemy" "alembic" "pydantic")
    local failed=0
    
    for pkg in "${packages[@]}"; do
        if "$venv_path/bin/python" -c "import $pkg" 2>/dev/null; then
            log_ok "Package '$pkg' installed correctly"
        else
            log_err "Package '$pkg' not found"
            ((failed++))
        fi
    done
    
    if [[ $failed -gt 0 ]]; then
        log_err "$failed package(s) failed verification"
        return 1
    fi
    
    log_ok "All key packages verified"
}

# =============================================================================
# Full Python Setup
# =============================================================================
setup_python() {
    log_header="🐍 PYTHON SETUP"
    log "$log_header"
    
    verify_python_version || return 1
    install_python_system_deps || return 1
    create_venv || return 1
    install_requirements || return 1
    verify_installation || return 1
    
    log_ok "Python setup complete!"
}

# =============================================================================
# Main entry point if run directly
# =============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    setup_python
fi
```

**Step 2: Verificar sintaxis**

Run: `bash -n scripts/modules/python.sh`

**Step 3: Commit**

```bash
git add scripts/modules/python.sh
git commit -m "feat(scripts): add python.sh module for venv and dependencies"
```

---

## Task 4: Crear módulo systemd.sh

**Files:**
- Create: `scripts/modules/systemd.sh`

**Step 1: Crear systemd.sh**

```bash
#!/bin/bash
# =============================================================================
# systemd.sh - Systemd service creation and management
# =============================================================================

set -Eeuo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# =============================================================================
# Create Systemd Service File
# =============================================================================
create_service_file() {
    local service_name="${1:-usipipo}"
    local project_dir="${2:-$PROJECT_DIR}"
    local venv_path="${3:-$project_dir/venv}"
    local service_file="/etc/systemd/system/${service_name}.service"
    
    log "📝 Creating systemd service: $service_name"
    
    # Check if service already exists
    if [[ -f "$service_file" ]]; then
        log_warn "Service file already exists at $service_file"
        if ! confirm "Overwrite existing service file?"; then
            log "Keeping existing service file"
            return 0
        fi
    fi
    
    # Create service file
    run_sudo tee "$service_file" > /dev/null <<EOF
[Unit]
Description=uSipipo VPN Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${project_dir}
Environment="PATH=${venv_path}/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${project_dir}/.env
ExecStart=${venv_path}/bin/python ${project_dir}/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    run_sudo chmod 644 "$service_file"
    
    log_ok "Service file created at $service_file"
}

# =============================================================================
# Enable Service
# =============================================================================
enable_service() {
    local service_name="${1:-usipipo}"
    
    log "🔄 Enabling service: $service_name"
    
    run_sudo systemctl daemon-reload
    run_sudo systemctl enable "$service_name"
    
    log_ok "Service enabled"
}

# =============================================================================
# Start Service
# =============================================================================
start_service() {
    local service_name="${1:-usipipo}"
    
    log "🚀 Starting service: $service_name"
    
    run_sudo systemctl start "$service_name"
    sleep 2
    
    if run_sudo systemctl is-active --quiet "$service_name"; then
        log_ok "Service started successfully"
    else
        log_err "Service failed to start. Check logs with: journalctl -u $service_name -f"
        return 1
    fi
}

# =============================================================================
# Stop Service
# =============================================================================
stop_service() {
    local service_name="${1:-usipipo}"
    
    log "🛑 Stopping service: $service_name"
    
    run_sudo systemctl stop "$service_name" 2>/dev/null || true
    log_ok "Service stopped"
}

# =============================================================================
# Show Service Status
# =============================================================================
show_service_status() {
    local service_name="${1:-usipipo}"
    
    log "📊 Service Status: $service_name"
    
    if [[ -f "/etc/systemd/system/${service_name}.service" ]]; then
        run_sudo systemctl status "$service_name" --no-pager || true
    else
        log_warn "Service not installed"
    fi
}

# =============================================================================
# View Service Logs
# =============================================================================
view_service_logs() {
    local service_name="${1:-usipipo}"
    local lines="${2:-100}"
    
    log "📄 Service Logs (last $lines lines):"
    run_sudo journalctl -u "$service_name" -n "$lines" --no-pager
}

# =============================================================================
# Full Systemd Setup
# =============================================================================
setup_systemd() {
    local service_name="${1:-usipipo}"
    
    log_header="🚀 SYSTEMD SERVICE SETUP"
    log "$log_header"
    
    # Verify .env exists
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        log_err ".env file not found. Run database setup first."
        return 1
    fi
    
    # Verify venv exists
    if [[ ! -d "$PROJECT_DIR/venv" ]]; then
        log_err "Virtual environment not found. Run Python setup first."
        return 1
    fi
    
    # Verify main.py exists
    if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
        log_err "main.py not found in $PROJECT_DIR"
        return 1
    fi
    
    create_service_file "$service_name" || return 1
    enable_service "$service_name" || return 1
    
    echo ""
    log "Service created but NOT started yet."
    log "To start: sudo systemctl start $service_name"
    log "To view logs: sudo journalctl -u $service_name -f"
    echo ""
    
    if confirm "Start the service now?"; then
        start_service "$service_name"
    fi
    
    log_ok "Systemd setup complete!"
}

# =============================================================================
# Main entry point if run directly
# =============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    setup_systemd
fi
```

**Step 2: Verificar sintaxis**

Run: `bash -n scripts/modules/systemd.sh`

**Step 3: Commit**

```bash
git add scripts/modules/systemd.sh
git commit -m "feat(scripts): add systemd.sh module for service management"
```

---

## Task 5: Crear módulo bot.sh

**Files:**
- Create: `scripts/modules/bot.sh`

**Step 1: Crear bot.sh**

```bash
#!/bin/bash
# =============================================================================
# bot.sh - Bot validation and execution
# =============================================================================

set -Eeuo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# =============================================================================
# Validate Environment Variables
# =============================================================================
validate_env() {
    log "🔍 Validating environment configuration..."
    
    local -a required_vars=("TELEGRAM_TOKEN" "DATABASE_URL")
    local -a missing=()
    
    for var in "${required_vars[@]}"; do
        local value
        value=$(env_get "$var" 2>/dev/null || true)
        if [[ -z "$value" ]]; then
            missing+=("$var")
        else
            log_ok "✓ $var is set"
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_err "Missing required environment variables: ${missing[*]}"
        log_err "Please configure .env file before running the bot"
        return 1
    fi
    
    log_ok "All required environment variables are set"
}

# =============================================================================
# Run Database Migrations
# =============================================================================
run_migrations() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    
    log "🔄 Running database migrations..."
    
    if [[ ! -d "$venv_path" ]]; then
        log_err "Virtual environment not found at $venv_path"
        return 1
    fi
    
    # Check alembic is installed
    if ! "$venv_path/bin/python" -c "import alembic" 2>/dev/null; then
        log_err "Alembic not installed in virtual environment"
        return 1
    fi
    
    # Check alembic.ini exists
    if [[ ! -f "$PROJECT_DIR/alembic.ini" ]]; then
        log_err "alembic.ini not found in $PROJECT_DIR"
        return 1
    fi
    
    # Run migrations
    cd "$PROJECT_DIR"
    "$venv_path/bin/alembic" upgrade head
    
    log_ok "Database migrations completed"
}

# =============================================================================
# Check Migration Status
# =============================================================================
check_migration_status() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    
    log "📊 Migration Status:"
    
    cd "$PROJECT_DIR"
    "$venv_path/bin/alembic" current 2>/dev/null || log_warn "No migrations applied yet"
}

# =============================================================================
# Start Bot (Interactive)
# =============================================================================
start_bot_interactive() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    
    log "🤖 Starting bot in interactive mode..."
    
    validate_env || return 1
    
    if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
        log_err "main.py not found in $PROJECT_DIR"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    log "Press Ctrl+C to stop the bot"
    echo ""
    
    "$venv_path/bin/python" main.py
}

# =============================================================================
# Start Bot (Background)
# =============================================================================
start_bot_background() {
    local venv_path="${1:-$PROJECT_DIR/venv}"
    local log_file="${2:-$PROJECT_DIR/logs/bot.log}"
    
    log "🤖 Starting bot in background..."
    
    validate_env || return 1
    
    mkdir -p "$(dirname "$log_file")"
    
    cd "$PROJECT_DIR"
    nohup "$venv_path/bin/python" main.py > "$log_file" 2>&1 &
    local pid=$!
    
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        log_ok "Bot started with PID: $pid"
        log "Logs: $log_file"
        echo "$pid" > "$PROJECT_DIR/bot.pid"
    else
        log_err "Bot failed to start. Check logs at $log_file"
        return 1
    fi
}

# =============================================================================
# Stop Bot (Background)
# =============================================================================
stop_bot_background() {
    local pid_file="$PROJECT_DIR/bot.pid"
    
    if [[ ! -f "$pid_file" ]]; then
        log_warn "No bot.pid file found. Is the bot running?"
        return 0
    fi
    
    local pid
    pid=$(cat "$pid_file")
    
    if kill -0 "$pid" 2>/dev/null; then
        log "🛑 Stopping bot (PID: $pid)..."
        kill "$pid"
        rm -f "$pid_file"
        log_ok "Bot stopped"
    else
        log_warn "Bot process not found (PID: $pid)"
        rm -f "$pid_file"
    fi
}

# =============================================================================
# Full Bot Setup
# =============================================================================
setup_bot() {
    log_header="🤖 BOT SETUP"
    log "$log_header"
    
    validate_env || return 1
    
    echo ""
    log "Ready to run migrations and start the bot."
    echo ""
    
    if confirm "Run database migrations now?"; then
        run_migrations || return 1
    fi
    
    echo ""
    log "Bot is ready to start!"
    log "Options:"
    log "  1) Start interactively (foreground)"
    log "  2) Start in background"
    log "  3) Use systemd service (recommended)"
    echo ""
    
    read -r -p "Select option [1-3]: " choice
    case "$choice" in
        1) start_bot_interactive ;;
        2) start_bot_background ;;
        3) log "Use: sudo systemctl start usipipo" ;;
        *) log_warn "Invalid option" ;;
    esac
}

# =============================================================================
# Main entry point if run directly
# =============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    setup_bot
fi
```

**Step 2: Verificar sintaxis**

Run: `bash -n scripts/modules/bot.sh`

**Step 3: Commit**

```bash
git add scripts/modules/bot.sh
git commit -m "feat(scripts): add bot.sh module for bot management"
```

---

## Task 6: Mover y actualizar install.sh como módulo VPN

**Files:**
- Move: `scripts/install.sh` → `scripts/modules/vpn.sh` (keep original in scripts/ for backward compat)
- Modify: Update install.sh to source common.sh

**Step 1: Crear modules/vpn.sh (copia de install.sh actual con sourcing)**

```bash
# Copy existing install.sh to modules/vpn.sh
cp scripts/install.sh scripts/modules/vpn.sh
```

**Step 2: Agregar sourcing de common.sh al inicio de vpn.sh**

Agregar después del shebang y set:
```bash
# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"
```

**Step 3: Eliminar funciones duplicadas de vpn.sh que ya están en common.sh**

- Colores y constantes
- Funciones log, log_ok, log_warn, log_err
- run_sudo, confirm
- get_public_ip
- ensure_env_exists, env_set

**Step 4: Verificar sintaxis**

Run: `bash -n scripts/modules/vpn.sh`

**Step 5: Commit**

```bash
git add scripts/modules/vpn.sh
git commit -m "refactor(scripts): add vpn.sh module from install.sh"
```

---

## Task 7: Crear setup.sh principal (orquestador)

**Files:**
- Create: `scripts/setup.sh`

**Step 1: Crear setup.sh**

```bash
#!/bin/bash
# =============================================================================
# setup.sh - uSipipo Setup Manager (Main Orchestrator)
# =============================================================================
# Author: uSipipo Team
# License: MIT
# Description: Interactive setup manager for uSipipo VPN Bot
# =============================================================================

set -Eeuo pipefail

# =============================================================================
# Paths & Directories
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MODULES_DIR="$SCRIPT_DIR/modules"

# Source common functions
# shellcheck source=./modules/common.sh
source "${MODULES_DIR}/common.sh"

# Log setup
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

# Temporary directory
TMPDIR=$(mktemp -d 2>/dev/null || echo "")
if [[ -n "$TMPDIR" ]]; then
    trap 'rm -rf -- "$TMPDIR" 2>/dev/null || true' EXIT
fi

# Error trap
trap 'log_err "Error on line $LINENO in ${FUNCNAME[0]:-main}"' ERR

# =============================================================================
# System Status
# =============================================================================
show_system_status() {
    clear
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo -e "${WHITE}              ${HEADER_ICON} uSipipo System Status ${HEADER_ICON}${NC}"
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo ""
    
    # Python
    echo -e "${WHITE}Python:${NC}"
    if command -v python3 &>/dev/null; then
        echo "  ✅ $(python3 --version)"
    else
        echo "  ❌ Not installed"
    fi
    
    # Virtual Environment
    echo ""
    echo -e "${WHITE}Virtual Environment:${NC}"
    if [[ -d "$PROJECT_DIR/venv" ]]; then
        echo "  ✅ $PROJECT_DIR/venv"
    else
        echo "  ❌ Not created"
    fi
    
    # PostgreSQL
    echo ""
    echo -e "${WHITE}PostgreSQL:${NC}"
    if command -v psql &>/dev/null; then
        if run_sudo systemctl is-active --quiet postgresql 2>/dev/null; then
            echo "  ✅ Running ($(psql --version))"
        else
            echo "  ⚠️  Installed but not running"
        fi
    else
        echo "  ❌ Not installed"
    fi
    
    # Docker
    echo ""
    echo -e "${WHITE}Docker:${NC}"
    if command -v docker &>/dev/null; then
        if run_sudo systemctl is-active --quiet docker 2>/dev/null; then
            echo "  ✅ Running"
        else
            echo "  ⚠️  Installed but not running"
        fi
    else
        echo "  ❌ Not installed"
    fi
    
    # Outline (shadowbox container)
    echo ""
    echo -e "${WHITE}Outline (shadowbox):${NC}"
    if command -v docker &>/dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -qw shadowbox; then
        echo "  ✅ Running"
    else
        echo "  ❌ Not running"
    fi
    
    # WireGuard
    echo ""
    echo -e "${WHITE}WireGuard:${NC}"
    if run_sudo systemctl is-active --quiet wg-quick@wg0 2>/dev/null; then
        echo "  ✅ Running (wg0)"
    else
        echo "  ❌ Not running"
    fi
    
    # Systemd Service
    echo ""
    echo -e "${WHITE}Systemd Service (usipipo):${NC}"
    if run_sudo systemctl is-active --quiet usipipo 2>/dev/null; then
        echo "  ✅ Running"
    elif [[ -f "/etc/systemd/system/usipipo.service" ]]; then
        echo "  ⚠️  Created but not running"
    else
        echo "  ❌ Not created"
    fi
    
    # Environment
    echo ""
    echo -e "${WHITE}Environment (.env):${NC}"
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        local token db_url
        token=$(env_get "TELEGRAM_TOKEN" "$PROJECT_DIR/.env" 2>/dev/null || true)
        db_url=$(env_get "DATABASE_URL" "$PROJECT_DIR/.env" 2>/dev/null || true)
        [[ -n "$token" ]] && echo "  ✅ TELEGRAM_TOKEN set" || echo "  ❌ TELEGRAM_TOKEN missing"
        [[ -n "$db_url" ]] && echo "  ✅ DATABASE_URL set" || echo "  ❌ DATABASE_URL missing"
    else
        echo "  ❌ .env file not found"
    fi
    
    echo ""
}

# =============================================================================
# Full Setup
# =============================================================================
run_full_setup() {
    clear
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo -e "${WHITE}        ${HEADER_ICON} Full Setup (Automated) ${HEADER_ICON}${NC}"
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo ""
    
    log "This will perform the following steps:"
    echo "  1. Install Docker"
    echo "  2. Install PostgreSQL and create database"
    echo "  3. Create Python virtual environment"
    echo "  4. Install Python dependencies"
    echo "  5. Run database migrations"
    echo "  6. Create systemd service"
    echo ""
    
    if ! confirm "Proceed with full setup?"; then
        log "Full setup cancelled"
        return 1
    fi
    
    # Step 1: Docker
    log "📦 Step 1/6: Docker..."
    source "${MODULES_DIR}/vpn.sh"
    install_docker_wrapper || log_warn "Docker installation skipped or failed"
    
    # Step 2: PostgreSQL
    log "📦 Step 2/6: PostgreSQL..."
    source "${MODULES_DIR}/database.sh"
    setup_database || { log_err "Database setup failed"; return 1; }
    
    # Step 3 & 4: Python
    log "📦 Step 3-4/6: Python environment..."
    source "${MODULES_DIR}/python.sh"
    setup_python || { log_err "Python setup failed"; return 1; }
    
    # Step 5: Migrations
    log "📦 Step 5/6: Database migrations..."
    source "${MODULES_DIR}/bot.sh"
    run_migrations "$PROJECT_DIR/venv" || { log_err "Migrations failed"; return 1; }
    
    # Step 6: Systemd
    log "📦 Step 6/6: Systemd service..."
    source "${MODULES_DIR}/systemd.sh"
    setup_systemd "usipipo" || log_warn "Systemd setup skipped"
    
    echo ""
    log_ok "🎉 Full setup complete!"
    echo ""
    log "Next steps:"
    echo "  1. Configure VPN (options 2 or 3) if needed"
    echo "  2. Set TELEGRAM_TOKEN in .env if not done"
    echo "  3. Start bot: sudo systemctl start usipipo"
    echo "  4. View logs: sudo journalctl -u usipipo -f"
    echo ""
}

# =============================================================================
# Main Menu
# =============================================================================
show_menu() {
    clear
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo -e "${WHITE}              ${HEADER_ICON} uSipipo Setup Manager ${HEADER_ICON}${NC}"
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} 🐳 Install Docker"
    echo -e "  ${GREEN}2)${NC} ⚙️  Install Outline Server (VPN)"
    echo -e "  ${GREEN}3)${NC} ⚙️  Install WireGuard Server (VPN)"
    echo -e "  ${BLUE}4)${NC} 🗄️  Install/Configure PostgreSQL"
    echo -e "  ${BLUE}5)${NC} 🐍 Setup Python Environment (venv + deps)"
    echo -e "  ${PURPLE}6)${NC} 🔄 Run Database Migrations (Alembic)"
    echo -e "  ${PURPLE}7)${NC} 🚀 Create Systemd Service"
    echo -e "  ${WHITE}8)${NC} ▶️  Start Bot (main.py)"
    echo -e "  ${YELLOW}9)${NC} 🔁 Full Setup (1-7 automated)"
    echo -e "  ${WHITE}10)${NC} 📊 System Status"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    read -r -p "$(echo -e "${WHITE}Select option [0-10]:${NC}")" choice

    case "$choice" in
        1)
            source "${MODULES_DIR}/vpn.sh"
            install_docker_wrapper
            ;;
        2)
            source "${MODULES_DIR}/vpn.sh"
            install_outline
            ;;
        3)
            source "${MODULES_DIR}/vpn.sh"
            install_wireguard
            fix_wireguard_mtu
            configure_bot_permissions
            ;;
        4)
            source "${MODULES_DIR}/database.sh"
            setup_database
            ;;
        5)
            source "${MODULES_DIR}/python.sh"
            setup_python
            ;;
        6)
            source "${MODULES_DIR}/bot.sh"
            run_migrations "$PROJECT_DIR/venv"
            ;;
        7)
            source "${MODULES_DIR}/systemd.sh"
            setup_systemd "usipipo"
            ;;
        8)
            source "${MODULES_DIR}/bot.sh"
            setup_bot
            ;;
        9)
            run_full_setup
            ;;
        10)
            show_system_status
            ;;
        0)
            log "Exiting."
            exit 0
            ;;
        *)
            log_err "Invalid option"
            ;;
    esac

    echo ""
    read -r -p "Press Enter to continue..."
    show_menu
}

# =============================================================================
# Bootstrap
# =============================================================================
bootstrap() {
    # Check dependencies
    check_dependencies || exit 1
    
    # Ensure .env exists
    ensure_env_exists "$PROJECT_DIR/.env" "$PROJECT_DIR/example.env"
    
    log "🛡️ uSipipo Setup Manager v1.0"
    log "Project directory: $PROJECT_DIR"
}

# =============================================================================
# Main
# =============================================================================
main() {
    bootstrap
    show_menu
}

main "$@"
```

**Step 2: Verificar sintaxis**

Run: `bash -n scripts/setup.sh`

**Step 3: Commit**

```bash
git add scripts/setup.sh
git commit -m "feat(scripts): add setup.sh main orchestrator with menu"
```

---

## Task 8: Actualizar example.env con nuevas variables

**Files:**
- Modify: `example.env`

**Step 1: Agregar variables de base de datos**

```bash
# Add to example.env:
DB_NAME=usipipo
DB_USER=usipipo
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=
```

**Step 2: Commit**

```bash
git add example.env
git commit -m "chore: update example.env with database variables"
```

---

## Task 9: Actualizar AGENTS.md

**Files:**
- Modify: `AGENTS.md`

**Step 1: Agregar sección de setup.sh**

Agregar al final de AGENTS.md:

```markdown
## Setup Script

The project includes a comprehensive setup script for automated installation:

```bash
# Run the setup manager
./scripts/setup.sh
```

### Setup Options

1. **Docker** - Install Docker (required for Outline)
2. **Outline** - Install Outline VPN Server
3. **WireGuard** - Install WireGuard VPN Server
4. **PostgreSQL** - Install and configure database
5. **Python** - Create venv and install dependencies
6. **Migrations** - Run Alembic migrations
7. **Systemd** - Create and enable service
8. **Bot** - Start the bot
9. **Full Setup** - Automated complete installation

### Manual Installation

If you prefer manual installation, follow these steps:

1. Install PostgreSQL: `sudo apt install postgresql postgresql-contrib`
2. Create database and user
3. Create venv: `python3 -m venv venv`
4. Install deps: `./venv/bin/pip install -r requirements.txt`
5. Configure `.env` with credentials
6. Run migrations: `./venv/bin/alembic upgrade head`
7. Start bot: `./venv/bin/python main.py`
```

**Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md with setup script documentation"
```

---

## Task 10: Verificación final y pruebas

**Step 1: Verificar sintaxis de todos los scripts**

```bash
for f in scripts/setup.sh scripts/modules/*.sh; do
    echo "Checking: $f"
    bash -n "$f" || exit 1
done
```

**Step 2: Verificar imports/source**

```bash
# Verify common.sh can be sourced
bash -c "source scripts/modules/common.sh && echo 'OK'"
```

**Step 3: Commit final**

```bash
git add -A
git commit -m "feat: complete modular setup script implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | common.sh - funciones compartidas | `scripts/modules/common.sh` |
| 2 | database.sh - PostgreSQL | `scripts/modules/database.sh` |
| 3 | python.sh - venv + deps | `scripts/modules/python.sh` |
| 4 | systemd.sh - servicio | `scripts/modules/systemd.sh` |
| 5 | bot.sh - validación y ejecución | `scripts/modules/bot.sh` |
| 6 | vpn.sh - VPN module | `scripts/modules/vpn.sh` |
| 7 | setup.sh - orquestador | `scripts/setup.sh` |
| 8 | example.env - variables DB | `example.env` |
| 9 | AGENTS.md - documentación | `AGENTS.md` |
| 10 | Verificación final | todos los scripts |
