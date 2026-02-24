# DuckDNS + Caddy Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from ngrok to DuckDNS + Caddy for fixed domain with automatic HTTPS

**Architecture:** Replace ngrok tunnel service with DuckDNS dynamic DNS and Caddy reverse proxy. DuckDNS provides fixed domain (usipipo.duckdns.org), Caddy handles HTTPS via Let's Encrypt.

**Tech Stack:** DuckDNS API, Caddy, Python asyncio, systemd/cron

---

## Task 1: Eliminar servicio ngrok

**Files:**
- Delete: `infrastructure/tunnel/ngrok_service.py`
- Delete: `infrastructure/tunnel/__init__.py`

**Step 1: Eliminar archivos de ngrok**

```bash
rm -rf infrastructure/tunnel/
```

**Step 2: Verificar eliminación**

```bash
ls infrastructure/tunnel/ 2>/dev/null || echo "Directorio eliminado correctamente"
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove ngrok tunnel service"
```

---

## Task 2: Actualizar requirements.txt

**Files:**
- Modify: `requirements.txt`

**Step 1: Eliminar pyngrok**

Editar `requirements.txt` y eliminar la línea:
```
pyngrok==7.2.3
```

**Step 2: Verificar**

```bash
grep -n "pyngrok" requirements.txt || echo "pyngrok eliminado correctamente"
```

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: remove pyngrok dependency"
```

---

## Task 3: Actualizar config.py

**Files:**
- Modify: `config.py`

**Step 1: Eliminar configuración de ngrok**

Eliminar las siguientes líneas (aproximadamente líneas 305-314):
```python
    # NGROK TUNNEL

    NGROK_AUTH_TOKEN: Optional[str] = Field(
        default=None,
        description="Auth token de ngrok (from ngrok.com)"
    )

    NGROK_SUBDOMAIN: Optional[str] = Field(
        default=None,
        description="Subdominio personalizado de ngrok"
    )
```

**Step 2: Agregar configuración de DuckDNS**

Agregar después de las configuraciones de API:
```python
    # DYNAMIC DNS (DuckDNS)
    
    DUCKDNS_DOMAIN: Optional[str] = Field(
        default=None,
        description="Dominio de DuckDNS (sin .duckdns.org)"
    )
    
    DUCKDNS_TOKEN: Optional[str] = Field(
        default=None,
        description="Token de autenticacion de DuckDNS"
    )
    
    PUBLIC_URL: Optional[str] = Field(
        default=None,
        description="URL publica del servidor (https://dominio.duckdns.org)"
    )
    
    @property
    def webhook_url(self) -> str:
        """URL del webhook de Tron Dealer."""
        if self.PUBLIC_URL:
            return f"{self.PUBLIC_URL}/api/v1/webhooks/tron-dealer"
        return f"http://localhost:{self.API_PORT}/api/v1/webhooks/tron-dealer"
```

**Step 3: Actualizar campos obligatorios**

En el método `model_config` o donde se listen campos sensibles, actualizar para incluir nuevos campos:
```python
            "DUCKDNS_TOKEN",
```

Y eliminar `NGROK_AUTH_TOKEN` si estaba listado.

**Step 4: Commit**

```bash
git add config.py
git commit -m "refactor: replace ngrok config with DuckDNS config"
```

---

## Task 4: Crear servicio DuckDNS

**Files:**
- Create: `infrastructure/dns/__init__.py`
- Create: `infrastructure/dns/duckdns_service.py`

**Step 1: Crear directorio**

```bash
mkdir -p infrastructure/dns
```

**Step 2: Crear __init__.py**

```python
from infrastructure.dns.duckdns_service import DuckDNSService

__all__ = ["DuckDNSService"]
```

**Step 3: Crear duckdns_service.py**

```python
import asyncio
import logging
from typing import Optional

import aiohttp

from utils.logger import logger


