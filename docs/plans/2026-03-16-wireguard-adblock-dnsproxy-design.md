# Plan de Diseño: AdBlock para WireGuard con dnsproxy + AdGuard DNS
**Fecha:** 16 de Marzo 2026
**Proyecto:** uSipipo VPN — usipipobot
**Estado:** Borrador — pendiente aprobación
**Scope:** Solo WireGuard. Outline NO se ve afectado.

---

## 1. Resumen Ejecutivo

Se integra `AdguardTeam/dnsproxy` como servidor DNS local en el VPS, escuchando exclusivamente en la interfaz `wg0` de WireGuard. El proxy reenvía todas las consultas DNS hacia los servidores de AdGuard (`94.140.14.14 / 94.140.15.15`) que aplican filtrado de anuncios y rastreo en origen. No se instala ningún software adicional de bloqueo: el filtrado lo hace AdGuard en sus servidores, no en el VPS.

**Resultado para el usuario:** Cualquier dispositivo conectado a la clave WireGuard de uSipipo tendrá bloqueo automático de anuncios y rastreadores, sin configuración adicional de su parte.

---

## 2. Por qué dnsproxy y no Pi-hole

| Criterio | Pi-hole | dnsproxy + AdGuard DNS |
|----------|---------|----------------------|
| RAM consumida | ~200-400 MB | ~10-15 MB |
| Interfaz web | Sí (Lighttpd + PHP) | No necesaria |
| Compatible con Outline | ❌ (ya lo rompió antes) | ✅ (solo escucha en wg0) |
| Mantenimiento de listas | Manual / cron | AdGuard lo hace en sus servidores |
| Instalación en VPS | Compleja (Docker anterior) | Binario único, sin dependencias |
| Riesgo de saturar VPS | Alto | Casi nulo |

**Veredicto:** dnsproxy es exactamente lo que se necesita para un VPS de 2GB con múltiples servicios corriendo.

---

## 3. Arquitectura de la solución

```
Cliente con WireGuard (Android / iOS / Desktop)
        │
        │  Túnel cifrado WireGuard (UDP puerto 51820)
        ▼
┌───────────────────────────────────────────────────┐
│                    VPS (2GB RAM)                  │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │  WireGuard daemon (wg0)                     │  │
│  │  Red interna: 10.0.0.1/24                   │  │
│  │  DNS del peer apunta a: 10.0.0.1            │  │
│  └──────────────────┬──────────────────────────┘  │
│                     │  consulta DNS               │
│                     ▼                             │
│  ┌─────────────────────────────────────────────┐  │
│  │  dnsproxy                                   │  │
│  │  Escucha: 10.0.0.1:53                       │  │
│  │  Solo interfaz: wg0                         │  │
│  │  Caché: activado (TTL mínimo 600s)          │  │
│  └──────────────────┬──────────────────────────┘  │
│                     │  reenvío upstream (DoH/53)  │
│                     ▼                             │
└─────────────────────┼─────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
  94.140.14.14:53          94.140.15.15:53
  AdGuard DNS              AdGuard DNS
  (filtra anuncios         (fallback)
   y rastreadores)
```

**Flujo cuando el usuario visita un sitio con anuncios:**
1. El dispositivo pregunta "¿cuál es la IP de ads.doubleclick.net?"
2. La pregunta va cifrada por el túnel WireGuard al VPS
3. dnsproxy recibe la consulta y la reenvía a AdGuard DNS
4. AdGuard DNS reconoce el dominio como publicitario → responde `0.0.0.0`
5. dnsproxy cachea la respuesta y la devuelve al cliente
6. El cliente no puede conectarse al servidor de anuncios → el anuncio no carga

---

## 4. Componentes técnicos

### 4.1 dnsproxy (binario Go — sin Docker)

Se instala el binario precompilado directamente en el VPS. No requiere Docker, no requiere Go instalado, no requiere dependencias.

```bash
# Descargar la última versión del binario para Linux amd64
DNSPROXY_VERSION=$(curl -s https://api.github.com/repos/AdguardTeam/dnsproxy/releases/latest \
  | grep tag_name | cut -d '"' -f 4)

wget "https://github.com/AdguardTeam/dnsproxy/releases/download/${DNSPROXY_VERSION}/dnsproxy-linux-amd64-${DNSPROXY_VERSION}.tar.gz" \
  -O /tmp/dnsproxy.tar.gz

tar -xzf /tmp/dnsproxy.tar.gz -C /tmp/
sudo mv /tmp/linux-amd64/dnsproxy /usr/local/bin/dnsproxy
sudo chmod +x /usr/local/bin/dnsproxy

# Verificar instalación
dnsproxy --version
```

### 4.2 Configuración de dnsproxy

