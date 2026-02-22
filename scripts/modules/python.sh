#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# python.sh - Python environment setup for uSipipo
# ==============================================================================

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
readonly MIN_PYTHON_VERSION="3.11"
readonly VENV_DIR="venv"
readonly REQUIREMENTS_FILE="requirements.txt"
readonly KEY_PACKAGES=("telegram" "sqlalchemy" "alembic" "pydantic")

# ------------------------------------------------------------------------------
# Python Version Verification
# ------------------------------------------------------------------------------

verify_python_version() {
    local python_cmd="${1:-python3}"
    local version major minor

    log "Verifying Python version..."

    if ! command -v "${python_cmd}" &>/dev/null; then
        log_err "Python not found. Please install Python ${MIN_PYTHON_VERSION} or higher."
        return 1
    fi

    version=$("${python_cmd}" --version 2>&1 | awk '{print $2}')
    major=$(echo "${version}" | cut -d. -f1)
    minor=$(echo "${version}" | cut -d. -f2)

    log "  Detected Python version: ${version}"

    if [[ "${major}" -lt 3 ]] || { [[ "${major}" -eq 3 ]] && [[ "${minor}" -lt 11 ]]; }; then
        log_err "Python ${MIN_PYTHON_VERSION}+ is required. Found ${version}"
        return 1
    fi

    log_ok "Python ${version} meets minimum requirement (${MIN_PYTHON_VERSION}+)"
}

# ------------------------------------------------------------------------------
# System Dependencies Installation
# ------------------------------------------------------------------------------

install_python_system_deps() {
    log "Installing Python system dependencies..."

    local packages=(
        "python3-venv"
        "python3-pip"
        "python3-dev"
    )

    local missing=()
    for pkg in "${packages[@]}"; do
        if ! dpkg -l "${pkg}" &>/dev/null; then
            missing+=("${pkg}")
        fi
    done

    if [[ ${#missing[@]} -eq 0 ]]; then
        log_ok "All Python system dependencies already installed"
        return 0
    fi

    log "Installing: ${missing[*]}"
    run_sudo apt update
    run_sudo apt install -y "${missing[@]}"
    log_ok "Python system dependencies installed successfully"
}

# ------------------------------------------------------------------------------
# Virtual Environment Creation
# ------------------------------------------------------------------------------

create_venv() {
    local project_dir="${1:-.}"
    local venv_path="${project_dir}/${VENV_DIR}"

    log "Creating Python virtual environment..."
    log "  Project directory: ${project_dir}"
    log "  Venv path: ${venv_path}"

    if [[ -d "${venv_path}" ]]; then
        if [[ -f "${venv_path}/bin/activate" ]]; then
            log_warn "Virtual environment already exists at ${venv_path}"
            if confirm "Recreate virtual environment?" "n"; then
                log "Removing existing virtual environment..."
                rm -rf "${venv_path}"
            else
                log_ok "Using existing virtual environment"
                return 0
            fi
        else
            log_warn "Directory exists but is not a valid venv, removing..."
            rm -rf "${venv_path}"
        fi
    fi

    python3 -m venv "${venv_path}"

    if [[ ! -f "${venv_path}/bin/activate" ]]; then
        log_err "Failed to create virtual environment"
        return 1
    fi

    log_ok "Virtual environment created at ${venv_path}"

    log "Upgrading pip..."
    "${venv_path}/bin/pip" install --upgrade pip --quiet
    log_ok "Pip upgraded successfully"
}

# ------------------------------------------------------------------------------
# Requirements Installation
# ------------------------------------------------------------------------------

install_requirements() {
    local project_dir="${1:-.}"
    local venv_path="${project_dir}/${VENV_DIR}"
    local requirements_path="${project_dir}/${REQUIREMENTS_FILE}"
    local pip_cmd="${venv_path}/bin/pip"

    log "Installing Python dependencies..."

    if [[ ! -f "${requirements_path}" ]]; then
        log_err "Requirements file not found: ${requirements_path}"
        return 1
    fi

    if [[ ! -f "${pip_cmd}" ]]; then
        log_err "Virtual environment not found. Run create_venv first."
        return 1
    fi

    log "  Requirements: ${requirements_path}"

    "${pip_cmd}" install -r "${requirements_path}"

    log_ok "Python dependencies installed successfully"
}

# ------------------------------------------------------------------------------
# Installation Verification
# ------------------------------------------------------------------------------

verify_installation() {
    local project_dir="${1:-.}"
    local venv_path="${project_dir}/${VENV_DIR}"
    local python_cmd="${venv_path}/bin/python"
    local failed=()

    log "Verifying Python package installation..."

    if [[ ! -f "${python_cmd}" ]]; then
        log_err "Virtual environment not found. Run create_venv first."
        return 1
    fi

    for pkg in "${KEY_PACKAGES[@]}"; do
        if "${python_cmd}" -c "import ${pkg}" 2>/dev/null; then
            local version
            version=$("${python_cmd}" -c "import ${pkg}; print(${pkg}.__version__)" 2>/dev/null || echo "installed")
            log "  ${pkg}: ${version}"
        else
            failed+=("${pkg}")
        fi
    done

    if [[ ${#failed[@]} -gt 0 ]]; then
        log_err "Failed to import packages: ${failed[*]}"
        return 1
    fi

    log_ok "All key packages verified successfully"
}

# ------------------------------------------------------------------------------
# Main Setup Function
# ------------------------------------------------------------------------------

setup_python() {
    local project_dir="${1:-.}"

    echo -e "${HEADER_ICON} ${CYAN}Python Environment Setup for uSipipo${NC}"
    echo -e "${GRAY}${SEPARATOR}${NC}"
    echo ""

    verify_python_version
    echo ""

    install_python_system_deps
    echo ""

    create_venv "${project_dir}"
    echo ""

    install_requirements "${project_dir}"
    echo ""

    verify_installation "${project_dir}"
    echo ""

    echo -e "${GRAY}${SEPARATOR}${NC}"
    log_ok "Python environment setup complete!"
    echo ""
    echo -e "${YELLOW}Virtual environment:${NC} ${project_dir}/${VENV_DIR}"
    echo -e "${YELLOW}Activate with:${NC} source ${project_dir}/${VENV_DIR}/bin/activate"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Activate venv: source venv/bin/activate"
    echo "  2. Run tests: pytest"
    echo "  3. Start bot: python main.py"
}

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    setup_python "${PROJECT_DIR}"
fi