class DuckDNSService:
    DUCKDNS_UPDATE_URL = "https://www.duckdns.org/update"

    def __init__(self, domain: str, token: str) -> None:
        self.domain = domain
        self.token = token
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def update_ip(self) -> bool:
        session = await self._get_session()
        params = {
            "domains": self.domain,
            "token": self.token,
            "ip": ""
        }
        try:
            async with session.get(self.DUCKDNS_UPDATE_URL, params=params) as response:
                result = await response.text()
                if result == "OK":
                    logger.info(f"✅ DuckDNS IP actualizada: {self.domain}.duckdns.org")
                    return True
                else:
                    logger.error(f"❌ DuckDNS error: {result}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error actualizando DuckDNS: {e}")
            return False

    def get_public_url(self) -> str:
        return f"https://{self.domain}.duckdns.org"

    @staticmethod
    def get_cron_script_content(domain: str, token: str) -> str:
        return f'''#!/bin/bash
echo url="https://www.duckdns.org/update?domains={domain}&token={token}&ip=" | curl -k -o ~/duckdns/duck.log -K -
'''

    @staticmethod
    def setup_instructions(domain: str, token: str) -> str:
        return f"""
Instrucciones para configurar DuckDNS:

1. Crear directorio:
   mkdir -p ~/duckdns

2. Crear script de actualizacion:
   cat > ~/duckdns/duck.sh << 'SCRIPT'
{DuckDNSService.get_cron_script_content(domain, token)}SCRIPT

3. Hacer ejecutable:
   chmod 700 ~/duckdns/duck.sh

4. Configurar cron (cada 5 minutos):
   (crontab -l 2>/dev/null; echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1") | crontab -

5. Probar:
   ~/duckdns/duck.sh
   cat ~/duckdns/duck.log

Debe mostrar: OK
"""
```

**Step 4: Verificar sintaxis**

```bash
python -m py_compile infrastructure/dns/duckdns_service.py
```

**Step 5: Commit**

```bash
git add infrastructure/dns/
git commit -m "feat: add DuckDNS service for dynamic DNS updates"
```

---

## Task 5: Actualizar main.py

**Files:**
- Modify: `main.py`

**Step 1: Eliminar import de ngrok**

Eliminar si existe:
```python
from infrastructure.tunnel.ngrok_service import NgrokService
```

**Step 2: Eliminar bloque ngrok en post_init_callback**

Eliminar las líneas 81-93:
```python
        if settings.NGROK_AUTH_TOKEN:
            try:
                from infrastructure.tunnel.ngrok_service import NgrokService
                NgrokService.kill_all_tunnels()
                ngrok_service = NgrokService(
                    auth_token=settings.NGROK_AUTH_TOKEN,
                    subdomain=settings.NGROK_SUBDOMAIN
                )
                public_url = ngrok_service.start(settings.API_PORT, kill_existing=False)
                logger.info(f"🌐 Ngrok tunnel activo: {public_url}")
                logger.info(f"📡 Webhook URL: {public_url}/api/v1/webhooks/tron-dealer")
            except Exception as e:
                logger.warning(f"⚠️  No se pudo iniciar ngrok: {e}")
```

**Step 3: Agregar inicialización DuckDNS**

Agregar después del bloque de startup (después de `await startup()`):
```python
        if settings.DUCKDNS_DOMAIN and settings.DUCKDNS_TOKEN:
            try:
                from infrastructure.dns.duckdns_service import DuckDNSService
                duckdns = DuckDNSService(
                    domain=settings.DUCKDNS_DOMAIN,
                    token=settings.DUCKDNS_TOKEN
                )
                await duckdns.update_ip()
                logger.info(f"🌐 DuckDNS configurado: {duckdns.get_public_url()}")
                logger.info(f"📡 Webhook URL: {settings.webhook_url}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo actualizar DuckDNS: {e}")
```

**Step 4: Commit**

```bash
git add main.py
git commit -m "refactor: replace ngrok with DuckDNS in main startup"
```

---

## Task 6: Crear Caddyfile

**Files:**
- Create: `config/Caddyfile`

**Step 1: Crear directorio**

```bash
mkdir -p config
```

**Step 2: Crear Caddyfile**

```
# Caddyfile para uSipipo VPN Bot
# Reemplazar 'usipipo' con tu dominio DuckDNS

