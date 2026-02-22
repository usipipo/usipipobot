#!/usr/bin/env bash

# Guard against re-sourcing
if [[ -n "${_COMMON_SH_LOADED:-}" ]]; then
    return 0 2>/dev/null || exit 0
fi
_COMMON_SH_LOADED=1

set -Eeuo pipefail

# ==============================================================================
# common.sh - Shared functions for uSipipo setup scripts
# ==============================================================================

# ------------------------------------------------------------------------------
# Colors and Constants
# ------------------------------------------------------------------------------
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[0;37m'
readonly GRAY='\033[0;90m'
readonly NC='\033[0m' # No Color

readonly SEPARATOR="════════════════════════════════════════════════════════════════"
readonly HEADER_ICON="🚀"
readonly SUCCESS_ICON="✅"
readonly ERROR_ICON="❌"
readonly INFO_ICON="ℹ️"

# ------------------------------------------------------------------------------
# Logging Functions
# ------------------------------------------------------------------------------

log() {
    local message="${1:-}"
    echo -e "${BLUE}[INFO]${NC} ${message}" >&2
}

log_ok() {
    local message="${1:-}"
    echo -e "${GREEN}[OK]${NC} ${message}" >&2
}

log_warn() {
    local message="${1:-}"
    echo -e "${YELLOW}[WARN]${NC} ${message}" >&2
}

log_err() {
    local message="${1:-}"
    echo -e "${RED}[ERROR]${NC} ${message}" >&2
}

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

run_sudo() {
    if [[ $EUID -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

confirm() {
    local prompt="${1:-Continue?}"
    local default="${2:-n}"
    local response

    if [[ "${default}" == "y" ]]; then
        prompt="${prompt} [Y/n]: "
    else
        prompt="${prompt} [y/N]: "
    fi

    read -r -p "${prompt}" response
    response="${response:-${default}}"

    [[ "${response}" =~ ^[Yy]$ ]]
}

generate_random_string() {
    local length="${1:-32}"
    local use_special="${2:-false}"
    local password

    if command -v openssl &>/dev/null; then
        if [[ "${use_special}" == "true" ]]; then
            password=$(openssl rand -base64 48 | tr -d '/+=' | head -c "${length}")
        else
            password=$(openssl rand -hex 32 | head -c "${length}")
        fi
    else
        if [[ "${use_special}" == "true" ]]; then
            password=$(head -c 100 /dev/urandom | base64 | tr -d '/+=' | head -c "${length}")
        else
            password=$(head -c 100 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c "${length}")
        fi
    fi

    echo "${password}"
}

check_dependencies() {
    local missing=()
    local cmd

    for cmd in "$@"; do
        if ! command -v "${cmd}" &>/dev/null; then
            missing+=("${cmd}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_err "Missing required dependencies: ${missing[*]}"
        log "Install with: apt install ${missing[*]}"
        return 1
    fi

    log_ok "All dependencies satisfied"
    return 0
}

get_public_ip() {
    local ip=""
    local services=(
        "https://api.ipify.org"
        "https://ifconfig.me"
        "https://icanhazip.com"
        "https://ipecho.net/plain"
        "https://ident.me"
    )

    for service in "${services[@]}"; do
        if command -v curl &>/dev/null; then
            ip=$(curl -s --max-time 5 "${service}" 2>/dev/null || true)
        elif command -v wget &>/dev/null; then
            ip=$(wget -qO- --timeout=5 "${service}" 2>/dev/null || true)
        fi

        if [[ -n "${ip}" && "${ip}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "${ip}"
            return 0
        fi
    done

    log_err "Could not detect public IP address"
    return 1
}

ensure_env_exists() {
    local env_file="${1:-.env}"
    local example_file="${2:-example.env}"

    if [[ -f "${env_file}" ]]; then
        return 0
    fi

    if [[ -f "${example_file}" ]]; then
        log "Creating ${env_file} from ${example_file}..."
        cp "${example_file}" "${env_file}"
        log_ok "Created ${env_file}"
    else
        log "Creating empty ${env_file}..."
        touch "${env_file}"
        log_ok "Created empty ${env_file}"
    fi
}

env_set() {
    local env_file="${1:-.env}"
    local key="${2:-}"
    local value="${3:-}"
    local temp_file

    if [[ -z "${key}" ]]; then
        log_err "env_set: key is required"
        return 1
    fi

    ensure_env_exists "${env_file}"

    temp_file=$(mktemp)
    if grep -q "^${key}=" "${env_file}" 2>/dev/null; then
        grep -v "^${key}=" "${env_file}" > "${temp_file}" 2>/dev/null || true
    else
        cat "${env_file}" > "${temp_file}" 2>/dev/null || true
    fi
    echo "${key}=${value}" >> "${temp_file}"
    mv "${temp_file}" "${env_file}"
}

env_get() {
    local env_file="${1:-.env}"
    local key="${2:-}"
    local value

    if [[ -z "${key}" ]]; then
        log_err "env_get: key is required"
        return 1
    fi

    if [[ ! -f "${env_file}" ]]; then
        return 1
    fi

    value=$(grep "^${key}=" "${env_file}" 2>/dev/null | head -1 | cut -d'=' -f2- || true)

    if [[ -n "${value}" ]]; then
        echo "${value}"
        return 0
    fi

    return 1
}
