#!/bin/bash
# =============================================================================
# vpn.sh - VPN installation and configuration module
# =============================================================================
# Source: scripts/install.sh (adapted for modular architecture)
# Description: Install and manage Outline and WireGuard VPN servers
# =============================================================================

set -Eeuo pipefail

# Source common functions
MODULES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${MODULES_DIR}/common.sh"

# =============================================================================
# Paths & Files (VPN-specific)
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
OL_SCRIPT="$SCRIPT_DIR/ol_server.sh"
WG_SCRIPT="$SCRIPT_DIR/wg_server.sh"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/vpn_$(date +%Y%m%d_%H%M%S).log"

# =============================================================================
# DNS helpers
# =============================================================================
fix_dns() {
    local NS1="1.1.1.1"
    local NS2="8.8.8.8"

    if command -v resolvconf &>/dev/null; then
        log "Ensuring resolvconf head contains fallback nameservers..."
        run_sudo mkdir -p /etc/resolvconf/resolv.conf.d
        if ! run_sudo grep -qE '^\s*nameserver' /etc/resolvconf/resolv.conf.d/head 2>/dev/null; then
            run_sudo tee /etc/resolvconf/resolv.conf.d/head >/dev/null <<EOF
# uSipipo fallback nameservers (added by vpn.sh)
nameserver ${NS1}
nameserver ${NS2}
EOF
            log_ok "Wrote /etc/resolvconf/resolv.conf.d/head"
        else
            log "resolvconf head already contains nameserver(s); leaving intact."
        fi

        log "Updating resolvconf..."
        run_sudo resolvconf -u || {
            log_warn "resolvconf -u failed or not supported; falling back to writing /etc/resolv.conf directly."
        }
    else
        if ! grep -qE '^\s*nameserver' /etc/resolv.conf 2>/dev/null; then
            log_warn "/etc/resolv.conf has no nameserver entries — writing fallback nameservers."
            run_sudo tee /etc/resolv.conf >/dev/null <<EOF
# uSipipo fallback resolv.conf
nameserver ${NS1}
nameserver ${NS2}
EOF
            log_ok "Wrote /etc/resolv.conf with fallback nameservers"
        else
            log "Existing /etc/resolv.conf contains nameserver(s); leaving intact."
        fi
    fi
}

check_dns() {
    if ! ping -c1 -W2 1.1.1.1 &>/dev/null; then
        log_err "Network connectivity to 1.1.1.1 failed. Check upstream network before proceeding."
        return 1
    fi

    if ! grep -qE '^\s*nameserver' /etc/resolv.conf 2>/dev/null; then
        log_warn "/etc/resolv.conf has no nameserver. Attempting to fix DNS."
        fix_dns
    fi

    if getent hosts google.com >/dev/null 2>&1; then
        log_ok "DNS resolution OK (getent)."
        return 0
    fi

    if command -v nslookup &>/dev/null; then
        if nslookup google.com 1.1.1.1 >/dev/null 2>&1; then
            log_ok "DNS resolution OK (nslookup to 1.1.1.1)."
            return 0
        fi
    fi

    if curl -s --head --max-time 3 https://www.google.com >/dev/null 2>&1; then
        log_ok "DNS resolution and HTTP connectivity OK."
        return 0
    fi

    log_warn "DNS resolution still failing after attempts. Forcing fallback resolv.conf and rechecking."
    fix_dns
    sleep 1
    if getent hosts google.com >/dev/null 2>&1 || curl -s --head --max-time 3 https://www.google.com >/dev/null 2>&1; then
        log_ok "DNS fixed using fallback."
        return 0
    fi

    log_err "DNS resolution could not be established. Aborting installation."
    return 1
}

get_random_port() {
    shuf -i 20000-55000 -n 1
}

