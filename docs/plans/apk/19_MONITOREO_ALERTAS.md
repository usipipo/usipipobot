# Plan de Monitoreo y Alertas Tempranas

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Contexto:** Single VPS con todos los servicios
> **Objetivo:** Detectar y responder a incidentes en <5 minutos

---

## 🎯 Estrategia de Monitoreo

### Filosofía
> **"Mejor prevenir que curar. Alertar solo lo importante. Automatizar la respuesta."**

### Principios
1. **Alertas accionables:** Si no hay acción que tomar, no es una alerta
2. **Multi-canal:** Telegram para crítico, email para informativo
3. **Auto-curación:** Si se puede automatizar la respuesta, hacerlo
4. **Sin ruido:** Alert fatigue es real, minimizar falsos positivos

---

## 📊 Nivel 1: Monitoreo de Servicios (Systemd)

### Script de Health Check por Servicio

**Archivo: `/opt/usipipobot/scripts/service_health_check.sh`**

```bash
#!/bin/bash
# Verificar que todos los servicios críticos estén activos

set -e

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"🚨 SERVICIO CRÍTICO:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
}

check_service() {
    local service=$1
    local display_name=$2

    if ! systemctl is-active --quiet "$service"; then
        alert "❌ <b>$display_name</b> está INACTIVO\\n\\nIntentando reiniciar..."

        # Intentar reiniciar automáticamente
        if sudo systemctl restart "$service"; then
            alert "✅ <b>$display_name</b> reiniciado exitosamente"
        else
            alert "❌❌ <b>$display_name</b> NO pudo reiniciarse\\n\\n⚠️ INTERVENCIÓN MANUAL REQUERIDA"
        fi
        return 1
    fi
    return 0
}

# Verificar todos los servicios críticos
echo "Verificando servicios..."

check_service "postgresql" "PostgreSQL" || true
check_service "redis" "Redis" || true
check_service "caddy" "Caddy (HTTPS)" || true
check_service "usipipo-backend" "Backend FastAPI" || true
check_service "usipipo-bot" "Bot de Telegram" || true
check_service "wg-quick@wg0" "WireGuard VPN" || true
check_service "outline-server" "Outline VPN" || true

echo "Health check completado"
```

**Cron (cada 2 minutos):**
```bash
sudo crontab -e

# Agregar:
*/2 * * * * /opt/usipipobot/scripts/service_health_check.sh >> /var/log/usipipo/service_health.log 2>&1
```

---

## 📈 Nivel 2: Monitoreo de Recursos del VPS

### Script de Monitoreo de Recursos

**Archivo: `/opt/usipipobot/scripts/resource_monitor.sh`**