usipipo.duckdns.org {
    # Reverse proxy a la API FastAPI
    reverse_proxy localhost:8000
    
    # Compresion gzip
    encode gzip zstd
    
    # Headers de seguridad
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
    
    # Logs
    log {
        output file /var/log/caddy/usipipo.log
        format json
    }
}
```

**Step 3: Commit**

```bash
git add config/Caddyfile
git commit -m "feat: add Caddyfile for HTTPS reverse proxy"
```

---

## Task 7: Crear script de instalación

**Files:**
- Create: `scripts/setup-duckdns-caddy.sh`

**Step 1: Crear script**

```bash
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
```

**Step 2: Hacer ejecutable**

```bash
chmod +x scripts/setup-duckdns-caddy.sh
```

**Step 3: Commit**

```bash
git add scripts/setup-duckdns-caddy.sh
git commit -m "feat: add DuckDNS + Caddy setup script"
```

---

## Task 8: Actualizar example.env

**Files:**
- Modify: `example.env`

**Step 1: Eliminar configuración ngrok**

Eliminar:
```
# NGROK TUNNEL (Development Only)
# Auth token de ngrok (from ngrok.com)
NGROK_AUTH_TOKEN=tu_ngrok_auth_token
# Subdominio personalizado de ngrok (opcional)
NGROK_SUBDOMAIN=usipipo
```

**Step 2: Agregar configuración DuckDNS**

Agregar:
```
# DYNAMIC DNS (DuckDNS)
# Dominio de DuckDNS (sin .duckdns.org)
DUCKDNS_DOMAIN=usipipo
# Token de autenticacion de DuckDNS (obtener en duckdns.org)
DUCKDNS_TOKEN=tu_duckdns_token_aqui
# URL publica del servidor
PUBLIC_URL=https://usipipo.duckdns.org
```

**Step 3: Commit**

```bash
git add example.env
git commit -m "docs: update example.env with DuckDNS config"
```

---

## Task 9: Actualizar documentación

**Files:**
- Modify: `docs/tron_dealer_registration.md`

**Step 1: Actualizar referencias de ngrok**

Buscar y reemplazar todas las referencias de ngrok con DuckDNS:
- `NGROK_AUTH_TOKEN` -> `DUCKDNS_TOKEN`
- `NGROK_SUBDOMAIN` -> `DUCKDNS_DOMAIN`
- URLs de ngrok -> `https://usipipo.duckdns.org`

**Step 2: Commit**

```bash
git add docs/tron_dealer_registration.md
git commit -m "docs: update Tron Dealer docs with DuckDNS"
```

---

## Task 10: Verificar y ejecutar tests

**Step 1: Verificar imports**

```bash
python -c "from infrastructure.dns import DuckDNSService; print('OK')"
```

**Step 2: Verificar config**

```bash
python -c "from config import settings; print(f'webhook_url: {settings.webhook_url}')"
```

**Step 3: Ejecutar tests existentes**

```bash
pytest -v --tb=short
```

**Step 4: Verificar mypy**

```bash
mypy infrastructure/dns/ main.py config.py
```

---

## Task 11: Commit final y push

**Step 1: Verificar cambios**

```bash
git status
git log --oneline -10
```

**Step 2: Push a develop**

```bash
git push origin develop
```

---

## Resumen de commits

1. `refactor: remove ngrok tunnel service`
2. `chore: remove pyngrok dependency`
3. `refactor: replace ngrok config with DuckDNS config`
4. `feat: add DuckDNS service for dynamic DNS updates`
5. `refactor: replace ngrok with DuckDNS in main startup`
6. `feat: add Caddyfile for HTTPS reverse proxy`
7. `feat: add DuckDNS + Caddy setup script`
8. `docs: update example.env with DuckDNS config`
9. `docs: update Tron Dealer docs with DuckDNS`

## URLs finales

| Servicio | URL |
|----------|-----|
| Mini App | https://usipipo.duckdns.org/miniapp/ |
| Webhook Tron Dealer | https://usipipo.duckdns.org/api/v1/webhooks/tron-dealer |
| API | https://usipipo.duckdns.org/api/ |
