# Plan de Seguridad Reforzada: Ecosistema Unificado

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Contexto:** Single VPS con todos los servicios (Bot + Mini App + VPN + Backend + APK)
> **Objetivo:** Seguridad de grado militar sin sacrificar rendimiento

---

## 🎯 Filosofía de Seguridad

> **"Defense in Depth" + "Zero Trust" + "Minimal Surface"**

En un VPS único donde todo está concentrado, la seguridad debe ser:
1. **En capas:** Si una falla, la siguiente detiene el ataque
2. **Zero Trust:** Nunca confiar, siempre verificar
3. **Superficie mínima:** Exponer solo lo estrictamente necesario

---

## 🏰 Capa 1: Hardening del Sistema Operativo

### 1.1 Configuración de Firewall (UFW)

**Script: `/opt/usipipobot/scripts/setup_firewall.sh`**

```bash
#!/bin/bash
# Firewall ultra-restrictivo para VPS uSipipo

set -e

echo "🔥 Configurando firewall UFW..."

# Resetear UFW
ufw --force reset

# Política por defecto: DENEGAR TODO
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH (solo desde IPs específicas si es posible)
ufw allow 22/tcp comment "SSH - Administración"

# Permitir HTTP/HTTPS para Caddy (reverse proxy)
ufw allow 80/tcp comment "HTTP - Redirección a HTTPS"
ufw allow 443/tcp comment "HTTPS - Tráfico seguro"

# Permitir WireGuard (UDP)
ufw allow 51820/udp comment "WireGuard VPN"

# Permitir Outline (Shadowsocks - TCP/UDP)
ufw allow 443/tcp comment "Outline VPN (Shadowsocks)"
ufw allow 443/udp comment "Outline VPN (UDP)"

# DENEGAR todo lo demás explícitamente
# Los puertos de PostgreSQL (5432), Redis (6379), y backend (8000)
# SOLO escuchan en localhost, no necesitan reglas de firewall

# Habilitar UFW
ufw --force enable

# Mostrar estado
ufw status verbose

echo "✅ Firewall configurado"
echo ""
echo "⚠️  IMPORTANTE: Si necesitas acceso SSH desde una IP específica:"
echo "    ufw allow from TU_IP to any port 22"
echo ""
echo "📊 Reglas activas:"
ufw status numbered
```

**Ejecutar:**
```bash
sudo bash /opt/usipipobot/scripts/setup_firewall.sh
```

---

### 1.2 Hardening de SSH

**Archivo: `/etc/ssh/sshd_config`**

```bash
# =============================================================================
# CONFIGURACIÓN DE SSH ENDURECIDA
# =============================================================================

# Autenticación
PermitRootLogin no                    # Nunca permitir root directo
PasswordAuthentication no             # Solo llaves SSH
PubkeyAuthentication yes              # Habilitar autenticación por llaves
AuthenticationMethods publickey       # Solo llaves, nada de passwords

# Usuarios permitidos (CRÍTICO)
AllowUsers usipipo                    # Solo el usuario usipipo puede hacer SSH
# Si necesitas otro admin: AllowUsers usipipo tu_usuario

# Seguridad de sesión
LoginGraceTime 60                     # 60 segundos para autenticar
MaxAuthTries 3                        # Máximo 3 intentos fallidos
MaxStartups 2:30:6                    # Límite de conexiones simultáneas
MaxSessions 5                         # Máximo 5 sesiones por conexión

# Network
Port 2222                             # Cambiar puerto (opcional, security by obscurity)
# ListenAddress 0.0.0.0               # Escuchar en todas las interfaces

# Protocolo
Protocol 2                            # Solo SSH v2
HostKey /etc/ssh/ssh_host_ed25519_key # Usar ED25519 (más seguro que RSA)
HostKeyAlgorithms ssh-ed25519         # Solo ED25519
PubkeyAcceptedAlgorithms ssh-ed25519  # Solo ED25519 para clientes

# Logging
SyslogFacility AUTH                   # Log de autenticación separado
LogLevel VERBOSE                      # Logs detallados

# Forwarding (deshabilitar si no se necesita)
AllowTcpForwarding no                 # No permitir tunneling TCP
X11Forwarding no                      # No permitir X11
AllowAgentForwarding no               # No permitir agent forwarding
PermitTunnel no                       # No permitir tun/tap

# Otros hardenings
UsePAM yes
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
Compression delayed                   # Solo comprimir después de autenticar
ClientAliveInterval 300               # Keep-alive cada 5 min
ClientAliveCountMax 2                 # Desconectar después de 2 keep-alives sin respuesta
PermitUserEnvironment no              # No permitir variables de entorno del usuario

# Rate limiting (protección contra brute force)
# Nota: Esto requiere que fail2ban esté configurado
```