```bash
# Crear directorio de configuración
sudo mkdir -p /etc/dnsproxy
sudo mkdir -p /var/log/usipipo
```

Archivo de configuración `/etc/dnsproxy/config.yaml`:

```yaml
# /etc/dnsproxy/config.yaml
# DNS proxy para WireGuard + AdBlock uSipipo

# Escuchar solo en la interfaz WireGuard
listen-addrs:
  - 10.0.0.1

# Puerto DNS estándar
listen-ports:
  - 53

# Servidores upstream: AdGuard DNS con filtrado de anuncios
upstreams:
  - 94.140.14.14:53          # AdGuard DNS primario (con adblock)
  - 94.140.15.15:53          # AdGuard DNS secundario (con adblock)
  - https://dns.adguard-dns.com/dns-query  # AdGuard DoH (fallback cifrado)

# Bootstrap DNS para resolver el hostname de AdGuard DoH
bootstrap:
  - 1.1.1.1:53
  - 8.8.8.8:53

# Caché DNS: reduce latencia y consultas externas
cache: true
cache-min-ttl: 600      # Mínimo 10 minutos en caché
cache-max-ttl: 86400    # Máximo 24 horas
cache-size: 4096        # Máximo 4096 entradas

# Rate limiting (protege contra abuso)
ratelimit: 20           # 20 requests/segundo por IP

# Rechazar peticiones tipo ANY (evita amplification attacks)
refuse-any: true

# Log reducido (no saturar disco)
verbose: false
```

### 4.3 Servicio systemd para dnsproxy

Archivo `/etc/systemd/system/dnsproxy.service`:

```ini
[Unit]
Description=AdGuard dnsproxy - DNS proxy with adblock for WireGuard
Documentation=https://github.com/AdguardTeam/dnsproxy
After=network-online.target wg-quick@wg0.service
Requires=network-online.target
Wants=wg-quick@wg0.service

[Service]
Type=simple
User=nobody
Group=nogroup

# Binario con config en archivo YAML
ExecStart=/usr/local/bin/dnsproxy \
  --config-path=/etc/dnsproxy/config.yaml \
  --log-file=/var/log/usipipo/dnsproxy.log

# Reinicio automático si falla
Restart=on-failure
RestartSec=5s

# Hardening de seguridad
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/log/usipipo

# Capacidad de bind en puerto 53 sin ser root
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```

```bash
# Activar e iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl enable dnsproxy
sudo systemctl start dnsproxy
sudo systemctl status dnsproxy
```

### 4.4 Modificación de la configuración WireGuard

En el archivo `/etc/wireguard/wg0.conf`, agregar la línea DNS en la sección `[Interface]`:

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>

# AGREGAR ESTA LÍNEA:
# El servidor mismo resuelve DNS vía dnsproxy con adblock
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PreDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Cada peer recibe el DNS del servidor WireGuard
# Esto va en la configuración del CLIENTE que se le entrega al usuario:
# DNS = 10.0.0.1
```

**Importante:** El campo `DNS = 10.0.0.1` va en la config del **cliente** (el archivo `.conf` que se le entrega al usuario o el QR code), no en el servidor. Cuando el bot genera una nueva clave WireGuard, ese campo ya debe estar incluido.

---

## 5. Cambios en el código de usipipobot

### 5.1 Actualizar el template de generación de claves WireGuard

El bot genera configuraciones WireGuard para los clientes. El template debe incluir el DNS:

```python
# infrastructure/vpn_providers/wireguard_provider.py

WIREGUARD_CLIENT_TEMPLATE = """[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}/32
DNS = 10.0.0.1          # AdGuard AdBlock DNS — uSipipo

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_ip}:{server_port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
```

Si el template ya existe con otro DNS (ej: `1.1.1.1` o `8.8.8.8`), cambiarlo a `10.0.0.1`.

### 5.2 Agregar campo `adblock_enabled` en la entidad VpnKey

```python
# domain/entities/vpn_key.py

@dataclass
class VpnKey:
    id: Optional[int] = None
    user_id: int = None
    protocol_type: str = "outline"   # "outline" | "wireguard"
    key_name: str = ""
    access_url: str = ""
    data_limit_bytes: int = 0
    is_premium: bool = False
    adblock_enabled: bool = False     # NUEVO: True si es WireGuard con dnsproxy activo
    created_at: datetime = None
    expires_at: datetime = None
```

### 5.3 Mensaje al usuario al crear clave WireGuard

```python
# telegram_bot/features/vpn/messages.py

def wireguard_key_created_message(key: VpnKey) -> str:
    adblock_status = "🛡️ AdBlock: ACTIVO" if key.adblock_enabled else ""

    return f"""
✅ *Clave WireGuard creada*

🔑 Nombre: `{key.key_name}`
📡 Protocolo: WireGuard
{adblock_status}
🌐 Servidor: EE.UU (US-East)

