# Plan 1 (v2): Integración del Protocolo TrustTunnel en uSipipo VPN
**Fecha:** 16 de Marzo 2026
**Proyecto:** uSipipo VPN — usipipobot
**Estado:** Borrador — pendiente aprobación
**Prioridad:** 🟢 Baja (implementar después del bug de checkout, latencia y adblock)
**Tiempo estimado:** 1-2 días
**Repositorio oficial:** https://github.com/TrustTunnel/TrustTunnel
**Licencia:** Apache 2.0 — libre para uso comercial

---

## 1. ¿Qué es TrustTunnel?

<TrustTunnel es el protocolo que ha estado corriendo internamente en todas las apps de AdGuard VPN
(móvil, desktop, extensiones). Fue liberado como open source el 21 de enero de 2026 bajo Apache 2.0.

Características técnicas clave:

| Característica | Detalle |
|---------------|---------|
| **Obfuscación** | El tráfico es indistinguible de HTTPS normal — imposible de detectar por DPI |
| **Protocolos** | Soporta HTTP/1.1, HTTP/2 y QUIC |
| **Tunneling** | TCP, UDP e ICMP |
| **Puerto** | 443 (el mismo que HTTPS) — prácticamente imposible de bloquear |
| **Servidor** | Binario Rust único, sin dependencias — Linux x86_64 y ARM64 |
| **Instalación** | Script oficial de 1 línea + wizard interactivo |
| **Servicio** | Template systemd incluido en el paquete |

**Diferenciador vs Outline y WireGuard:** Outline y WireGuard son detectables con DPI avanzado
(China, Irán, Rusia). TrustTunnel no — se ve exactamente como navegar a un sitio HTTPS.

---

## 2. Decisión: Nativo con systemd (NO Docker)

### Por qué NO usar Docker para TrustTunnel

La intuición de que Docker consume menos RAM es incorrecta. La realidad:

- **Docker añade overhead**, no lo reduce. El daemon de Docker en sí consume ~50MB de RAM
  adicionales. Con un proceso liviano como TrustTunnel (binario Rust), ese overhead es
  proporcionalmente mayor.
- **Outline usa Docker** porque tiene muchas dependencias internas (Node.js, Shadowsocks, etc.).
  TrustTunnel es un **binario único sin dependencias** — el caso ideal para instalación nativa.
- **Port mapping añade latencia**: Docker mapea `443→8443` internamente, una capa NAT extra
  que no existe en instalación nativa.
- **El README lo indica explícitamente**: para producción en Linux, el método recomendado es
  la instalación nativa con systemd.

### Instalación nativa: lo mismo que tienes con WireGuard

```
WireGuard:   binario wg-quick → systemd service → gestión de peers por comandos
TrustTunnel: binario único     → systemd service → gestión de clientes por CLI
```

El patrón es idéntico al que ya conoces. Sin sorpresas.

---

## 3. Prerequisito crítico: certificado TLS válido

Este es el único requisito diferente respecto a WireGuard y Outline:

> Los clientes móviles Flutter (Android/iOS) **requieren un certificado TLS firmado por
> una CA pública reconocida** (Let's Encrypt, ZeroSSL, etc.) asociado a un dominio.

Tú ya tienes `usipipo.duckdns.org` con Nginx. La estrategia es:

```
usipipo.duckdns.org:443  →  Nginx (reverse proxy actual)
                                  ↓
                     ¿Cómo convive TrustTunnel en el puerto 443?
```

**El problema:** TrustTunnel necesita el puerto 443 directamente para su obfuscación
(parecer tráfico HTTPS). Si Nginx ya ocupa ese puerto, hay conflicto.

**Solución recomendada — Nginx como SNI proxy:**

Nginx actúa como distribuidor de tráfico TLS por hostname:

```
:443 (todo el tráfico TLS)
        │
     Nginx SNI proxy
        │              │
        ▼              ▼
  trusttunnel.   usipipo.duckdns.org
  usipipo.       → FastAPI (mini app web)
  duckdns.org    → bot webhook (si aplica)
  → TrustTunnel
    :8443
```

```nginx
# /etc/nginx/nginx.conf — bloque stream (nivel TCP, no HTTP)
stream {
    map $ssl_preread_server_name $backend {
        trusttunnel.usipipo.duckdns.org  127.0.0.1:8443;
        usipipo.duckdns.org              127.0.0.1:8080;
        default                          127.0.0.1:8080;
    }

    server {
        listen 443;
        ssl_preread on;
        proxy_pass $backend;
    }
}
```

De esta forma:
- `usipipo.duckdns.org:443` → FastAPI / web app (igual que ahora)
- `trusttunnel.usipipo.duckdns.org:443` → TrustTunnel en :8443

**Alternativa más simple — puerto separado:**

Si no quieres tocar Nginx, TrustTunnel puede escuchar en un puerto distinto
(ej: `8443` o `2053`). Pierde algo de obfuscación pero sigue funcionando.
Esta es la opción recomendada para el primer deployment.

---

## 4. Instalación del servidor en el VPS

### 4.1 Script de instalación oficial (1 línea)

```bash
# Instalar TrustTunnel en /opt/trusttunnel (binario, wizard, template systemd)
curl -fsSL https://raw.githubusercontent.com/TrustTunnel/TrustTunnel/refs/heads/master/scripts/install.sh \
  | sh -s -

# Verificar instalación
ls /opt/trusttunnel/
# trusttunnel_endpoint  setup_wizard  trusttunnel.service.template  ...
```

### 4.2 Wizard de configuración interactivo

```bash
cd /opt/trusttunnel/
./setup_wizard
```

El wizard pregunta:

| Campo | Valor recomendado para uSipipo |
|-------|-------------------------------|
| `listen_address` | `0.0.0.0:8443` (si Nginx hace proxy) o `0.0.0.0:443` (si puerto directo) |
| `domain` | `trusttunnel.usipipo.duckdns.org` o `usipipo.duckdns.org` |
| `cert_path` | `/etc/letsencrypt/live/usipipo.duckdns.org/fullchain.pem` |
| `key_path` | `/etc/letsencrypt/live/usipipo.duckdns.org/privkey.pem` |

Genera automáticamente `vpn.toml` y `hosts.toml` en `/opt/trusttunnel/`.

### 4.3 Configurar como servicio systemd

```bash
cd /opt/trusttunnel/
cp trusttunnel.service.template /etc/systemd/system/trusttunnel.service

sudo systemctl daemon-reload
sudo systemctl enable trusttunnel
sudo systemctl start trusttunnel
sudo systemctl status trusttunnel
```

### 4.4 Verificar que corre

```bash
# Ver el proceso
ps aux | grep trusttunnel_endpoint | grep -v grep

# Verificar RAM consumida (esperado: < 30MB para pocos usuarios)
cat /proc/$(pgrep trusttunnel_endpoint)/status | grep VmRSS

# Ver logs
journalctl -u trusttunnel -f
```

### 4.5 Actualizar en el futuro (1 línea)

```bash
# Re-ejecutar el instalador sobreescribe el binario con la última versión
curl -fsSL https://raw.githubusercontent.com/TrustTunnel/TrustTunnel/refs/heads/master/scripts/install.sh \
  | sh -s -
sudo systemctl restart trusttunnel
```

---

## 5. Generación de claves de cliente

### 5.1 Generar configuración para un cliente

```bash
cd /opt/trusttunnel/

# Generar config para un cliente nuevo
# <nombre_cliente>: identificador único (ej: user_12345_key_1)
# <dominio_o_ip>: dirección que usará el cliente para conectarse
./trusttunnel_endpoint vpn.toml hosts.toml \
  -c user_12345_key_1 \
  -a trusttunnel.usipipo.duckdns.org

# Output: deep-link tt://? listo para QR code o app móvil
# Ejemplo: tt://?server=trusttunnel.usipipo.duckdns.org&token=...
```

Si el certificado es de Let's Encrypt (CA pública reconocida), el deep-link es
compacto y el cliente lo acepta automáticamente sin advertencias.

### 5.2 Integración con el bot — TrustTunnelProvider

```python
# infrastructure/vpn_providers/trusttunnel_provider.py

import asyncio
import subprocess
import re
from dataclasses import dataclass
from typing import Optional
from domain.entities.vpn_key import VpnKey
from domain.enums.protocol_type import ProtocolType

TRUSTTUNNEL_DIR = "/opt/trusttunnel"
TRUSTTUNNEL_BINARY = f"{TRUSTTUNNEL_DIR}/trusttunnel_endpoint"
VPN_TOML = f"{TRUSTTUNNEL_DIR}/vpn.toml"
HOSTS_TOML = f"{TRUSTTUNNEL_DIR}/hosts.toml"
SERVER_ADDRESS = "trusttunnel.usipipo.duckdns.org"  # o IP:8443


class TrustTunnelProvider:
    """Provider para el protocolo TrustTunnel (AdGuard VPN)."""

    async def create_key(self, user_id: int, key_name: str) -> VpnKey:
        """Genera una nueva clave de cliente TrustTunnel."""
        client_id = f"user_{user_id}_{key_name}"

        proc = await asyncio.create_subprocess_exec(
            TRUSTTUNNEL_BINARY,
            VPN_TOML, HOSTS_TOML,
            "-c", client_id,
            "-a", SERVER_ADDRESS,
            "--format", "deeplink",
            cwd=TRUSTTUNNEL_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"TrustTunnel key creation failed: {stderr.decode()}"
            )

        # Extraer el deep-link tt://? del output
        output = stdout.decode().strip()
        deeplink = self._extract_deeplink(output)

        return VpnKey(
            user_id=user_id,
            key_name=key_name,
            protocol_type=ProtocolType.TRUSTTUNNEL,
            access_url=deeplink,
            client_id=client_id,
            adblock_enabled=False,  # TrustTunnel no incluye adblock por diseño
        )

    async def delete_key(self, client_id: str) -> bool:
        """Revoca una clave de cliente existente."""
        # TrustTunnel gestiona clientes en hosts.toml
        # El binario debe soportar comando de revocación — verificar en docs
        try:
            proc = await asyncio.create_subprocess_exec(
                TRUSTTUNNEL_BINARY,
                VPN_TOML, HOSTS_TOML,
                "--revoke", client_id,
                cwd=TRUSTTUNNEL_DIR,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, _ = await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    def _extract_deeplink(self, output: str) -> str:
        """Extrae el deep-link tt:// del output del binario."""
        for line in output.splitlines():
            if line.strip().startswith("tt://"):
                return line.strip()
        raise ValueError(f"No deeplink found in output:\n{output}")
```

### 5.3 Enum ProtocolType actualizado

```python
# domain/enums/protocol_type.py

from enum import Enum

class ProtocolType(str, Enum):
    OUTLINE = "outline"
    WIREGUARD = "wireguard"
    TRUSTTUNNEL = "trusttunnel"    # NUEVO — antes llamado "adguard"
```

### 5.4 Cambio en base de datos

```sql
-- Actualizar constraint de protocol_type para incluir trusttunnel
ALTER TABLE vpn_keys
DROP CONSTRAINT IF EXISTS vpn_keys_protocol_type_check;

ALTER TABLE vpn_keys
ADD CONSTRAINT vpn_keys_protocol_type_check
CHECK (protocol_type IN ('outline', 'wireguard', 'trusttunnel'));

-- Índice
CREATE INDEX IF NOT EXISTS idx_vpn_keys_protocol ON vpn_keys(protocol_type);

-- Migración Alembic
```

```python
# migrations/versions/XXXX_add_trusttunnel_protocol.py

def upgrade():
    op.execute("""
        ALTER TABLE vpn_keys
        DROP CONSTRAINT IF EXISTS vpn_keys_protocol_type_check
    """)
    op.execute("""
        ALTER TABLE vpn_keys
        ADD CONSTRAINT vpn_keys_protocol_type_check
        CHECK (protocol_type IN ('outline', 'wireguard', 'trusttunnel'))
    """)

def downgrade():
    op.execute("""
        ALTER TABLE vpn_keys
        DROP CONSTRAINT IF EXISTS vpn_keys_protocol_type_check
    """)
    op.execute("""
        ALTER TABLE vpn_keys
        ADD CONSTRAINT vpn_keys_protocol_type_check
        CHECK (protocol_type IN ('outline', 'wireguard'))
    """)
```

---

## 6. UI en el bot — Selector de protocolo

```python
# telegram_bot/features/vpn/keyboards.py

def protocol_selector_keyboard(user_plan: Optional[str] = None) -> InlineKeyboardMarkup:
    is_ninja = user_plan == "ninja"

    keyboard = [
        [InlineKeyboardButton(
            "📡 Outline — Estable, universal",
            callback_data="proto:outline"
        )],
        [InlineKeyboardButton(
            "⚡ WireGuard — Rápido + AdBlock 🛡️",
            callback_data="proto:wireguard"
        )],
    ]

    if is_ninja:
        keyboard.append([InlineKeyboardButton(
            "🔮 TrustTunnel — Anti-censura, invisible 🆕",
            callback_data="proto:trusttunnel"
        )])
    else:
        keyboard.append([InlineKeyboardButton(
            "🔮 TrustTunnel — Solo Plan Ninja 🔒",
            callback_data="proto:trusttunnel_locked"
        )])

    return InlineKeyboardMarkup(keyboard)
```

Mensaje al crear una clave TrustTunnel exitosamente:

```
✅ Clave TrustTunnel creada

🔮 Protocolo: TrustTunnel
🌐 Servidor: EE.UU (US-East)
🔒 Cifrado: HTTP/2 + QUIC
👁️ Obfuscación: ACTIVA

━━━━━━━━━━━━━━━━
🛡️ Tu tráfico es invisible para:
├─ Tu proveedor de Internet (ISP)
├─ Firewalls corporativos
├─ Sistemas de censura (DPI)
└─ Cualquier tercero en la red

━━━━━━━━━━━━━━━━
📲 Cómo conectarte:

1. Descarga la app TrustTunnel Flutter:
   [Android] [iOS]

2. En la app, selecciona "Importar" y
   escanea el código QR de abajo

3. Activa la conexión ✅

[Mostrar QR] [Copiar enlace tt://]
━━━━━━━━━━━━━━━━
⚠️ Exclusivo para Plan Ninja
```

---

## 7. Restricción de protocolo por plan

```python
# application/services/vpn_service.py

PROTOCOL_PLAN_REQUIREMENTS = {
    ProtocolType.OUTLINE:      None,           # Todos los planes
    ProtocolType.WIREGUARD:    ["estudiante", "one_month", "three_months",
                                "six_months", "ninja"],
    ProtocolType.TRUSTTUNNEL:  ["ninja"],       # Exclusivo Plan Ninja
}

async def create_key(
    self, user_id: int, protocol: ProtocolType, key_name: str, ...
) -> VpnKey:
    required_plans = PROTOCOL_PLAN_REQUIREMENTS.get(protocol)

    if required_plans is not None:
        active_plan = await self.subscription_service.get_active_plan(user_id)
        plan_type = active_plan.plan_type.value if active_plan else None

        if plan_type not in required_plans:
            if protocol == ProtocolType.TRUSTTUNNEL:
                raise PermissionError(
                    "TrustTunnel es exclusivo del Plan Ninja 🔮\n"
                    "Activa tu Plan Ninja desde el menú de tienda."
                )
            raise PermissionError("Plan insuficiente para este protocolo.")

    provider = self._get_provider(protocol)
    return await provider.create_key(user_id, key_name)

def _get_provider(self, protocol: ProtocolType):
    providers = {
        ProtocolType.OUTLINE:     self.outline_provider,
        ProtocolType.WIREGUARD:   self.wireguard_provider,
        ProtocolType.TRUSTTUNNEL: self.trusttunnel_provider,  # NUEVO
    }
    if protocol not in providers:
        raise ValueError(f"Protocolo no soportado: {protocol}")
    return providers[protocol]
```

---

## 8. Integración en el medidor de estado del servidor (Plan 3)

Agregar TrustTunnel al `ServerStats`:

```python
# infrastructure/jobs/latency_collector_job.py

@dataclass
class ServerStats:
    ...
    trusttunnel_status: bool = False   # True = daemon UP

async def collect_server_stats() -> ServerStats:
    ...
    tt_up = is_service_active("trusttunnel")

    return ServerStats(
        ...
        trusttunnel_status=tt_up,
    )
```

Mensaje `/status` actualizado:

```
📡 Estado del Servidor uSipipo

🟢 Excelente

⚡ Latencia:    23 ms
🖥️ CPU:         42%
💾 RAM:         61%

Protocolos:
✅ Outline
✅ WireGuard + 🛡️ AdBlock
✅ TrustTunnel 🔮

Actualizado: hace 38s
```

---

## 9. Estimación de RAM en producción

| Servicio | RAM estimada |
|---------|-------------|
| Bot (Python + aiogram) | ~80 MB |
| FastAPI (web app) | ~60 MB |
| Outline (Docker) | ~120 MB |
| WireGuard (kernel module) | ~15 MB |
| dnsproxy | ~12 MB |
| **TrustTunnel (Rust, nativo)** | **~25-40 MB** |
| **Total estimado** | **~310-325 MB** |

Con 2GB de RAM disponibles y ~600-700 MB usados por el sistema operativo, queda
~1.3 GB de margen. TrustTunnel cabe holgadamente.

**Benchmark recomendado antes del lanzamiento:**

```bash
# Medir baseline antes de instalar TrustTunnel
free -m | grep Mem

# Después de instalar y arrancar el daemon
free -m | grep Mem

# Con 20 clientes conectados simultáneamente
free -m | grep Mem
```

---

## 10. Firewall: abrir el puerto de TrustTunnel

```bash
# Si usa puerto 443 directo (Nginx SNI proxy)
# → Puerto 443 ya está abierto

# Si usa puerto 8443 separado
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 8443 -j ACCEPT  # Para QUIC
sudo netfilter-persistent save

# O con ufw
sudo ufw allow 8443/tcp
sudo ufw allow 8443/udp
```

---

## 11. Rollback si algo falla

```bash
# Detener y deshabilitar TrustTunnel
sudo systemctl stop trusttunnel
sudo systemctl disable trusttunnel

# Outline y WireGuard no se ven afectados en absoluto
# Son procesos completamente independientes

# Verificar que los otros servicios siguen bien
sudo systemctl status wg-quick@wg0
sudo docker ps | grep outline
```

---

## 12. Archivos a crear / modificar

| Archivo | Acción |
|---------|--------|
| `/opt/trusttunnel/` | CREAR vía script oficial |
| `/etc/systemd/system/trusttunnel.service` | CREAR vía template incluido |
| `infrastructure/vpn_providers/trusttunnel_provider.py` | CREAR |
| `domain/enums/protocol_type.py` | MODIFICAR — agregar `TRUSTTUNNEL` |
| `domain/entities/vpn_key.py` | MODIFICAR — agregar campo `client_id` |
| `application/services/vpn_service.py` | MODIFICAR — registrar provider + restricción de plan |
| `telegram_bot/features/vpn/keyboards.py` | MODIFICAR — agregar botón TrustTunnel |
| `telegram_bot/features/vpn/messages.py` | MODIFICAR — mensaje de clave TrustTunnel |
| `infrastructure/jobs/latency_collector_job.py` | MODIFICAR — agregar `trusttunnel_status` |
| `migrations/versions/XXXX_add_trusttunnel.py` | CREAR — migración Alembic |
| `/etc/nginx/nginx.conf` | MODIFICAR — SNI proxy (si se usa puerto 443) |

---

## 13. Criterios de éxito

- [ ] `systemctl status trusttunnel` muestra `active (running)`
- [ ] El deep-link `tt://` generado por el binario conecta desde un cliente Flutter
- [ ] La conexión pasa tráfico real (navegar, streaming)
- [ ] RAM adicional < 50 MB con 20 usuarios conectados
- [ ] Solo usuarios con Plan Ninja pueden crear claves TrustTunnel
- [ ] El medidor de estado muestra `TrustTunnel ✅`
- [ ] Outline y WireGuard siguen funcionando sin cambios tras la instalación

---

## 14. Notas finales

**Sobre los clientes móviles:** TrustTunnel tiene su propia app Flutter para Android e iOS
(`TrustTunnel/TrustTunnelFlutterClient`). Los usuarios del Plan Ninja la descargarán para
conectarse. Es diferente a la app del cliente de AdGuard VPN comercial — es open source
y específica para servidores self-hosted.

**Sobre la obfuscación:** Es el diferenciador técnico más fuerte de todo tu stack.
Ni Outline ni WireGuard logran esto. TrustTunnel en el puerto 443 con Let's Encrypt
es literalmente indistinguible de visitar `google.com` para cualquier sistema de
inspección de tráfico.

**Sobre el nombre en el bot:** Usar "TrustTunnel" es transparente y profesional.
Alternativamente puedes llamarlo "Protocolo Ninja 🔮" en la UI del bot para
diferenciar el Plan Ninja — queda a tu criterio de marketing.

---

**Fin del documento**
*Siguiente paso al aprobar: invocar writing-plans para el plan de implementación detallado.*