**Reiniciar SSH:**
```bash
sudo systemctl restart sshd
```

**⚠️ ADVERTENCIA:** Antes de aplicar estos cambios:
1. Asegúrate de tener acceso de consola (no solo SSH)
2. Prueba la nueva configuración en una sesión SSH separada
3. No cierres tu sesión actual hasta verificar que puedes conectar con la nueva config

---

### 1.3 Fail2Ban para Protección contra Brute Force

**Instalación:**
```bash
sudo apt update
sudo apt install fail2ban -y
```

**Archivo: `/etc/fail2ban/jail.local`**

```ini
# =============================================================================
# FAIL2BAN - Configuración para uSipipo VPS
# =============================================================================

[DEFAULT]
# Acción por defecto: banear con iptables
banaction = ufw
bantime = 86400                     # 24 horas de ban
findtime = 600                      # Ventana de 10 minutos
maxretry = 3                        # 3 intentos fallidos = ban
ignoreip = 127.0.0.1/8 ::1          # Nunca banear localhost

# Notificación por email (opcional)
# destemail = admin@usipipo.com
# sender = fail2ban@usipipo.com
# mta = sendmail
# action = %(action_mwl)s             # Ban + email con logs

# =============================================================================
# JAILS ESPECÍFICOS
# =============================================================================

[sshd]
enabled = true
port = 22,2222                      # Ambos puertos si cambiaste el default
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 604800                    # 7 días para SSH (más agresivo)

[sshd-ddos]
enabled = true
port = 22,2222
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 5
bantime = 604800                    # 7 días

# Protección para el backend FastAPI
[usipipo-backend]
enabled = true
port = 8000
filter = usipipo-backend
logpath = /var/log/usipipo/backend.log
maxretry = 10                       # 10 intentos de rate limit = ban
bantime = 3600                      # 1 hora

# Protección para PostgreSQL (intentos de conexión fallidos)
[postgresql]
enabled = true
port = 5432
filter = postgresql
logpath = /var/log/postgresql/postgresql-15-main.log
maxretry = 5
bantime = 3600                      # 1 hora
```

**Filtro personalizado para el backend: `/etc/fail2ban/filter.d/usipipo-backend.conf`**

```ini
[Definition]
# Detectar logs de rate limiting y errores de autenticación
failregex = ^.*Rate limit exceeded for IP <HOST>.*$
            ^.*Invalid OTP attempt from IP <HOST>.*$
            ^.*Invalid JWT token from IP <HOST>.*$
            ^.*Authentication failed for user.*from IP <HOST>.*$
ignoreregex =
```

**Reiniciar Fail2Ban:**
```bash
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

**Verificar estado:**
```bash
sudo fail2ban-client status
sudo fail2ban-client status usipipo-backend
sudo fail2ban-client status sshd
```

---

### 1.4 Sysctl Hardening (Kernel)

**Archivo: `/etc/sysctl.d/99-usipipo-hardening.conf`**

```ini
# =============================================================================
# HARDENING DEL KERNEL LINUX PARA VPS uSipipo
# =============================================================================

# -----------------------------------------------------------------------------
# Network Security
# -----------------------------------------------------------------------------

