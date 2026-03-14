#!/bin/bash
# Script para instalar y configurar Caddy con HTTPS automático
# Ejecutar con: sudo ./scripts/install-caddy.sh

set -e

echo "🚀 Instalando Caddy para HTTPS automático..."

# 1. Instalar Caddy
echo ""
echo "📦 Instalando Caddy..."
apt update
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl

# Agregar repositorio de Caddy
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list

apt update
apt install -y caddy

echo "✅ Caddy instalado"

# 2. Crear Caddyfile
echo ""
echo "📝 Configurando Caddyfile..."
mkdir -p /var/log/caddy
chown caddy:caddy /var/log/caddy

cat > /etc/caddy/Caddyfile << 'EOF'
usipipo.duckdns.org {
    reverse_proxy localhost:8000
    encode gzip zstd

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    log {
        output file /var/log/caddy/usipipo.log
        format json
    }
}
EOF

echo "✅ Caddyfile creado"

# 3. Iniciar Caddy
echo ""
echo "🚀 Iniciando Caddy..."
systemctl enable caddy
systemctl restart caddy

echo ""
echo "✅ Configuración completada!"
echo ""
echo "Verificar:"
echo "  curl https://usipipo.duckdns.org/health"