```bash
#!/bin/bash
# Monitoreo de recursos del VPS con alertas inteligentes

set -e

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"
LOG_FILE="/var/log/usipipo/resource_monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    local level="$1"
    local message="$2"
    local emoji=""

    case $level in
        "CRITICAL") emoji="🚨" ;;
        "WARNING") emoji="⚠️" ;;
        "INFO") emoji="ℹ️" ;;
    esac

    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"${emoji} <b>${level}</b>\\n\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"

    log "${level}: ${message}"
}

# =============================================================================
# MONITOREO DE RAM
# =============================================================================

RAM_TOTAL=$(free -m | grep Mem | awk '{print $2}')
RAM_USED=$(free -m | grep Mem | awk '{print $3}')
RAM_AVAILABLE=$(free -m | grep Mem | awk '{print $7}')
RAM_PERCENT=$((RAM_USED * 100 / RAM_TOTAL))

log "RAM: ${RAM_USED}MB/${RAM_TOTAL}MB (${RAM_PERCENT}%) - Disponible: ${RAM_AVAILABLE}MB"

if [ "$RAM_PERCENT" -gt 95 ]; then
    alert "CRITICAL" "Uso de RAM CRÍTICO: ${RAM_PERCENT}%\\n\\nUsada: ${RAM_USED}MB\\nTotal: ${RAM_TOTAL}MB\\nDisponible: ${RAM_AVAILABLE}MB\\n\\n⚠️ El sistema puede colapsar en cualquier momento."
elif [ "$RAM_PERCENT" -gt 85 ]; then
    alert "WARNING" "Uso de RAM ALTO: ${RAM_PERCENT}%\\n\\nUsada: ${RAM_USED}MB\\nTotal: ${RAM_TOTAL}MB\\nDisponible: ${RAM_AVAILABLE}MB"
fi

# =============================================================================
# MONITOREO DE DISCO
# =============================================================================

DISK_TOTAL=$(df -m / | awk 'NR==2 {print $2}')
DISK_USED=$(df -m / | awk 'NR==2 {print $3}')
DISK_AVAILABLE=$(df -m / | awk 'NR==2 {print $4}')
DISK_PERCENT=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

log "Disco: ${DISK_USED}MB/${DISK_TOTAL}MB (${DISK_PERCENT}%) - Disponible: ${DISK_AVAILABLE}MB"

if [ "$DISK_PERCENT" -gt 95 ]; then
    alert "CRITICAL" "Espacio en disco CRÍTICO: ${DISK_PERCENT}%\\n\\nUsado: ${DISK_USED}MB\\nTotal: ${DISK_TOTAL}MB\\nDisponible: ${DISK_AVAILABLE}MB\\n\\n⚠️ El sistema puede dejar de funcionar."
elif [ "$DISK_PERCENT" -gt 85 ]; then
    alert "WARNING" "Espacio en disco ALTO: ${DISK_PERCENT}%\\n\\nUsado: ${DISK_USED}MB\\nTotal: ${DISK_TOTAL}MB\\nDisponible: ${DISK_AVAILABLE}MB"
fi

# =============================================================================
# MONITOREO DE CPU
# =============================================================================

# Obtener carga promedio (load average)
LOAD_1MIN=$(cat /proc/loadavg | awk '{print $1}')
CPU_CORES=$(nproc)
LOAD_PERCENT=$(echo "scale=0; $LOAD_1MIN * 100 / $CPU_CORES" | bc)

log "CPU Load: ${LOAD_1MIN} (${LOAD_PERCENT}% de ${CPU_CORES} cores)"

if [ "$LOAD_PERCENT" -gt 90 ]; then
    alert "CRITICAL" "CPU CRÍTICO: ${LOAD_PERCENT}%\\n\\nLoad (1min): ${LOAD_1MIN}\\nCores: ${CPU_CORES}\\n\\n⚠️ El sistema está sobrecargado."
elif [ "$LOAD_PERCENT" -gt 70 ]; then
    alert "WARNING" "CPU ALTO: ${LOAD_PERCENT}%\\n\\nLoad (1min): ${LOAD_1MIN}\\nCores: ${CPU_CORES}"
fi

# =============================================================================
# MONITOREO DE RED (ancho de banda)
# =============================================================================

# Obtener interfaz de red principal
INTERFACE=$(ip route | grep default | awk '{print $5}')

if [ -n "$INTERFACE" ]; then
    # RX/TX bytes
    RX_BYTES=$(cat /sys/class/net/$INTERFACE/statistics/rx_bytes)
    TX_BYTES=$(cat /sys/class/net/$INTERFACE/statistics/tx_bytes)

    # Convertir a MB
    RX_MB=$((RX_BYTES / 1024 / 1024))
    TX_MB=$((TX_BYTES / 1024 / 1024))

    log "Red ($INTERFACE): RX=${RX_MB}MB TX=${TX_MB}MB"
fi

# =============================================================================
# MONITOREO DE TEMPERATURA (si está disponible)
# =============================================================================

if command -v vcgencmd &> /dev/null; then
    # Raspberry Pi
    TEMP=$(vcgencmd measure_temp | cut -d"'" -f2)
    log "Temperatura: ${TEMP}"

    TEMP_NUM=$(echo "$TEMP" | cut -d"." -f1)
    if [ "$TEMP_NUM" -gt 80 ]; then
        alert "WARNING" "Temperatura ALTA: ${TEMP}\\n\\n⚠️ Considerar mejorar ventilación."
    fi
fi

log "=== Monitoreo completado ==="
```

**Cron (cada 5 minutos):**
```bash
*/5 * * * * /opt/usipipobot/scripts/resource_monitor.sh >> /var/log/usipipo/resource_monitor.log 2>&1
```

---

## 🔍 Nivel 3: Monitoreo de Aplicación

### Endpoint de Health del Backend

**Archivo: `infrastructure/api/routes_health.py`**