# Deshabilitar IP forwarding (no somos un router)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Deshabilitar source routing (ataques de enrutamiento)
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Deshabilitar ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# No enviar ICMP redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Ignorar ICMP broadcasts (protección contra smurf attacks)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignorar ICMP bogus errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Habilitar protección contra spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Habilitar SYN cookies (protección contra SYN flood)
net.ipv4.tcp_syncookies = 1

# Limitar tasa de mensajes de error ICMP
net.ipv4.icmp_ratelimit = 100
net.ipv4.icmp_burst = 50

# TCP hardening
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# Deshabilitar IPv6 si no se usa (opcional)
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1

# -----------------------------------------------------------------------------
# Kernel Security
# -----------------------------------------------------------------------------

# Restringir dmesg (logs del kernel) para usuarios no privilegiados
kernel.dmesg_restrict = 1

# Restringir acceso a /proc/kallsyms (información de kernel)
kernel.kptr_restrict = 2

# Restringir punteros de kernel en /proc
kernel.perf_event_paranoid = 3

# Habilitar ASLR (Address Space Layout Randomization)
kernel.randomize_va_space = 2

# Prevenir que procesos no-root usen ptrace (protección contra debugging malicioso)
kernel.yama.ptrace_scope = 2

# Limitar el uso de fanotify (monitoreo de filesystem)
kernel.fanotify_max_queued_events = 16384

# -----------------------------------------------------------------------------
# Core Dumps
# -----------------------------------------------------------------------------

# Deshabilitar core dumps (pueden contener información sensible)
fs.suid_dumpable = 0

# -----------------------------------------------------------------------------
# Filesystem
# -----------------------------------------------------------------------------

# Restringir enlaces duros a archivos que no posees
fs.protected_hardlinks = 1

# Restringir enlaces simbólicos en directorios world-writable
fs.protected_symlinks = 1
```

**Aplicar cambios:**
```bash
sudo sysctl --system
```

---

## 🔐 Capa 2: Seguridad de la Base de Datos

### 2.1 PostgreSQL Hardening

**Archivo: `/etc/postgresql/15/main/pg_hba.conf`**

```ini
# =============================================================================
# PostgreSQL HBA (Host-Based Authentication)
# =============================================================================
# TIPO  DATABASE        USER            ADDRESS                 METHOD

# Conexiones locales (Unix socket) - solo usuario usipipo
local   all             usipipo                               peer
local   all             postgres                              peer

# Conexiones localhost (IPv4) - solo desde localhost
host    all             usipipo       127.0.0.1/32            md5
host    all             postgres      127.0.0.1/32            md5

# Conexiones localhost (IPv6) - solo desde localhost
host    all             usipipo       ::1/128                 md5
host    all             postgres      ::1/128                 md5

# DENEGAR todo lo demás explícitamente
host    all             all           0.0.0.0/0               reject
host    all             all           ::/0                    reject
```

**Reiniciar PostgreSQL:**
```bash
sudo systemctl restart postgresql
```

### 2.2 Usuario de Base de Datos con Privilegios Mínimos

**Script SQL: `/opt/usipipobot/scripts/setup_db_user.sql`**

```sql
-- =============================================================================
-- Configuración de usuario de base de datos con privilegios mínimos
-- =============================================================================

-- Crear usuario solo para la aplicación (no superuser)
CREATE USER usipipo_app WITH
    PASSWORD '<generar_contraseña_segura_con_openssl_rand_hex_32>'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 20;

-- Grant solo en la base de datos específica
GRANT CONNECT ON DATABASE usipipodb TO usipipo_app;
GRANT USAGE ON SCHEMA public TO usipipo_app;

-- Grant en tablas existentes (se ejecuta después de crear las tablas)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO usipipo_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO usipipo_app;

-- Grant por defecto para tablas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO usipipo_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO usipipo_app;

