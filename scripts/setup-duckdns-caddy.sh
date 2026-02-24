#!/bin/bash
# Setup script para DuckDNS + Caddy
# Uso: ./scripts/setup-duckdns-caddy.sh

set -e

echo "🦆 Configurando DuckDNS + Caddy para uSipipo VPN Bot"

# Variables (sobrescribir con variables de entorno o .env)
DUCKDNS_DOMAIN="${DUCKDNS_DOMAIN:-usipipo}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"

# Verificar token
if [ -z "$DUCKDNS_TOKEN" ]; then
    echo "❌ Error: DUCKDNS_TOKEN no esta configurado"
    echo "   Exporta la variable: export DUCKDNS_TOKEN=tu_token"
    exit 1
fi

# 1. Instalar Caddy
echo ""
echo "📦 Instalando Caddy..."
if ! command -v caddy &> /dev/null; then
    sudo apt update
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt update
    sudo apt install -y caddy
    echo "✅ Caddy instalado"
else
    echo "✅ Caddy ya esta instalado"
fi

# 2. Configurar DuckDNS
echo ""
echo "🦆 Configurando DuckDNS..."
mkdir -p ~/duckdns

cat > ~/duckdns/duck.sh << EOF
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=" | curl -k -o ~/duckdns/duck.log -K -
EOF

chmod 700 ~/duckdns/duck.sh

# Probar actualizacion
~/duckdns/duck.sh
if grep -q "OK" ~/duckdns/duck.log 2>/dev/null; then
    echo "✅ DuckDNS configurado correctamente"
else
    echo "⚠️ DuckDNS puede tener problemas. Revisa: cat ~/duckdns/duck.log"
fi

# 3. Configurar cron
echo ""
echo "⏰ Configurando cron job..."
(crontab -l 2>/dev/null | grep -v "duckdns/duck.sh"; echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1") | crontab -
echo "✅ Cron configurado (actualizacion cada 5 minutos)"

# 4. Copiar Caddyfile
echo ""
echo "📝 Configurando Caddy..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$PROJECT_DIR/config/Caddyfile" ]; then
    # Crear Caddyfile con el dominio correcto
    sed "s/usipipo\.duckdns\.org/${DUCKDNS_DOMAIN}.duckdns.org/g" "$PROJECT_DIR/config/Caddyfile" | sudo tee /etc/caddy/Caddyfile > /dev/null
    echo "✅ Caddyfile copiado a /etc/caddy/Caddyfile"
else
    echo "❌ No se encontro config/Caddyfile"
    exit 1
fi

# 5. Crear directorio de logs
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# 6. Habilitar e iniciar Caddy
echo ""
echo "🚀 Iniciando Caddy..."
sudo systemctl enable caddy
sudo systemctl restart caddy

echo ""
echo "✅ Configuracion completada!"
echo ""
echo "URLs:"
echo "  - Mini App:    https://${DUCKDNS_DOMAIN}.duckdns.org/miniapp/"
echo "  - Webhook:     https://${DUCKDNS_DOMAIN}.duckdns.org/api/v1/webhooks/tron-dealer"
echo "  - API:         https://${DUCKDNS_DOMAIN}.duckdns.org/api/"
echo ""
echo "Proximos pasos:"
echo "  1. Configura estas variables en tu .env:"
echo "     DUCKDNS_DOMAIN=${DUCKDNS_DOMAIN}"
echo "     DUCKDNS_TOKEN=tu_token"
echo "     PUBLIC_URL=https://${DUCKDNS_DOMAIN}.duckdns.org"
echo "  2. Actualiza la URL en BotFather para la Mini App"
echo "  3. Reinicia el bot: sudo systemctl restart usipipo"