```python
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import text
import redis.asyncio as redis
import time
import aiohttp
from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check completo del backend.
    Retorna 200 si todo está sano, 503 si hay problemas.
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "latency_ms": 0,
        "checks": {}
    }

    # Check 1: PostgreSQL
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        health_status["checks"]["postgresql"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }
    except Exception as e:
        health_status["checks"]["postgresql"] = {"status": "error", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check 2: Redis
    try:
        r = redis.Redis()
        await r.ping()
        await r.close()
        health_status["checks"]["redis"] = {"status": "ok"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "error", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check 3: Outline API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.outline_api_url}/server",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    health_status["checks"]["outline"] = {"status": "ok"}
                else:
                    health_status["checks"]["outline"] = {
                        "status": "degraded",
                        "http_status": resp.status
                    }
    except Exception as e:
        health_status["checks"]["outline"] = {"status": "error", "error": str(e)}
        # Outline down no hace unhealthy al backend completo

    # Check 4: WireGuard (verificar interfaz)
    try:
        import subprocess
        result = subprocess.run(
            ["wg", "show"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            health_status["checks"]["wireguard"] = {"status": "ok"}
        else:
            health_status["checks"]["wireguard"] = {"status": "error"}
    except Exception as e:
        health_status["checks"]["wireguard"] = {"status": "error", "error": str(e)}

    # Calcular latencia total
    health_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)

    # Determinar status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(status_code=status_code, content=health_status)


@router.get("/health/live")
async def liveness_probe():
    """
    Liveness probe para Kubernetes/systemd.
    Solo verifica que el proceso esté corriendo.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe.
    Verifica que el backend esté listo para recibir tráfico.
    """
    # Verificar DB y Redis
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))

        r = redis.Redis()
        await r.ping()
        await r.close()

        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Not ready: {str(e)}"
        )
```

---

### Script de Monitoreo del Backend

**Archivo: `/opt/usipipobot/scripts/backend_monitor.sh`**

```bash
#!/bin/bash
# Monitoreo específico del backend FastAPI

set -e

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"
BACKEND_URL="http://localhost:8000"
LOG_FILE="/var/log/usipipo/backend_monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"🚨 BACKEND:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
    log "ALERT: $message"
}

# =============================================================================
# HEALTH CHECK DEL BACKEND
# =============================================================================

log "Verificando health del backend..."

# Intentar health check
RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "000" ]; then
    alert "❌ Backend NO RESPONDE en ${BACKEND_URL}\\n\\n⚠️ El proceso puede estar colgado o caído.\\n\\nIntentando reiniciar..."

    # Intentar reiniciar
    if sudo systemctl restart usipipo-backend; then
        alert "✅ Backend reiniciado"

        # Verificar que levantó
        sleep 5
        RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo -e "\n000")
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

        if [ "$HTTP_CODE" = "200" ]; then
            alert "✅ Backend levantó correctamente"
        else
            alert "❌ Backend reinició pero no responde correctamente (HTTP $HTTP_CODE)"
        fi
    else
        alert "❌❌ NO se pudo reiniciar el backend\\n\\n⚠️ INTERVENCIÓN MANUAL REQUERIDA"
    fi

elif [ "$HTTP_CODE" = "200" ]; then
    log "✅ Backend saludable (HTTP 200)"

    # Extraer latencia del response
    LATENCY=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('latency_ms', 'N/A'))" 2>/dev/null || echo "N/A")
    log "Latencia: ${LATENCY}ms"

    # Alertar si la latencia es muy alta
    if [ "$LATENCY" != "N/A" ]; then
        LATENCY_INT=${LATENCY%.*}
        if [ "$LATENCY_INT" -gt 500 ]; then
            alert "⚠️ Latencia ALTA: ${LATENCY}ms\\n\\nEl backend está respondiendo pero muy lento."
        fi
    fi

elif [ "$HTTP_CODE" = "503" ]; then
    alert "⚠️ Backend responde pero NO está saludable (HTTP 503)\\n\\n${BODY}"
else
    alert "⚠️ Backend responde con HTTP $HTTP_CODE (esperado 200)"
fi

# =============================================================================
# MONITOREO DE PROCESOS
# =============================================================================

# Verificar que el proceso de Uvicorn esté corriendo
UVICORN_COUNT=$(pgrep -f "uvicorn.*infrastructure.api.server" | wc -l || echo "0")
log "Procesos Uvicorn activos: $UVICORN_COUNT"

if [ "$UVICORN_COUNT" -lt 1 ]; then
    alert "❌ No hay procesos Uvicorn corriendo\\n\\nEl backend no está en ejecución."
fi

log "=== Backend monitor completado ==="
```

**Cron (cada 2 minutos):**
```bash
*/2 * * * * /opt/usipipobot/scripts/backend_monitor.sh >> /var/log/usipipo/backend_monitor.log 2>&1
```

---

## 📱 Nivel 4: Monitoreo de VPN

### Script de Monitoreo de WireGuard

**Archivo: `/opt/usipipobot/scripts/wireguard_monitor.sh`**