-- Usuario solo para lecturas (opcional, para reporting)
CREATE USER usipipo_readonly WITH
    PASSWORD '<otra_contraseña_segura>'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 5;

GRANT CONNECT ON DATABASE usipipodb TO usipipo_readonly;
GRANT USAGE ON SCHEMA public TO usipipo_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO usipipo_readonly;

-- Revocar privilegios de PUBLIC (por seguridad)
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE usipipodb FROM PUBLIC;
```

**Ejecutar:**
```bash
sudo -u postgres psql -f /opt/usipipobot/scripts/setup_db_user.sql
```

### 2.3 Encriptación de Datos Sensibles

**Nueva columna para datos encriptados en la tabla `users`:**

```sql
-- Agregar columna para wallet encriptada
ALTER TABLE users
    ADD COLUMN wallet_address_encrypted BYTEA,
    ADD COLUMN wallet_nonce BYTEA;

-- Función de encriptación (usando pgcrypto)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- La aplicación usará estas funciones para encriptar/desencriptar
-- ENCRYPT: pgp_sym_encrypt(data, secret_key)
-- DECRYPT: pgp_sym_decrypt(encrypted_data, secret_key)
```

**En el backend (`infrastructure/persistence/postgresql/encrypted_repository.py`):**

```python
from sqlalchemy import text
from cryptography.fernet import Fernet
import base64
import os

class EncryptedWalletRepository:
    """Repositorio para wallets con encriptación a nivel de aplicación."""

    def __init__(self, session, encryption_key: str):
        self.session = session
        self.cipher = Fernet(encryption_key.encode())

    async def save_wallet(self, telegram_id: int, wallet_address: str):
        """Guardar wallet encriptada."""
        # Encriptar con Fernet (AES-128-CBC)
        encrypted = self.cipher.encrypt(wallet_address.encode())

        await self.session.execute(
            text("""
                UPDATE users
                SET wallet_address_encrypted = :encrypted,
                    updated_at = NOW()
                WHERE telegram_id = :telegram_id
            """),
            {"telegram_id": telegram_id, "encrypted": encrypted}
        )
        await self.session.commit()

    async def get_wallet(self, telegram_id: int) -> str | None:
        """Obtener wallet desencriptada."""
        result = await self.session.execute(
            text("""
                SELECT wallet_address_encrypted
                FROM users
                WHERE telegram_id = :telegram_id
            """),
            {"telegram_id": telegram_id}
        )
        row = result.first()

        if row and row[0]:
            # Desencriptar
            decrypted = self.cipher.decrypt(row[0])
            return decrypted.decode()
        return None
```

---

## 🔑 Capa 3: Gestión de Secrets

### 3.1 Generación de Secrets Seguros

**Script: `/opt/usipipobot/scripts/generate_secrets.sh`**

```bash
#!/bin/bash
# Generar secrets criptográficamente seguros para .env

set -e

echo "🔐 Generando secrets seguros..."

# SECRET_KEY para JWT (64 caracteres hex = 256 bits)
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY"

# Contraseña para PostgreSQL (32 caracteres)
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
echo "DATABASE_PASSWORD=$DB_PASSWORD"

# Contraseña para Redis (32 caracteres)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"

# Key para encriptación Fernet (URL-safe base64)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"

# JWT Secret para Android (64 caracteres)
ANDROID_JWT_SECRET=$(openssl rand -hex 32)
echo "ANDROID_JWT_SECRET=$ANDROID_JWT_SECRET"

# Webhook secret para TronDealer (32 caracteres)
TRON_DEALER_WEBHOOK_SECRET=$(openssl rand -hex 16)
echo "TRON_DEALER_WEBHOOK_SECRET=$TRON_DEALER_WEBHOOK_SECRET"

echo ""
echo "⚠️  GUARDA ESTOS SECRETS EN UN LUGAR SEGURO (KeePass, Bitwarden)"
echo "⚠️  NUNCA LOS COMMITAS AL REPOSITORIO"
```

### 3.2 Permisos del Archivo .env

**Script de protección: `/opt/usipipobot/scripts/protect_env.sh`**

```bash
#!/bin/bash
# Proteger el archivo .env con permisos estrictos

