#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# bot.sh - Bot validation and execution for uSipipo VPN Bot
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

readonly BOT_PID_FILE="bot.pid"
readonly BOT_LOG_FILE="logs/bot.log"
readonly REQUIRED_ENV_VARS=("TELEGRAM_TOKEN" "DATABASE_URL")

validate_env() {
    local env_file="${1:-.env}"
    local missing=()

    if [[ ! -f "${env_file}" ]]; then
        log_err "Environment file not found: ${env_file}"
        log "Run setup first or create ${env_file} from example.env"
        return 1
    fi

    for var in "${REQUIRED_ENV_VARS[@]}"; do
        local value
        value=$(env_get "${env_file}" "${var}" 2>/dev/null || true)
        if [[ -z "${value}" ]]; then
            missing+=("${var}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_err "Missing required environment variables: ${missing[*]}"
        log "Set them in ${env_file}:"
        for var in "${missing[@]}"; do
            echo "  ${var}=your_value_here"
        done
        return 1
    fi

    log_ok "All required environment variables are set"
    return 0
}

run_migrations() {
    local env_file="${1:-.env}"

    log "Running database migrations..."

    cd "${PROJECT_ROOT}" || {
        log_err "Failed to change to project root: ${PROJECT_ROOT}"
        return 1
    }

    if [[ ! -f "alembic.ini" ]]; then
        log_err "alembic.ini not found in project root"
        return 1
    fi

    if [[ ! -f "venv/bin/alembic" ]]; then
        log_err "alembic not found in virtual environment"
        log "Run: source venv/bin/activate && pip install alembic"
        return 1
    fi

    if ! validate_env "${env_file}"; then
        return 1
    fi

    source venv/bin/activate

    if ! alembic upgrade head; then
        log_err "Migration failed"
        return 1
    fi

    log_ok "Migrations completed successfully"
    return 0
}

check_migration_status() {
    log "Checking migration status..."

    if [[ ! -f "alembic.ini" ]]; then
        log_err "alembic.ini not found in project root"
        return 1
    fi

    if [[ ! -f "venv/bin/alembic" ]]; then
        log_err "alembic not found in virtual environment"
        return 1
    fi

    source venv/bin/activate

    log "Current migration version:"
    alembic current

    return 0
}

start_bot_interactive() {
    local env_file="${1:-.env}"

    log "Starting bot in interactive mode..."

    if ! validate_env "${env_file}"; then
        return 1
    fi

    if [[ ! -f "main.py" ]]; then
        log_err "main.py not found in project root"
        return 1
    fi

    if [[ ! -f "venv/bin/python" ]]; then
        log_err "Python not found in virtual environment"
        return 1
    fi

    source venv/bin/activate

    log "Starting bot (Ctrl+C to stop)..."
    python main.py
}

start_bot_background() {
    local env_file="${1:-.env}"

    log "Starting bot in background mode..."

    if ! validate_env "${env_file}"; then
        return 1
    fi

    if [[ ! -f "main.py" ]]; then
        log_err "main.py not found in project root"
        return 1
    fi

    if [[ ! -f "venv/bin/python" ]]; then
        log_err "Python not found in virtual environment"
        return 1
    fi

    if [[ -f "${BOT_PID_FILE}" ]]; then
        local existing_pid
        existing_pid=$(cat "${BOT_PID_FILE}" 2>/dev/null || true)
        if [[ -n "${existing_pid}" ]] && kill -0 "${existing_pid}" 2>/dev/null; then
            log_warn "Bot already running with PID ${existing_pid}"
            log "Stop it first with: stop_bot_background"
            return 1
        fi
        rm -f "${BOT_PID_FILE}"
    fi

    mkdir -p logs

    source venv/bin/activate

    nohup python main.py >> "${BOT_LOG_FILE}" 2>&1 &
    local pid=$!

    echo "${pid}" > "${BOT_PID_FILE}"

    sleep 1

    if kill -0 "${pid}" 2>/dev/null; then
        log_ok "Bot started in background"
        log "PID: ${pid} (saved to ${BOT_PID_FILE})"
        log "Log: ${BOT_LOG_FILE}"
        log "Stop with: stop_bot_background or kill ${pid}"
        return 0
    else
        log_err "Bot failed to start. Check ${BOT_LOG_FILE} for details"
        rm -f "${BOT_PID_FILE}"
        return 1
    fi
}

stop_bot_background() {
    log "Stopping background bot..."

    if [[ ! -f "${BOT_PID_FILE}" ]]; then
        log_warn "No PID file found (${BOT_PID_FILE})"
        log "Bot may not be running or was started without this script"
        return 1
    fi

    local pid
    pid=$(cat "${BOT_PID_FILE}" 2>/dev/null || true)

    if [[ -z "${pid}" ]]; then
        log_err "PID file is empty"
        rm -f "${BOT_PID_FILE}"
        return 1
    fi

    if ! kill -0 "${pid}" 2>/dev/null; then
        log_warn "Process ${pid} is not running"
        rm -f "${BOT_PID_FILE}"
        return 0
    fi

    log "Sending SIGTERM to process ${pid}..."
    kill "${pid}" 2>/dev/null || true

    local attempts=0
    local max_attempts=10

    while kill -0 "${pid}" 2>/dev/null; do
        ((attempts++))
        if [[ ${attempts} -ge ${max_attempts} ]]; then
            log_warn "Process did not stop gracefully, sending SIGKILL..."
            kill -9 "${pid}" 2>/dev/null || true
            sleep 1
            break
        fi
        sleep 1
    done

    if kill -0 "${pid}" 2>/dev/null; then
        log_err "Failed to stop process ${pid}"
        return 1
    fi

    rm -f "${BOT_PID_FILE}"
    log_ok "Bot stopped successfully"
    return 0
}

setup_bot() {
    local env_file="${1:-.env}"
    local skip_migrations="${2:-false}"

    echo -e "${CYAN}${HEADER_ICON} uSipipo Bot Setup${NC}"
    echo -e "${GRAY}${SEPARATOR}${NC}"
    echo

    cd "${PROJECT_ROOT}" || {
        log_err "Failed to change to project root: ${PROJECT_ROOT}"
        return 1
    }

    if [[ ! -f "venv/bin/activate" ]]; then
        log_err "Virtual environment not found"
        log "Run the environment setup first"
        return 1
    fi

    log "Step 1: Validating environment..."
    if ! validate_env "${env_file}"; then
        return 1
    fi

    if [[ "${skip_migrations}" != "true" ]]; then
        log "Step 2: Running migrations..."
        if ! run_migrations "${env_file}"; then
            return 1
        fi
    else
        log "Step 2: Skipping migrations (skip_migrations=${skip_migrations})"
    fi

    echo
    echo -e "${CYAN}${SUCCESS_ICON} Bot setup complete!${NC}"
    echo
    echo "Next steps:"
    echo "  - Start interactively: source scripts/modules/bot.sh && start_bot_interactive"
    echo "  - Start in background: source scripts/modules/bot.sh && start_bot_background"
    echo "  - Stop background:     source scripts/modules/bot.sh && stop_bot_background"
    echo "  - Check migrations:    source scripts/modules/bot.sh && check_migration_status"
    echo

    return 0
}