━━━━━━━━━━━━━━━━
📲 *Cómo conectarte:*
1. Descarga WireGuard desde tu tienda de apps
2. Importa el archivo de configuración o escanea el QR
3. Activa el túnel

🛡️ *Incluye bloqueo de:*
├─ Anuncios (Google Ads, Facebook Ads, etc.)
├─ Rastreadores (analytics, pixels)
└─ Dominios de malware conocidos
━━━━━━━━━━━━━━━━
⚠️ El bloqueo de anuncios funciona a nivel DNS.
Algunos anuncios integrados en apps nativas pueden no bloquearse.
"""
```

---

## 6. Migración de claves WireGuard existentes

Los usuarios que ya tienen claves WireGuard activas necesitan regenerar su configuración para obtener `DNS = 10.0.0.1`. Hay dos opciones:

**Opción A — Notificación opcional (recomendada):**
Enviar mensaje a usuarios con claves WireGuard existentes informando que pueden regenerar su clave para obtener AdBlock. La clave existente sigue funcionando, solo que sin AdBlock hasta que regeneren.

**Opción B — Migración forzada:**
No recomendada. Forzar regeneración rompe la experiencia de usuario.

```python
# Mensaje de notificación (enviar una sola vez via job)
ADBLOCK_MIGRATION_MESSAGE = """
🆕 *Nueva función: AdBlock en WireGuard*

Tus claves WireGuard ahora pueden incluir bloqueo de anuncios automático.

Para activarlo, regenera tu clave desde el menú:
📱 Mis Claves → [nombre de clave] → Regenerar

La nueva clave incluirá:
🛡️ Bloqueo de anuncios
🛡️ Bloqueo de rastreadores