set -e

ENV_FILE="/opt/usipipobot/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ El archivo .env no existe"
    exit 1
fi

# Cambiar propietario a root:usipipo (solo root puede leer)
sudo chown root:usipipo "$ENV_FILE"

# Permisos: solo owner puede leer/escribir, grupo puede leer
sudo chmod 640 "$ENV_FILE"

# Verificar
ls -la "$ENV_FILE"

echo "✅ Archivo .env protegido"
echo ""
echo "El archivo .env ahora solo puede ser leído por:"
echo "  - root (owner)"
echo "  - usuarios del grupo usipipo"
```

### 3.3 Rotación de Secrets

**Política de rotación:**

| Secret | Frecuencia | Método |
|--------|------------|--------|
| SECRET_KEY (JWT) | 90 días o si hay compromiso | Generar nuevo, invalidar JWTs existentes |
| Contraseña DB | 180 días | Cambiar en PostgreSQL y .env |
| Contraseña Redis | 180 días | Cambiar en Redis config y .env |
| SSH Keys | 365 días | Generar nuevo par, actualizar authorized_keys |
| Encryption Key | Solo si hay compromiso | Re-encriptar todos los datos |

**Script de rotación de JWT Secret: `/opt/usipipobot/scripts/rotate_jwt_secret.sh`**

```bash
#!/bin/bash
# Rotar el SECRET_KEY y invalidar todos los JWTs existentes

set -e

echo "🔄 Rotando SECRET_KEY..."

# Generar nuevo secret
NEW_SECRET=$(openssl rand -hex 32)

# Backup del .env actual
cp /opt/usipipobot/.env /opt/usipipobot/.env.backup.$(date +%Y%m%d_%H%M%S)

# Actualizar .env
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" /opt/usipipobot/.env

# Reiniciar servicios para aplicar el nuevo secret
sudo systemctl restart usipipo-backend

# Limpiar blacklist de Redis (los JWTs viejos ya no son válidos)
redis-cli FLUSHDB

# Notificar al admin
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{
        \"chat_id\": ${ADMIN_ID},
        \"text\": \"🔐 SECRET_KEY rotado exitosamente\\n\\n⚠️ Todos los JWTs existentes fueron invalidados.\\nLos usuarios deberán iniciar sesión nuevamente.\",
        \"parse_mode\": \"HTML\"
    }"

echo "✅ SECRET_KEY rotado exitosamente"
echo "⚠️  Todos los JWTs existentes fueron invalidados"
```

---

## 🛡️ Capa 4: Seguridad de la APK Android

### 4.1 Certificate Pinning

**En el backend, generar el pin del certificado:**

**Script: `/opt/usipipobot/scripts/generate_cert_pin.sh`**

```bash
#!/bin/bash
# Generar el pin SHA-256 del certificado SSL

DOMAIN="usipipo.duckdns.org"

echo "📜 Obteniendo certificado de $DOMAIN..."

# Obtener el certificado y calcular el pin
openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | \
    openssl x509 -pubkey -noout | \
    openssl pkey -pubin -outform der | \
    openssl dgst -sha256 -binary | \
    openssl enc -base64

echo ""
echo "Este es el pin que debe ir en la APK (buildozer.spec o config.py)"
```

**En la APK (`android_app/src/config.py`):**

```python
# Certificate pins para el backend
# Se generan con: openssl s_client -connect domain:443 | openssl x509 -pubkey -noout | ...
CERT_PINS = [
    "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",  # Pin actual
    "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=",  # Pin de respaldo (próximo certificado)
]

# El pin de respaldo es CRÍTICO: cuando el certificado se renueve (Let's Encrypt cada 90 días),
# la APK debe tener ambos pins para no quedar inservible hasta el próximo update.
```

**En el cliente HTTP de la APK (`android_app/src/services/api_client.py`):**

```python
import httpx
import ssl
from typing import List
from .config import CERT_PINS, BACKEND_URL