```bash
#!/bin/bash
# Monitoreo de WireGuard VPN

set -e

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"
LOG_FILE="/var/log/usipipo/wg_monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"🔵 WireGuard:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
    log "ALERT: $message"
}

log "=== WireGuard Monitor ==="

# Verificar que la interfaz wg0 existe
if ! ip link show wg0 &>/dev/null; then
    alert "❌ Interfaz wg0 NO existe\\n\\nWireGuard no está funcionando."
    exit 1
fi

# Verificar que el proceso wg-quick está activo
if ! systemctl is-active --quiet wg-quick@wg0; then
    alert "❌ wg-quick@wg0 NO está activo\\n\\nIntentando reiniciar..."

    if sudo systemctl restart wg-quick@wg0; then
        alert "✅ WireGuard reiniciado"
    else
        alert "❌❌ NO se pudo reiniciar WireGuard"
    fi
fi

# Obtener estadísticas de WireGuard
WG_STATS=$(wg show wg0 2>/dev/null || echo "")

if [ -z "$WG_STATS" ]; then
    alert "⚠️ wg show no retorna datos\\n\\nWireGuard puede estar en estado inconsistente."
else
    # Contar peers conectados
    PEER_COUNT=$(echo "$WG_STATS" | grep -c "peer:" || echo "0")
    log "Peers conectados: $PEER_COUNT"

    # Obtener última handshake de cada peer
    LAST_HANDSHAKE=$(wg show wg0 latest-handshakes 2>/dev/null || echo "")

    # Verificar peers sin handshake reciente (> 10 minutos)
    # Esto requiere parsing más complejo, simplificado para el ejemplo
fi

log "=== WireGuard monitor completado ==="
```

### Script de Monitoreo de Outline

**Archivo: `/opt/usipipobot/scripts/outline_monitor.sh`**

```bash
#!/bin/bash
# Monitoreo de Outline VPN Server

set -e

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"
OUTLINE_API_URL="${OUTLINE_API_URL:-http://localhost:8080}"
LOG_FILE="/var/log/usipipo/outline_monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"🟠 Outline:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
    log "ALERT: $message"
}

log "=== Outline Monitor ==="

# Verificar que el servicio Outline está activo
if ! systemctl is-active --quiet outline-server; then
    alert "❌ outline-server NO está activo\\n\\nIntentando reiniciar..."

    if sudo systemctl restart outline-server; then
        alert "✅ Outline reiniciado"
    else
        alert "❌❌ NO se pudo reiniciar Outline"
    fi
fi

# Verificar API de Outline
RESPONSE=$(curl -s -w "\n%{http_code}" "${OUTLINE_API_URL}/server" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    log "✅ Outline API saludable"

    # Extraer información del servidor
    BODY=$(echo "$RESPONSE" | head -n -1)
    SERVER_NAME=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', 'N/A'))" 2>/dev/null || echo "N/A")
    log "Server: $SERVER_NAME"

elif [ "$HTTP_CODE" = "000" ]; then
    alert "❌ Outline API NO responde en ${OUTLINE_API_URL}"
else
    alert "⚠️ Outline API responde con HTTP $HTTP_CODE"
fi

log "=== Outline monitor completado ==="
```

---

## 📊 Nivel 5: Dashboard de Monitoreo (Web)

### Dashboard Ligero con FastAPI