# =============================================================================
# Docker installer
# =============================================================================
install_docker_wrapper() {
    if command -v docker &> /dev/null; then
        log_ok "Docker already installed."
        return 0
    fi

    log "Installing Docker using get.docker.com..."
    run_sudo bash -c "curl -fsSL https://get.docker.com | sh" | tee -a "$LOG_FILE"
    run_sudo systemctl enable --now docker || true
    if command -v docker &> /dev/null; then
        log_ok "Docker installed successfully."
    else
        log_err "Docker installation failed. Please install docker manually."
        return 1
    fi
}

# =============================================================================
# Outline: installer wrapper
# =============================================================================
install_outline() {
    if [ ! -f "$OL_SCRIPT" ]; then
        log_err "Outline installer script not found at: $OL_SCRIPT"
        return 1
    fi

    log "🚀 INSTALL OUTLINE (official wrapper)"

    if ! command -v docker &> /dev/null; then
        log_warn "Docker not found. Installing..."
        install_docker_wrapper || { log_err "Docker is required for Outline. Aborting."; return 1; }
    fi

    check_dns || { log_err "DNS check failed. Fix DNS and retry Outline installation."; return 1; }

    local server_ip
    server_ip=$(get_public_ip)
    if [[ -z "$server_ip" ]]; then
        log_warn "Could not auto-detect public IP via metadata/external services. Falling back to primary interface address."
        local iface
        iface=$(ip route 2>/dev/null | awk '/default/ {print $5; exit}' || true)
        iface=${iface:-eth0}
        server_ip=$(ip -4 addr show dev "$iface" 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1 || true)
    fi
    log "Detected public IP: ${server_ip:-<none>}"

    local api_port keys_port
    api_port=$(get_random_port)
    keys_port=$(get_random_port)
    while [ "$keys_port" = "$api_port" ]; do keys_port=$(get_random_port); done

    if [[ "$api_port" -lt 1024 || "$api_port" -gt 65535 || "$keys_port" -lt 1024 || "$keys_port" -gt 65535 ]]; then
        log_err "Generated ports out of valid range. Aborting."
        return 1
    fi

    echo ""
    echo "Outline installation will run with:"
    echo "  Hostname / IP: ${server_ip:-<none>}"
    echo "  API port: $api_port"
    echo "  Keys port: $keys_port"
    echo ""
    if ! confirm "Proceed to run official Outline installer now (interactive prompts may appear)?"; then
        log_warn "User cancelled Outline install."
        return 1
    fi

    log "Running Outline installer script..."
    run_sudo bash "$OL_SCRIPT" --hostname "${server_ip:-}" --api-port "$api_port" --keys-port "$keys_port" 2>&1 | tee -a "$LOG_FILE"

    log_ok "Outline installer finished. Attempting to extract API info..."

    local access_file="/opt/outline/access.txt"
    if [ ! -f "$access_file" ]; then
        log_warn "Outline access file not found at ${access_file}. Searching persisted-state..."
        if run_sudo test -f /opt/outline/persisted-state/access.txt; then
            access_file="/opt/outline/persisted-state/access.txt"
        fi
    fi

    if [ -f "$access_file" ]; then
        log "Found Outline access file at: $access_file"
        local apiUrl certSha
        apiUrl=$(run_sudo awk -F'apiUrl:' '/apiUrl/{print substr($0, index($0,$2))}' "$access_file" | tr -d '\r' | sed -n '1p' || true)
        certSha=$(run_sudo awk -F'certSha256:' '/certSha256/{print substr($0, index($0,$2))}' "$access_file" | tr -d '\r' | sed -n '1p' || true)
        
        if [ -z "$apiUrl" ]; then
            apiUrl=$(run_sudo grep -E "^apiUrl:" "$access_file" 2>/dev/null | sed 's/^apiUrl://' | tr -d '[:space:]' || true)
        fi
        if [ -z "$certSha" ]; then
            certSha=$(run_sudo grep -E "^certSha256:" "$access_file" 2>/dev/null | sed 's/^certSha256://' | tr -d '[:space:]' || true)
        fi

        local outline_server_ip outline_dashboard
        outline_server_ip="${server_ip:-}"
        outline_dashboard="${apiUrl:-}"

        if [ -n "$apiUrl" ]; then
            env_set "OUTLINE_API_URL" "$apiUrl" "$ENV_FILE"
            log_ok "OUTLINE_API_URL saved"
        else
            log_warn "Could not extract OUTLINE_API_URL from ${access_file}"
        fi
        if [ -n "$certSha" ]; then
            env_set "OUTLINE_CERT_SHA256" "$certSha" "$ENV_FILE"
            log_ok "OUTLINE_CERT_SHA256 saved"
        else
            log_warn "Could not extract OUTLINE_CERT_SHA256 from ${access_file}"
        fi

        env_set "OUTLINE_API_PORT" "$api_port" "$ENV_FILE"
        env_set "OUTLINE_KEYS_PORT" "$keys_port" "$ENV_FILE"
        env_set "OUTLINE_SERVER_IP" "$outline_server_ip" "$ENV_FILE"
        env_set "OUTLINE_DASHBOARD_URL" "$outline_dashboard" "$ENV_FILE"

        log_ok "Outline variables exported to ${ENV_FILE}"
    else
        log_err "Outline access file not found; manual extraction may be required."
        return 1
    fi
}