class CertificatePinnedTransport(httpx.AsyncHTTPTransport):
    """Transporte HTTP con certificate pinning."""

    def __init__(self, pins: List[str]):
        self.pins = pins

        # Configurar SSL con pinning
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        # Implementar pinning manualmente (httpx no lo soporta nativamente)
        # Se necesita una implementación custom con urllib3
        super().__init__(ssl_context=ssl_context)

    async def handle_async_request(self, request):
        # Verificar el pin del certificado antes de enviar la request
        # Implementación simplificada - en producción usar urllib3 con pinning
        return await super().handle_async_request(request)

def create_api_client() -> httpx.AsyncClient:
    """Crear cliente HTTP con certificate pinning."""

    transport = CertificatePinnedTransport(pins=CERT_PINS)

    client = httpx.AsyncClient(
        base_url=BACKEND_URL,
        transport=transport,
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers={
            "User-Agent": "uSipipo-Android/1.0.0",
            "Accept": "application/json",
        }
    )

    return client
```

### 4.2 Almacenamiento Seguro del JWT

**En la APK (`android_app/src/storage/secure_storage.py`):**

```python
"""
Almacenamiento seguro usando Android Keystore.
Nunca guardar el JWT en texto plano o SharedPreferences.
"""
import keyring
from loguru import logger

SERVICE_NAME = "usipipo_secure_storage"
JWT_KEY = "usipipo_jwt_token"

class SecureStorage:
    """Almacenamiento seguro usando el keystore de Android."""

    @staticmethod
    def save_jwt(token: str) -> bool:
        """
        Guardar JWT en el keystore de Android.

        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            keyring.set_password(SERVICE_NAME, JWT_KEY, token)
            logger.info("JWT guardado en keystore")
            return True
        except Exception as e:
            logger.error(f"Error guardando JWT: {e}")
            return False

    @staticmethod
    def get_jwt() -> str | None:
        """
        Obtener JWT del keystore.

        Returns:
            str | None: El token o None si no existe
        """
        try:
            token = keyring.get_password(SERVICE_NAME, JWT_KEY)
            if token:
                logger.debug("JWT recuperado del keystore")
            return token
        except Exception as e:
            logger.error(f"Error recuperando JWT: {e}")
            return None

    @staticmethod
    def delete_jwt() -> bool:
        """
        Eliminar JWT del keystore.

        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            keyring.delete_password(SERVICE_NAME, JWT_KEY)
            logger.info("JWT eliminado del keystore")
            return True
        except Exception as e:
            logger.error(f"Error eliminando JWT: {e}")
            return False

    @staticmethod
    def is_jwt_valid() -> bool:
        """
        Verificar si hay un JWT almacenado.
        No verifica si está expirado, solo si existe.
        """
        token = SecureStorage.get_jwt()
        return token is not None and len(token) > 0
```

---

## 🔒 Capa 5: Seguridad de la API Backend

### 5.1 Middleware de Security Headers

**Archivo: `infrastructure/api/middleware/security_headers.py`**

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que agrega headers de seguridad HTTP a todas las respuestas.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevenir MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevenir leakage de información por referer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Habilitar HSTS (solo en producción)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (CSP) - restrictivo para API
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        # Permissions Policy (antes Feature Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Cache control para respuestas sensibles
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Eliminar headers que revelan información
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        return response
```

**Registrar en `infrastructure/api/server.py`:**