**Archivo: `infrastructure/api/routes_monitoring.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text, func
import psutil
import subprocess
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/monitoring/dashboard")
async def monitoring_dashboard():
    """
    Dashboard completo de monitoreo para el admin.
    """
    # Información del sistema
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Información de procesos
    backend_process = None
    bot_process = None

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent', 'cpu_percent']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'uvicorn' in cmdline and 'infrastructure.api.server' in cmdline:
                backend_process = {
                    'pid': proc.info['pid'],
                    'memory_percent': proc.info['memory_percent'],
                    'cpu_percent': proc.info['cpu_percent'],
                }
            if 'python' in cmdline and 'main.py' in cmdline:
                bot_process = {
                    'pid': proc.info['pid'],
                    'memory_percent': proc.info['memory_percent'],
                    'cpu_percent': proc.info['cpu_percent'],
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Estadísticas de la base de datos
    async with get_session() as session:
        # Usuarios totales y activos
        result = await session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as new_24h
            FROM users
        """))
        user_stats = result.first()

        # Claves VPN activas
        result = await session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_active = true) as active,
                SUM(used_bytes) as total_used_bytes
            FROM vpn_keys
        """))
        key_stats = result.first()

        # Paquetes activos
        result = await session.execute(text("""
            SELECT
                COUNT(*) as active_packages,
                SUM(stars_paid) as total_stars
            FROM data_packages
            WHERE is_active = true
        """))
        package_stats = result.first()

    # Estado de servicios (systemctl)
    services = {}
    for service in ['postgresql', 'redis', 'caddy', 'usipipo-backend', 'usipipo-bot', 'wg-quick@wg0', 'outline-server']:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True,
                timeout=5
            )
            services[service] = result.stdout.strip()
        except Exception as e:
            services[service] = f"error: {str(e)}"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_mb": memory.total / 1024 / 1024,
                "used_mb": memory.used / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": disk.percent,
            },
        },
        "processes": {
            "backend": backend_process,
            "bot": bot_process,
        },
        "database": {
            "users": {
                "total": user_stats[0],
                "active": user_stats[1],
                "new_24h": user_stats[2],
            },
            "vpn_keys": {
                "total": key_stats[0],
                "active": key_stats[1],
                "total_used_bytes": key_stats[2],
            },
            "packages": {
                "active": package_stats[0],
                "total_stars": package_stats[1],
            },
        },
        "services": services,
    }


@router.get("/monitoring/alerts/history")
async def alerts_history(hours: int = 24):
    """
    Historial de alertas de las últimas X horas.
    """
    # Esto requeriría una tabla de alerts en la DB
    # Por ahora, leer de logs
    import re

    alerts = []
    log_files = [
        '/var/log/usipipo/service_health.log',
        '/var/log/usipipo/resource_monitor.log',
        '/var/log/usipipo/backend_monitor.log',
    ]

    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if 'ALERT' in line or 'CRITICAL' in line or 'WARNING' in line:
                        # Parsear línea del log
                        match = re.match(r'\[(.*?)\] (.*?): (.*)', line)
                        if match:
                            alerts.append({
                                'timestamp': match.group(1),
                                'level': match.group(2),
                                'message': match.group(3),
                                'source': log_file,
                            })
        except FileNotFoundError:
            pass

    # Ordenar por timestamp (más reciente primero)
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)

    # Limitar a últimas 100 alertas
    return {"alerts": alerts[:100]}
```

---

## 🚨 Matriz de Alertas

| Alerta | Nivel | Canal | Acción Automática | Acción Manual |
|--------|-------|-------|-------------------|---------------|
| Servicio inactivo | CRÍTICO | Telegram | Intentar restart | Si falla restart |
| RAM > 95% | CRÍTICO | Telegram | Limpieza de caché | Identificar proceso |
| Disco > 95% | CRÍTICO | Telegram | Limpieza de logs | Liberar espacio |
| CPU > 90% | WARNING | Telegram | - | Identificar causa |
| Backend latency > 500ms | WARNING | Telegram | - | Investigar slow queries |
| PostgreSQL down | CRÍTICO | Telegram | Intentar restart | Verificar DB |
| Redis down | WARNING | Telegram | Intentar restart | Verificar Redis |
| WireGuard down | CRÍTICO | Telegram | Intentar restart | Verificar config |
| Outline down | CRÍTICO | Telegram | Intentar restart | Verificar Outline |
| Rate limit excedido | INFO | - | Auto-bloqueo | Revisar logs |
| Múltiples IPs baneadas | WARNING | Telegram | - | Investigar ataque |

---

## ✅ Checklist de Implementación

### Día 1-2: Monitoreo de Servicios
- [ ] Implementar service_health_check.sh
- [ ] Configurar cron cada 2 minutos
- [ ] Probar alertas de Telegram
- [ ] Verificar auto-restart de servicios

### Día 3-4: Monitoreo de Recursos
- [ ] Implementar resource_monitor.sh
- [ ] Configurar umbrales de alerta
- [ ] Probar alertas de RAM, disco, CPU
- [ ] Ajustar thresholds según el VPS

### Día 5-6: Monitoreo de Aplicación
- [ ] Implementar endpoints de health
- [ ] Implementar backend_monitor.sh
- [ ] Configurar alertas de latencia
- [ ] Probar detección de backend caído

### Día 7-8: Monitoreo de VPN
- [ ] Implementar wireguard_monitor.sh
- [ ] Implementar outline_monitor.sh
- [ ] Configurar alertas de VPN
- [ ] Probar detección de VPN caída

### Día 9-10: Dashboard
- [ ] Implementar dashboard de monitoreo
- [ ] Agregar historial de alertas
- [ ] Proteger endpoint con autenticación
- [ ] Probar dashboard en producción

---

## 🎯 Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| Tiempo de detección de incidentes | <2 minutos |
| Falsos positivos por día | <1 |
| Alertas accionables | 100% |
| Auto-curación exitosa | >80% |
| Tiempo de respuesta manual | <30 minutos |

---

*Documento versión 1.0 - Fecha: Marzo 2026*