Tu clave actual sigue funcionando normalmente.
"""
```

---

## 7. Compatibilidad con Outline

Outline no se ve afectado porque:

- dnsproxy escucha **solo en `10.0.0.1`** (IP interna de WireGuard)
- Outline usa su propio mecanismo de proxy SOCKS5/HTTP con DNS interno
- No hay ningún cambio en la configuración de `iptables` para el tráfico de Outline
- Los dos protocolos comparten el VPS pero usan rutas de red completamente distintas

Para verificar que no hay conflicto después de la instalación:

```bash
# Verificar que dnsproxy solo escucha en la IP de WireGuard
ss -ulnp | grep :53
# Debe mostrar solo 10.0.0.1:53, NO 0.0.0.0:53

# Verificar que Outline sigue respondiendo
curl -sk https://localhost:443/access-keys | head -c 100
```

---

## 8. Firewall: reglas iptables

Asegurarse de que el tráfico DNS desde los peers WireGuard llega al dnsproxy y no sale hacia afuera sin pasar por él:

```bash
# Permitir DNS desde la red WireGuard hacia dnsproxy local
sudo iptables -A INPUT -i wg0 -p udp --dport 53 -j ACCEPT
sudo iptables -A INPUT -i wg0 -p tcp --dport 53 -j ACCEPT

# Bloquear DNS directo hacia servidores externos desde peers WireGuard
# (fuerza todo DNS a pasar por dnsproxy — evita bypass del adblock)
sudo iptables -A FORWARD -i wg0 -p udp --dport 53 ! -d 10.0.0.1 -j DROP
sudo iptables -A FORWARD -i wg0 -p tcp --dport 53 ! -d 10.0.0.1 -j DROP

# Guardar reglas para persistencia
sudo netfilter-persistent save
```

---

## 9. Monitoreo y verificación

### 9.1 Verificar que el adblock funciona

```bash
# Desde el VPS, simular una consulta de un dominio de anuncios
dig @10.0.0.1 ads.google.com
# Debe responder: 0.0.0.0 (bloqueado)

# Verificar un dominio legítimo
dig @10.0.0.1 google.com
# Debe responder: IP real de Google

# Ver logs de dnsproxy
tail -f /var/log/usipipo/dnsproxy.log

# Verificar consumo de RAM (debe ser < 20MB)
ps aux | grep dnsproxy | grep -v grep
```

### 9.2 Verificar funcionamiento del servicio

```bash
# Estado del servicio
sudo systemctl status dnsproxy

# Ver si está escuchando correctamente
ss -ulnp | grep dnsproxy

# Reiniciar si es necesario
sudo systemctl restart dnsproxy
```

### 9.3 Agregar al medidor de latencia (Plan 3)

Agregar el estado de dnsproxy al `ServerStats`:

```python
# infrastructure/jobs/latency_collector_job.py

@dataclass
class ServerStats:
    ...
    dnsproxy_status: bool = False   # True = UP
    adblock_active: bool = False    # True = dnsproxy respondiendo correctamente

async def collect_server_stats() -> ServerStats:
    ...
    # Verificar dnsproxy
    dnsproxy_up = _check_service("dnsproxy")

    # Test funcional: resolver un dominio de anuncios
    # Si responde 0.0.0.0 → adblock activo
    adblock_ok = await _test_adblock_dns("10.0.0.1", "ads.google.com")

    return ServerStats(
        ...
        dnsproxy_status=dnsproxy_up,
        adblock_active=adblock_ok,
    )
```

Y actualizar el mensaje de estado:

```
📡 Estado del Servidor

🟢 Estado: Excelente

⚡ Latencia: 23ms
🖥️ CPU:      42%
💾 RAM:      61%

Protocolos:
✅ Outline
✅ WireGuard
🛡️ AdBlock DNS: ACTIVO

Actualizado: hace 45s
```

---

## 10. Consideraciones de privacidad para los usuarios

AdGuard DNS es un servicio de terceros. Las consultas DNS de los usuarios pasan por los servidores de AdGuard Team. Esto hay que comunicarlo honestamente:

```
🛡️ Sobre el AdBlock de uSipipo

Tu VPN cifra TODO tu tráfico de navegación.
Para el bloqueo de anuncios usamos AdGuard DNS,
un servicio de terceros reconocido.

AdGuard DNS ve: qué dominios consultas (no el contenido)
AdGuard Team: empresa con sede en Chipre, política de no-logs.

Si prefieres sin AdBlock: contacta soporte para una
clave WireGuard con DNS neutro (1.1.1.1).
```

---

## 11. Posible problema: Compatibilidad con systemd-resolved

En Ubuntu/Debian reciente, `systemd-resolved` ocupa el puerto 53 en `127.0.0.53`. Como dnsproxy escucha en `10.0.0.1:53` (no en `127.0.0.1`), no hay conflicto directo. Pero verificar:

```bash
# Ver qué ocupa el puerto 53
ss -ulnp | grep :53

# Si systemd-resolved ocupa 0.0.0.0:53 (raro pero posible):
sudo systemctl disable systemd-resolved
sudo systemctl stop systemd-resolved

# Y crear un resolv.conf manual
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf
```

---

## 12. Plan de rollback

Si algo sale mal, revertir es trivial:

```bash
# 1. Detener dnsproxy
sudo systemctl stop dnsproxy
sudo systemctl disable dnsproxy

# 2. Restaurar DNS en wg0.conf (volver a 1.1.1.1 o el DNS anterior)
# Editar los templates de generación de claves en el bot

# 3. Verificar que WireGuard sigue funcionando
sudo wg show
```

Outline nunca se vio afectado, por lo que no necesita rollback.

---

## 13. Resumen de archivos modificados/creados

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `/usr/local/bin/dnsproxy` | CREAR | Binario descargado de GitHub releases |
| `/etc/dnsproxy/config.yaml` | CREAR | Configuración del proxy DNS |
| `/etc/systemd/system/dnsproxy.service` | CREAR | Servicio systemd |
| `/etc/wireguard/wg0.conf` | MODIFICAR | Sin cambios directos — solo los templates del bot |
| `infrastructure/vpn_providers/wireguard_provider.py` | MODIFICAR | Agregar `DNS = 10.0.0.1` en el template de config cliente |
| `domain/entities/vpn_key.py` | MODIFICAR | Agregar campo `adblock_enabled: bool` |
| `telegram_bot/features/vpn/messages.py` | MODIFICAR | Mensaje de creación de clave con info de AdBlock |
| `infrastructure/jobs/latency_collector_job.py` | MODIFICAR | Agregar `dnsproxy_status` al `ServerStats` |

---

## 14. Estimación de esfuerzo

| Tarea | Tiempo estimado |
|-------|----------------|
| Instalar dnsproxy en VPS + systemd | 30 minutos |
| Verificar compatibilidad con Outline + iptables | 20 minutos |
| Actualizar template de claves en wireguard_provider.py | 15 minutos |
| Actualizar mensajes del bot | 15 minutos |
| Testing end-to-end (conexión real + dig) | 30 minutos |
| **Total** | **~2 horas** |

---

## 15. Criterios de éxito

- [ ] `dig @10.0.0.1 ads.google.com` responde `0.0.0.0`
- [ ] `dig @10.0.0.1 google.com` responde la IP real de Google
- [ ] Outline sigue generando y entregando claves normalmente
- [ ] dnsproxy consume menos de 20MB de RAM
- [ ] Nuevas claves WireGuard generadas por el bot incluyen `DNS = 10.0.0.1`
- [ ] El medidor de estado del servidor muestra `AdBlock: ACTIVO`
- [ ] CPU del VPS no aumenta más de 2% en idle

---

**Fin del documento**
*Próximo paso: invocar writing-plans para crear el plan de implementación detallado.*