```python
from infrastructure.api.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

### 5.2 Rate Limiting Avanzado

**Archivo: `infrastructure/api/middleware/rate_limiter.py`**

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis
from datetime import datetime, timezone
import hashlib

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting con Redis para múltiples reglas por endpoint.
    """

    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)

        # Reglas de rate limiting
        self.rules = {
            # Endpoint: (límite, ventana en segundos)
            "POST:/api/v1/auth/request-otp": (3, 3600),      # 3 por hora
            "POST:/api/v1/auth/verify-otp": (5, 900),         # 5 por 15 min
            "POST:/api/v1/keys/create": (5, 3600),            # 5 por hora
            "POST:/api/v1/payments/*/create": (10, 3600),     # 10 por hora
            "GET:/api/v1/dashboard/summary": (60, 60),        # 60 por minuto
            "GET:/api/v1/notifications/pending": (120, 60),   # 120 por minuto
            "POST:/api/v1/tickets/create": (3, 3600),         # 3 por hora
        }

    async def dispatch(self, request: Request, call_next):
        # Obtener identificador único del cliente
        client_id = await self._get_client_identifier(request)
        endpoint = f"{request.method}:{request.url.path}"

        # Verificar si hay regla para este endpoint
        if endpoint in self.rules:
            limit, window = self.rules[endpoint]

            # Construir key de Redis
            key = f"rate:{endpoint}:{client_id}"

            # Obtener conteo actual
            current = await self.redis.get(key)

            if current is None:
                # Primer request, inicializar contador
                await self.redis.setex(key, window, 1)
            elif int(current) >= limit:
                # Rate limit excedido
                ttl = await self.redis.ttl(key)

                # Log para monitoreo
                logger.warning(
                    f"Rate limit excedido: {endpoint} - IP: {client_id} - "
                    f"Límite: {limit}/{window}s"
                )

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "Demasiadas peticiones. Por favor espera.",
                        "retry_after": ttl
                    }
                )
            else:
                # Incrementar contador
                await self.redis.incr(key)

        response = await call_next(request)
        return response

    async def _get_client_identifier(self, request: Request) -> str:
        """
        Obtener identificador único del cliente.
        Prioridad: JWT telegram_id > IP address
        """
        # Intentar obtener telegram_id del JWT
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Aquí se podría decodificar el JWT para obtener el telegram_id
            # Por ahora, usamos IP
            pass

        # Usar IP address como fallback
        # Considerar X-Forwarded-For si hay proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        # Hashear la IP para privacidad en logs
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
```

### 5.3 Validación Estricta de Inputs con Pydantic

**Ejemplo: `infrastructure/api/schemas/auth.py`**

```python
from pydantic import BaseModel, Field, field_validator
import re

class OTPRequest(BaseModel):
    """Request para solicitar OTP."""

    identifier: str = Field(..., min_length=1, max_length=50)

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validar que el identifier sea username o telegram_id válido."""
        v = v.strip()

        # Si empieza con @, es username
        if v.startswith("@"):
            # Username: 5-32 caracteres, solo letras, números, guiones bajos
            if not re.match(r"^[a-zA-Z0-9_]{5,32}$", v[1:]):
                raise ValueError(
                    "Username inválido. Debe tener 5-32 caracteres "
                    "y solo letras, números y guiones bajos"
                )
        else:
            # Debe ser telegram_id (número)
            if not v.isdigit():
                raise ValueError("Debe ser un username (@usuario) o telegram_id válido")
            if not (1 <= int(v) <= 9223372036854775807):
                raise ValueError("telegram_id fuera de rango válido")

        return v


class OTPVerify(BaseModel):
    """Request para verificar OTP."""

    identifier: str
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Validar que el OTP sea numérico de 6 dígitos."""
        if not v.isdigit():
            raise ValueError("El código OTP debe ser numérico")
        return v
```

---

## 📊 Capa 6: Monitoreo de Seguridad

### 6.1 Logs de Seguridad Centralizados

**Archivo: `/etc/rsyslog.d/10-usipipo-security.conf`**