# =============================================================================
# WireGuard: installer wrapper
# =============================================================================
install_wireguard() {
    if [ ! -f "$WG_SCRIPT" ]; then
        log_err "WireGuard installer script not found at: $WG_SCRIPT"
        return 1
    fi

    log "🚀 INSTALL WIREGUARD (official wrapper)"

    echo ""
    log "The WireGuard installer is interactive. It will ask a few questions (interface, IPs, port)."

    if ! confirm "Proceed to run official WireGuard installer now?"; then
        log_warn "User cancelled WireGuard install."
        return 1
    fi

    fix_dns
    check_dns || { log_err "DNS check failed. Fix DNS and retry WireGuard installation."; return 1; }

    run_sudo bash "$WG_SCRIPT" 2>&1 | tee -a "$LOG_FILE"

    local params_file="/etc/wireguard/params"
    if run_sudo test -f "$params_file"; then
        log_ok "WireGuard params found: $params_file"
        install_wireguard_extract_only
    else
        log_err "WireGuard params file not found at /etc/wireguard/params. Installation may have failed."
        return 1
    fi
}

install_wireguard_extract_only() {
    local params_file="/etc/wireguard/params"
    if ! run_sudo test -f "$params_file"; then
        return 1
    fi
    
    local WG_SERVER_WG_NIC WG_SERVER_WG_IPV4 WG_SERVER_WG_IPV6 WG_SERVER_PORT WG_SERVER_PRIV_KEY WG_SERVER_PUB_KEY CLIENT_DNS_1 CLIENT_DNS_2 ALLOWED_IPS
    WG_SERVER_WG_NIC=$(run_sudo grep '^SERVER_WG_NIC=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    WG_SERVER_WG_IPV4=$(run_sudo grep '^SERVER_WG_IPV4=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    WG_SERVER_WG_IPV6=$(run_sudo grep '^SERVER_WG_IPV6=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    WG_SERVER_PORT=$(run_sudo grep '^SERVER_PORT=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    WG_SERVER_PRIV_KEY=$(run_sudo grep '^SERVER_PRIV_KEY=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    WG_SERVER_PUB_KEY=$(run_sudo grep '^SERVER_PUB_KEY=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    CLIENT_DNS_1=$(run_sudo grep '^CLIENT_DNS_1=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    CLIENT_DNS_2=$(run_sudo grep '^CLIENT_DNS_2=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    ALLOWED_IPS=$(run_sudo grep '^ALLOWED_IPS=' "$params_file" | cut -d= -f2- | tr -d '"' || true)
    
    if [[ -n "$WG_SERVER_PUB_KEY" && ${#WG_SERVER_PUB_KEY} -lt 44 ]]; then
        log_warn "Clave pública extraída parece truncada (${#WG_SERVER_PUB_KEY} chars). Intentando obtener del sistema..."
        WG_SERVER_PUB_KEY=$(run_sudo wg show "$WG_SERVER_WG_NIC" public-key 2>/dev/null || true)
        if [[ -z "$WG_SERVER_PUB_KEY" ]]; then
            log_err "No se pudo obtener la clave pública del sistema."
        else
            log_ok "Clave pública obtenida del sistema: ${WG_SERVER_PUB_KEY:0:10}..."
        fi
    fi

    [ -n "$WG_SERVER_WG_NIC" ] && env_set "WG_INTERFACE" "$WG_SERVER_WG_NIC" "$ENV_FILE"
    [ -n "$WG_SERVER_WG_IPV4" ] && env_set "WG_SERVER_IPV4" "$WG_SERVER_WG_IPV4" "$ENV_FILE"
    [ -n "$WG_SERVER_WG_IPV6" ] && env_set "WG_SERVER_IPV6" "$WG_SERVER_WG_IPV6" "$ENV_FILE"
    [ -n "$WG_SERVER_PORT" ] && env_set "WG_SERVER_PORT" "$WG_SERVER_PORT" "$ENV_FILE"
    [ -n "$WG_SERVER_PUB_KEY" ] && env_set "WG_SERVER_PUBKEY" "$WG_SERVER_PUB_KEY" "$ENV_FILE"
    [ -n "$WG_SERVER_PRIV_KEY" ] && env_set "WG_SERVER_PRIVKEY" "$WG_SERVER_PRIV_KEY" "$ENV_FILE"
    [ -n "$ALLOWED_IPS" ] && env_set "WG_ALLOWED_IPS" "$ALLOWED_IPS" "$ENV_FILE"
    [ -n "$CLIENT_DNS_1" ] && env_set "WG_CLIENT_DNS_1" "$CLIENT_DNS_1" "$ENV_FILE"
    [ -n "$CLIENT_DNS_2" ] && env_set "WG_CLIENT_DNS_2" "$CLIENT_DNS_2" "$ENV_FILE"

    local server_ip
    server_ip=$(get_public_ip)
    if [[ -z "$server_ip" ]]; then
        local iface
        iface=$(ip route 2>/dev/null | awk '/default/ {print $5; exit}' || true)
        iface=${iface:-eth0}
        server_ip=$(ip -4 addr show dev "$iface" 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1 || true)
    fi
    if [[ -n "$server_ip" ]]; then
        env_set "SERVER_IP" "$server_ip" "$ENV_FILE"
        if [ -n "$WG_SERVER_PORT" ]; then
            env_set "WG_ENDPOINT" "${server_ip}:${WG_SERVER_PORT}" "$ENV_FILE"
        fi
    else
        log_warn "Could not determine public IP during extraction."
    fi

    log_ok "WireGuard variables exported to ${ENV_FILE}"
    return 0
}

# =============================================================================
# Extract VPN vars from existing installs
# =============================================================================
extract_vpn_vars() {
    log "Extracting variables from existing installations..."

    local access_file="/opt/outline/access.txt"
    if run_sudo test -f "$access_file"; then
        log "Reading Outline access file..."
        local apiUrl certSha
        apiUrl=$(run_sudo grep -E "^apiUrl:" "$access_file" 2>/dev/null | sed 's/^apiUrl://' | tr -d '[:space:]' || true)
        certSha=$(run_sudo grep -E "^certSha256:" "$access_file" 2>/dev/null | sed 's/^certSha256://' | tr -d '[:space:]' || true)

        [ -n "$apiUrl" ] && env_set "OUTLINE_API_URL" "$apiUrl" "$ENV_FILE"
        [ -n "$certSha" ] && env_set "OUTLINE_CERT_SHA256" "$certSha" "$ENV_FILE"

        if run_sudo test -f /opt/outline/persisted-state/shadowbox_server_config.json; then
            local cfg="/opt/outline/persisted-state/shadowbox_server_config.json"
            local hostname portForNewAccessKeys
            hostname=$(run_sudo jq -r '.hostname' "$cfg" 2>/dev/null || true)
            portForNewAccessKeys=$(run_sudo jq -r '.portForNewAccessKeys' "$cfg" 2>/dev/null || true)
            [ -n "$hostname" ] && env_set "OUTLINE_SERVER_IP" "$hostname" "$ENV_FILE"
            [ -n "$portForNewAccessKeys" ] && env_set "OUTLINE_KEYS_PORT" "$portForNewAccessKeys" "$ENV_FILE"
        fi
    else
        log_warn "Outline access file not found at ${access_file}"
    fi

    local params_file="/etc/wireguard/params"
    if run_sudo test -f "$params_file"; then
        log "Reading WireGuard params..."
        install_wireguard_extract_only
    else
        log_warn "WireGuard params file not found at ${params_file}"
    fi

    log_ok "Extraction completed."
}

# =============================================================================
# Status & logs helpers
# =============================================================================
vpn_status() {
    log "📊 VPN STATUS"
    if command -v docker &> /dev/null; then
        if docker ps --format '{{.Names}}' | grep -qw shadowbox; then
            docker ps --filter name=shadowbox --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        else
            log_warn "Outline (shadowbox) container not running or not present."
        fi
    else
        log_warn "Docker not installed, cannot show Outline status."
    fi

    if systemctl list-units --type=service --all | grep -q 'wg-quick@'; then
        systemctl status --no-pager 'wg-quick@*' || true
    else
        if run_sudo systemctl is-active --quiet "wg-quick@wg0" 2>/dev/null; then
            systemctl status --no-pager wg-quick@wg0 || true
        else
            log_warn "WireGuard service (wg-quick@...) not active or not installed via systemd."
        fi
    fi
}

vpn_logs() {
    echo ""
    echo "Select logs to view:"
    echo "  1) Outline container logs (shadowbox)"
    echo "  2) Watchtower logs"
    echo "  3) WireGuard syslogs / systemctl (wg-quick)"
    echo "  4) Tail VPN logs"
    read -r -p "Choice [1-4]: " ch
    case "$ch" in
        1)
            if docker ps --format '{{.Names}}' | grep -qw shadowbox; then
                docker logs --tail 200 shadowbox
            else
                log_warn "shadowbox container not found."
            fi
            ;;
        2)
            if docker ps --format '{{.Names}}' | grep -qw watchtower; then
                docker logs --tail 200 watchtower
            else
                log_warn "watchtower container not found."
            fi
            ;;
        3)
            journalctl -u "wg-quick@*" --no-pager -n 200 || journalctl -t wg-quick --no-pager -n 200 || log_warn "No wg logs found"
            ;;
        4)
            tail -n 200 "$LOG_FILE"
            ;;
        *)
            log_warn "Invalid choice"
            ;;
    esac
}

# =============================================================================
# Uninstall helpers
# =============================================================================
uninstall_outline() {
    log "Removing Outline containers & persisted state (best-effort)."
    if docker ps --format '{{.Names}}' | grep -qw shadowbox; then
        run_sudo docker rm -f shadowbox || true
    fi
    if docker ps --format '{{.Names}}' | grep -qw watchtower; then
        run_sudo docker rm -f watchtower || true
    fi
    run_sudo rm -rf /opt/outline || true
    log_ok "Outline removed (files at /opt/outline deleted)."
}

uninstall_wireguard() {
    log "Attempting to uninstall WireGuard (best-effort)."
    if run_sudo test -f "$WG_SCRIPT"; then
        log "If your wg installer provides an uninstall option, run it manually."
    fi
    run_sudo rm -rf /etc/wireguard || true
    run_sudo rm -f /etc/sysctl.d/wg.conf || true
    log_ok "WireGuard files removed from /etc/wireguard (manual cleanup may still be required)."
}

# =============================================================================
# Bot permissions for WireGuard
# =============================================================================
configure_bot_permissions() {
    log "🛡️ Configurando permisos de WireGuard para el bot" 
    
    local BOT_USER=${SUDO_USER:-$(whoami)}
    local WG_PATH="/etc/wireguard" 
    local WG_CONF="${WG_PATH}/wg0.conf" 

    log "Usuario del bot identificado: ${BOT_USER}"
    
    if [ "${BOT_USER}" = "root" ]; then
        log_warn "El bot se está ejecutando como 'root'. NO se modificará el sudoers."
    else
        log "Añadiendo reglas NOPASSWD para ${BOT_USER} en sudoers..."

        local SUDOERS_FILE="/etc/sudoers.d/usipipo_wg_bot"

        run_sudo tee "$SUDOERS_FILE" > /dev/null <<EOF
# Permisos de WireGuard para el bot ${BOT_USER}
${BOT_USER} ALL=(root) NOPASSWD: /usr/bin/mkdir -p /etc/wireguard/clients
${BOT_USER} ALL=(root) NOPASSWD: /usr/bin/chown -R * /etc/wireguard/clients
${BOT_USER} ALL=(root) NOPASSWD: /usr/bin/wg set *
${BOT_USER} ALL=(root) NOPASSWD: /usr/bin/wg show *
EOF
        run_sudo chmod 0440 "$SUDOERS_FILE"
        log_ok "Reglas de NOPASSWD añadidas a ${SUDOERS_FILE}." 
    fi

    log "Asegurando el directorio de clientes: ${WG_PATH}/clients"
    run_sudo mkdir -p "${WG_PATH}/clients"
    run_sudo chown -R "${BOT_USER}:${BOT_USER}" "${WG_PATH}/clients"
    log_ok "Propiedad del directorio clients ajustada." 
    
    if [ -f "${WG_CONF}" ]; then
        log "Asegurando permisos para el archivo de configuración principal: ${WG_CONF}"
        run_sudo chown "${BOT_USER}:${BOT_USER}" "${WG_CONF}"
        run_sudo chmod 600 "${WG_CONF}"
        log_ok "Permisos de ${WG_CONF} ajustados." 
    else
        log_warn "Archivo ${WG_CONF} no encontrado. Asumiendo que se creará luego."
    fi

    log_ok "Permisos y directorios de WireGuard configurados correctamente."
}

# =============================================================================
# Fix WireGuard MTU
# =============================================================================
fix_wireguard_mtu() {
    log "🔧 Aplicando MTU=1420 a configuración de WireGuard..."
    
    local wg_conf="/etc/wireguard/wg0.conf"
    
    if run_sudo test -f "$wg_conf"; then
        if ! run_sudo grep -q "^MTU" "$wg_conf"; then
            log "Añadiendo MTU=1420 a ${wg_conf}..."
            run_sudo sed -i '/^PrivateKey/a MTU = 1420' "$wg_conf"
            
            log_ok "MTU añadido. Reiniciando WireGuard..."
            run_sudo wg-quick down wg0 2>/dev/null || true
            run_sudo wg-quick up wg0
            
            log_ok "WireGuard reiniciado con MTU correcto"
        else
            log_ok "MTU ya está configurado en ${wg_conf}"
        fi
    else
        log_warn "Archivo ${wg_conf} no encontrado. Saltando corrección de MTU."
    fi
}

# =============================================================================
# Main entry point if run directly
# =============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "VPN Module - Use via setup.sh or source this file"
    echo "Available functions: install_docker_wrapper, install_outline, install_wireguard, etc."
fi
