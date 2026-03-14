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
    # shellcheck source=./modules/vpn.sh
    source "${MODULES_DIR}/vpn.sh"
    install_docker_wrapper || log_warn "Docker installation skipped or failed"

    # Step 2: PostgreSQL
    log "📦 Step 2/6: PostgreSQL..."
    # shellcheck source=./modules/database.sh
    source "${MODULES_DIR}/database.sh"
    setup_database || { log_err "Database setup failed"; return 1; }

    # Step 3 & 4: Python
    log "📦 Step 3-4/6: Python environment..."
    # shellcheck source=./modules/python.sh
    source "${MODULES_DIR}/python.sh"
    setup_python || { log_err "Python setup failed"; return 1; }

    # Step 5: Migrations
    log "📦 Step 5/6: Database migrations..."
    # shellcheck source=./modules/bot.sh
    source "${MODULES_DIR}/bot.sh"
    run_migrations "$PROJECT_DIR/venv" || { log_err "Migrations failed"; return 1; }

    # Step 6: Systemd
    log "📦 Step 6/6: Systemd service..."
    # shellcheck source=./modules/systemd.sh
    source "${MODULES_DIR}/systemd.sh"
    setup_systemd "$PROJECT_DIR" || log_warn "Systemd setup skipped"

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
# Setup Outline Auto-Updates
# =============================================================================
setup_outline_autoupdates() {
    clear
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo -e "${WHITE}        ${HEADER_ICON} Setup Outline Auto-Updates ${HEADER_ICON}${NC}"
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo ""

    log "This will configure automatic monthly updates for Outline VPN."
    echo ""
    echo "What it does:"
    echo "  - Checks for new shadowbox image monthly"
    echo "  - Updates container if new version available"
    echo "  - Runs on first Sunday of each month at 3:00 AM"
    echo "  - Logs to: /var/log/outline-update.log"
    echo ""

    if ! command -v docker &>/dev/null; then
        log_err "Docker is not installed. Please install Docker first (option 1)."
        return 1
    fi

    if ! confirm "Proceed with setting up auto-updates?"; then
        log "Auto-update setup cancelled"
        return 1
    fi

    local SCRIPT_PATH="$PROJECT_DIR/scripts/update-outline.sh"

    # Check if script exists
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        log_err "Update script not found: $SCRIPT_PATH"
        return 1
    fi

    # Make script executable
    chmod +x "$SCRIPT_PATH"
    log "Update script ready: $SCRIPT_PATH"

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "update-outline.sh"; then
        log_warn "Cron job for Outline updates already exists."
        if confirm "Replace existing cron job?"; then
            # Remove existing job
            crontab -l 2>/dev/null | grep -v "update-outline.sh" | crontab -
        else
            log "Keeping existing cron job."
            return 0
        fi
    fi

    # Add cron job
    (crontab -l 2>/dev/null; echo "# uSipipo: Outline VPN monthly auto-update - first Sunday at 3:00 AM"; echo "0 3 1-7 * 0 $SCRIPT_PATH") | crontab -

    if [[ $? -eq 0 ]]; then
        log_ok "✅ Auto-updates configured successfully!"
        echo ""
        log "Schedule: First Sunday of each month at 3:00 AM"
        log "Log file: /var/log/outline-update.log"
        log "Manual run: sudo $SCRIPT_PATH"
    else
        log_err "Failed to configure cron job"
        return 1
    fi

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
    echo -e "  ${GREEN}3)${NC} 🔄 Setup Outline Auto-Updates"
    echo -e "  ${GREEN}4)${NC} ⚙️  Install WireGuard Server (VPN)"
    echo -e "  ${BLUE}5)${NC} 🗄️  Install/Configure PostgreSQL"
    echo -e "  ${BLUE}6)${NC} 🐍 Setup Python Environment (venv + deps)"
    echo -e "  ${PURPLE}7)${NC} 🔄 Run Database Migrations (Alembic)"
    echo -e "  ${PURPLE}8)${NC} 🚀 Create Systemd Service"
    echo -e "  ${WHITE}9)${NC} ▶️  Start Bot (main.py)"
    echo -e "  ${YELLOW}10)${NC} 🔁 Full Setup (1-8 automated)"
    echo -e "  ${WHITE}11)${NC} 📊 System Status"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    read -r -p "$(echo -e "${WHITE}Select option [0-11]:${NC}")" choice

    case "$choice" in
        1)
            # shellcheck source=./modules/vpn.sh
            source "${MODULES_DIR}/vpn.sh"
            install_docker_wrapper
            ;;
        2)
            # shellcheck source=./modules/vpn.sh
            source "${MODULES_DIR}/vpn.sh"
            install_outline
            ;;
        3)
            setup_outline_autoupdates
            ;;
        4)
            # shellcheck source=./modules/vpn.sh
            source "${MODULES_DIR}/vpn.sh"
            install_wireguard
            fix_wireguard_mtu
            configure_bot_permissions
            ;;
        5)
            # shellcheck source=./modules/database.sh
            source "${MODULES_DIR}/database.sh"
            setup_database
            ;;
        6)
            # shellcheck source=./modules/python.sh
            source "${MODULES_DIR}/python.sh"
            setup_python
            ;;
        7)
            # shellcheck source=./modules/bot.sh
            source "${MODULES_DIR}/bot.sh"
            run_migrations "$PROJECT_DIR/.env"
            ;;
        8)
            # shellcheck source=./modules/systemd.sh
            source "${MODULES_DIR}/systemd.sh"
            setup_systemd "$PROJECT_DIR"
            ;;
        9)
            # shellcheck source=./modules/bot.sh
            source "${MODULES_DIR}/bot.sh"
            setup_bot
            ;;
        10)
            run_full_setup
            ;;
        11)
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