```
# =============================================================================
# Centralizar logs de seguridad en un solo archivo
# =============================================================================

# Logs de autenticación SSH
:programname, isequal, "sshd" /var/log/usipipo/security-ssh.log

# Logs de Fail2Ban
:programname, isequal, "fail2ban" /var/log/usipipo/security-fail2ban.log

# Logs del backend (autenticación, rate limiting)
:programname, isequal, "usipipo-backend" /var/log/usipipo/security-backend.log

# Logs de PostgreSQL (intentos de conexión fallidos)
:programname, isequal, "postgres" /var/log/usipipo/security-postgres.log

# Rotación de logs
# Configurar en /etc/logrotate.d/usipipo-security
```

### 6.2 Alertas de Seguridad por Telegram

**Script: `/opt/usipipobot/scripts/security_alert.sh`**

```bash
#!/bin/bash
# Enviar alertas de seguridad críticas por Telegram

set -e

MESSAGE="$1"
CHAT_ID="${ADMIN_ID}"
BOT_TOKEN="${TELEGRAM_TOKEN}"

# Solo enviar si hay mensaje
if [ -z "$MESSAGE" ]; then
    echo "Uso: security_alert.sh <mensaje>"
    exit 1
fi

# Enviar a Telegram
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{
        \"chat_id\": ${CHAT_ID},
        \"text\": \"🚨 ALERTA DE SEGURIDAD\\n\\n${MESSAGE}\",
        \"parse_mode\": \"HTML\"
    }"

echo "Alerta enviada"
```

**Ejemplos de eventos que disparan alertas:**

1. **Múltiples bans de Fail2Ban en 1 hora** (>5 IPs baneadas)
2. **Intento de acceso SSH root** (debería estar deshabilitado, pero igual alertar)
3. **Rate limit excedido >100 veces en 5 minutos** (posible DDoS)
4. **PostgreSQL: múltiples intentos de conexión fallidos**
5. **Backend: múltiples intentos de JWT inválido**
6. **Uso de RAM >95%** (posible ataque de agotamiento)
7. **Disco >95%** (posible ataque de llenado de logs)

---

## ✅ Checklist de Implementación

### Día 1-2: Hardening del SO
- [ ] Configurar firewall UFW
- [ ] Endurecer configuración SSH
- [ ] Instalar y configurar Fail2Ban
- [ ] Aplicar sysctl hardening
- [ ] Verificar que todos los servicios funcionen

### Día 3-4: Seguridad de Base de Datos
- [ ] Configurar pg_hba.conf (solo localhost)
- [ ] Crear usuario de DB con privilegios mínimos
- [ ] Habilitar pgcrypto para encriptación
- [ ] Implementar repositorio de wallets encriptadas

### Día 5-6: Gestión de Secrets
- [ ] Generar todos los secrets con el script
- [ ] Guardar secrets en gestor seguro (KeePass/Bitwarden)
- [ ] Proteger archivo .env con permisos 640
- [ ] Documentar política de rotación

### Día 7-8: Seguridad de la APK
- [ ] Generar certificate pins del backend
- [ ] Implementar certificate pinning en la APK
- [ ] Implementar almacenamiento seguro del JWT
- [ ] Probar que la APK no conecta sin el pin correcto

### Día 9-10: Seguridad de la API
- [ ] Implementar middleware de security headers
- [ ] Configurar rate limiting avanzado
- [ ] Validar todos los inputs con Pydantic
- [ ] Eliminar headers que revelan información

### Día 11-12: Monitoreo de Seguridad
- [ ] Configurar logs centralizados de seguridad
- [ ] Implementar script de alertas por Telegram
- [ ] Configurar alertas para eventos críticos
- [ ] Probar todo el sistema de alertas

---

## 🎯 Métricas de Éxito de Seguridad

| Métrica | Objetivo |
|---------|----------|
| Intentos de brute force bloqueados | 100% |
| Rate limits aplicados correctamente | 100% |
| Secrets rotados según política | 100% |
| Tiempo de detección de incidentes | <5 minutos |
| Tiempo de respuesta a incidentes | <30 minutos |
| Vulnerabilidades críticas | 0 |
| Datos sensibles encriptados | 100% |

---

*Documento versión 1.0 - Fecha: Marzo 2026*
