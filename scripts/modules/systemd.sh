#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# systemd.sh - Systemd service management for uSipipo VPN Bot
# ==============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common functions
source "${SCRIPT_DIR}/common.sh"

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
readonly SERVICE_NAME="usipipo"
readonly SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# ------------------------------------------------------------------------------
# Service File Creation
# ------------------------------------------------------------------------------

create_service_file() {
    local project_dir="${1:-$(pwd)}"
    local venv_path="${2:-${project_dir}/venv}"
    local user="${3:-${USER}}"

    log "Creating systemd service file..."

    if [[ ! -f "${project_dir}/.env" ]]; then
        log_err ".env file not found at ${project_dir}/.env"
        return 1
    fi

    if [[ ! -d "${venv_path}" ]]; then
        log_err "Virtual environment not found at ${venv_path}"
        return 1
    fi

    if [[ ! -f "${project_dir}/main.py" ]]; then
        log_err "main.py not found at ${project_dir}/main.py"
        return 1
    fi

    local service_content
    service_content=$(cat <<EOF
[Unit]
Description=uSipipo VPN Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=${user}
Group=${user}
WorkingDirectory=${project_dir}
Environment="PATH=${venv_path}/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${project_dir}/.env
ExecStart=${venv_path}/bin/python ${project_dir}/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
)

    echo "${service_content}" | run_sudo tee "${SERVICE_FILE}" > /dev/null
    run_sudo chmod 644 "${SERVICE_FILE}"

    log_ok "Created service file at ${SERVICE_FILE}"
}

# ------------------------------------------------------------------------------
# Service Control Functions
# ------------------------------------------------------------------------------

enable_service() {
    log "Enabling ${SERVICE_NAME} service..."

    run_sudo systemctl daemon-reload
    run_sudo systemctl enable "${SERVICE_NAME}"

    log_ok "Service ${SERVICE_NAME} enabled"
}

start_service() {
    log "Starting ${SERVICE_NAME} service..."

    run_sudo systemctl start "${SERVICE_NAME}"

    log_ok "Service ${SERVICE_NAME} started"
}

stop_service() {
    log "Stopping ${SERVICE_NAME} service..."

    run_sudo systemctl stop "${SERVICE_NAME}"

    log_ok "Service ${SERVICE_NAME} stopped"
}

restart_service() {
    log "Restarting ${SERVICE_NAME} service..."

    run_sudo systemctl restart "${SERVICE_NAME}"

    log_ok "Service ${SERVICE_NAME} restarted"
}

disable_service() {
    log "Disabling ${SERVICE_NAME} service..."

    run_sudo systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    run_sudo systemctl disable "${SERVICE_NAME}"

    log_ok "Service ${SERVICE_NAME} disabled"
}

# ------------------------------------------------------------------------------
# Service Status Functions
# ------------------------------------------------------------------------------

show_service_status() {
    log "Service status for ${SERVICE_NAME}:"
    echo ""

    run_sudo systemctl status "${SERVICE_NAME}" --no-pager || true
}

view_service_logs() {
    local lines="${1:-100}"
    local follow="${2:-false}"

    if [[ "${follow}" == "true" ]]; then
        run_sudo journalctl -u "${SERVICE_NAME}" -f
    else
        run_sudo journalctl -u "${SERVICE_NAME}" -n "${lines}" --no-pager
    fi
}

# ------------------------------------------------------------------------------
# Main Setup Function
# ------------------------------------------------------------------------------

setup_systemd() {
    local project_dir="${1:-$(pwd)}"
    local venv_path="${2:-${project_dir}/venv}"
    local user="${3:-${USER}}"
    local start_now="${4:-true}"

    echo ""
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo -e "${CYAN}  ${HEADER_ICON} Setting up Systemd Service${NC}"
    echo -e "${CYAN}${SEPARATOR}${NC}"
    echo ""

    create_service_file "${project_dir}" "${venv_path}" "${user}"
    enable_service

    if [[ "${start_now}" == "true" ]]; then
        start_service
        sleep 2
        show_service_status
    fi

    echo ""
    echo -e "${GREEN}${SUCCESS_ICON} Systemd service setup complete!${NC}"
    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status ${SERVICE_NAME}   - Check service status"
    echo "  sudo systemctl start ${SERVICE_NAME}    - Start service"
    echo "  sudo systemctl stop ${SERVICE_NAME}     - Stop service"
    echo "  sudo systemctl restart ${SERVICE_NAME}  - Restart service"
    echo "  sudo journalctl -u ${SERVICE_NAME} -f   - Follow logs"
    echo ""
}

# ------------------------------------------------------------------------------
# Cleanup Function
# ------------------------------------------------------------------------------

remove_service() {
    log "Removing ${SERVICE_NAME} service..."

    run_sudo systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    run_sudo systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
    run_sudo rm -f "${SERVICE_FILE}"
    run_sudo systemctl daemon-reload

    log_ok "Service ${SERVICE_NAME} removed"
}
