# Plan Maestro: Infraestructura Unificada de Alto Rendimiento

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Contexto:** Single VPS hosting todo el ecosistema uSipipo
> **Objetivo:** Máximo rendimiento, seguridad y estabilidad para 500-1000 usuarios en un solo servidor

---

## 🎯 Contexto Actual

### Infraestructura Existente
```
┌─────────────────────────────────────────────────────────────┐
│                    VPS ÚNICO (2GB RAM)                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  SERVIDORES VPN (Alto Consumo)                        │ │
│  │  - WireGuard Server (wg0)                             │ │
│  │  - Outline Server (Shadowsocks)                       │ │
│  │  - Consumo RAM: ~400-600MB                            │ │
│  │  - CPU: Variable según tráfico VPN                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  BACKEND FastAPI + Bot Telegram                       │ │
│  │  - python-telegram-bot (async)                        │ │
│  │  - FastAPI (uvicorn)                                  │ │
│  │  - Background jobs (cleanup, sync, expire)            │ │
│  │  - Consumo RAM: ~300-500MB                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  BASE DE DATOS PostgreSQL                             │ │
│  │  - PostgreSQL 15+ local                               │ │
│  │  - Consumo RAM: ~200-400MB (shared_buffers)           │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  REDIS (Caché + Rate Limiting + OTP)                  │ │
│  │  - Consumo RAM: ~50-100MB                             │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  REVERSE PROXY Caddy                                  │ │
│  │  - HTTPS automático (Let's Encrypt)                   │ │
│  │  - Rate limiting                                      │ │
│  │  - Consumo RAM: ~50MB                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  RAM TOTAL ESTIMADA: 1.0-1.6GB / 2GB                       │
│  CPU: 2-4 vCPU (compartido entre todos los servicios)      │
└─────────────────────────────────────────────────────────────┘
```

### Puntos Críticos Identificados

1. **Competencia por RAM:** Los servidores VPN compiten con el backend por memoria
2. **Single Point of Failure:** Si el VPS cae, todo el ecosistema se detiene
3. **I/O de Disco:** PostgreSQL + logs VPN + background jobs = estrés de disco
4. **Red Compartida:** Tráfico VPN + tráfico API comparten el mismo ancho de banda

---

## 🏗️ Estrategia de Optimización

### Principio Rector
> **"Cada MB de RAM cuenta. Cada ms de CPU importa."**

Todas las optimizaciones están diseñadas para:
1. Minimizar consumo de RAM
2. Maximizar throughput del backend
3. Aislar fallos entre componentes
4. Mantener seguridad sin sacrificar rendimiento

---

## 📊 Fase 1: Optimización de PostgreSQL (Impacto: Alto)

### Problema
PostgreSQL por defecto consume ~25% de la RAM del sistema en `shared_buffers`. En un VPS de 2GB, esto es ~500MB que el backend necesita.

### Solución: Configuración Ultra-Light

**Archivo: `/etc/postgresql/15/main/postgresql.conf`**

```ini
# =============================================================================
# OPTIMIZACIÓN PARA VPS DE 2GB RAM CON CARGA MIXTA (VPN + API)
# =============================================================================

# MEMORY - Crítico para nuestro caso
shared_buffers = 128MB              # Reducido de 512MB (25% → 6.5%)
effective_cache_size = 768MB        # Lo que queda para OS cache
work_mem = 4MB                      # Por operación (joins, sorts)
maintenance_work_mem = 64MB         # Para VACUUM, CREATE INDEX
wal_buffers = 4MB                   # Write-ahead log buffer

# CONNECTIONS - Limitar para controlar RAM
max_connections = 50                # Suficiente para async pool
superuser_reserved_connections = 3  # Para mantenimiento

# CHECKPOINTING - Reducir I/O spikes
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min          # Más espaciado para reducir I/O
checkpoint_warning = 30s

# WAL - Optimizar para SSD (asumimos SSD en VPS)
wal_compression = on
random_page_cost = 1.1              # SSD tiene acceso aleatorio rápido
effective_io_concurrency = 200      # Para SSD

# QUERY PLANNING - Ajustes finos
default_statistics_target = 100     # Mejor planificación sin exceso de CPU
constraint_exclusion = partition    # Solo para particionamiento

# LOGGING - Reducir I/O de logs
log_min_duration_statement = 100    # Solo logs de queries > 100ms
log_checkpoints = off
log_connections = off
log_disconnections = off
log_lock_waits = off

# AUTOVACUUM - Ajustado para baja RAM
autovacuum_max_workers = 2          # Reducido de 3
autovacuum_vacuum_cost_limit = 200  # Menos agresivo
autovacuum_vacuum_cost_delay = 20ms
```

### Pool de Conexiones con PgBouncer (Opcional pero recomendado)

**Instalación:**
```bash
sudo apt install pgbouncer -y
```

**Configuración `/etc/pgbouncer/pgbouncer.ini`:**
```ini
[databases]
usipipodb = host=127.0.0.1 port=5432 dbname=usipipodb

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction           # CRÍTICO: transacción, no session
max_client_conn = 200             # Máximo de conexiones entrantes
default_pool_size = 10            # Conexiones por usuario/DB
min_pool_size = 5                 # Mantener conexiones calientes
reserve_pool_size = 5             # Extra bajo carga
reserve_pool_timeout = 5          # Segundos antes de usar reserve
server_lifetime = 3600            # Reciclar conexiones cada hora
server_idle_timeout = 600         # Cerrar conexiones inactivas
```

**Beneficio:** Reduce conexiones PostgreSQL de 50 a ~10-15 activas, ahorrando ~50-100MB RAM.

---

## ⚡ Fase 2: Optimización de Redis (Impacto: Medio)

### Problema
Redis puede crecer sin control si no se configuran límites y políticas de expiración.

### Solución: Redis con Límites Estrictos

**Archivo: `/etc/redis/redis.conf`**

```ini
# =============================================================================
# OPTIMIZACIÓN PARA VPS DE 2GB RAM
# =============================================================================

# MEMORY LIMIT - Crítico
maxmemory 128mb                     # Límite absoluto
maxmemory-policy allkeys-lru        # Evict keys menos usadas primero

# PERSISTENCE - Reducir I/O
save 900 1                          # Backup después de 900s si 1 key cambia
save 300 10                         # Backup después de 300s si 10 keys cambian
save 60 10000                       # Backup después de 60s si 10000 keys cambian

# O alternativamente: sin persistencia (OTP y caché son desechables)
# save ""                           # Deshabilitar RDB completamente

# LOGGING
loglevel notice                     # Menos verboso que verbose
logfile /var/log/redis/redis-server.log

# NETWORK
bind 127.0.0.1                      # Solo localhost (seguridad)
port 6379
timeout 300                         # Cerrar clientes inactivos después de 5min
tcp-keepalive 60                    # Keep-alive cada 60s

# SLOW LOG - Para debugging de performance
slowlog-log-slower-than 10000       # Logs de operaciones > 10ms
slowlog-max-len 128                 # Mantener últimos 128 slow logs
```

### Estructura de Keys con TTL Automático

```python
# En el backend, TODAS las keys de Redis deben tener TTL:

# OTPs - 5 minutos
await redis.setex(f"otp:{telegram_id}", 300, otp_code)

# Rate limiting - 1 hora
await redis.setex(f"rate:otp:{telegram_id}", 3600, count)
await redis.setex(f"rate:ip:{ip_address}", 3600, count)

# JWT blacklist - TTL = tiempo restante del JWT
await redis.setex(f"jwt:blacklist:{jti}", ttl_seconds, "1")

# Caché de dashboard - 15 minutos
await redis.setex(f"cache:dashboard:{telegram_id}", 900, cached_data)

# Notificaciones leídas - 7 días (limpieza automática)
await redis.setex(f"notif:ack:{telegram_id}:{notif_id}", 604800, "1")
```

**Beneficio:** Redis nunca excede 128MB, con limpieza automática de keys viejas.

---

## 🔥 Fase 3: Optimización del Backend FastAPI (Impacto: Alto)

### Problema
El backend corre en el mismo proceso que el bot, compitiendo por CPU y RAM.

### Solución: Separación de Procesos con Uvicorn Workers

**Archivo: `systemd/usipipo-backend.service`**

```ini
[Unit]
Description=uSipipo Backend API (FastAPI)
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=usipipo
Group=usipipo
WorkingDirectory=/opt/usipipobot

# Entorno
Environment="PATH=/opt/usipipobot/venv/bin"
EnvironmentFile=/opt/usipipobot/.env

# Ejecución con múltiples workers (ajustar según CPU cores)
# Para 2 vCPU: 2 workers
# Para 4 vCPU: 4 workers
ExecStart=/opt/usipipobot/venv/bin/uvicorn infrastructure.api.server:create_app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --loop asyncio \
    --http httptools \
    --lifespan on \
    --timeout-keep-alive 30 \
    --access-log

# Restart policy
Restart=always
RestartSec=5

# Resource limits - CRÍTICO para evitar OOM
LimitNOFILE=65535                   # Máximo de archivos abiertos
LimitNPROC=4096                     # Máximo de procesos/hilos

# Memory limit - Prevenir OOM killer
# MemoryMax=800M                    # Descomentar si systemd lo soporta

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=usipipo-backend

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/usipipobot/logs /opt/usipipobot/data

[Install]
WantedBy=multi-user.target
```

### Optimización de Uvicorn con HttpTools

**Instalación:**
```bash
pip install httptools uvloop
```

**Beneficio:** HttpTools es un parser HTTP en C que es 2-3x más rápido que el parser de Python puro.

### Connection Pooling de Base de Datos

**Archivo: `infrastructure/persistence/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

# Configuración optimizada para VPS de 2GB
engine = create_async_engine(
    settings.database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=10,                   # Máximo de conexiones en el pool
    max_overflow=5,                 # Conexiones extra temporales
    pool_timeout=30,                # Timeout esperando conexión
    pool_recycle=1800,              # Reciclar conexiones cada 30min
    pool_pre_ping=True,             # Verificar conexión antes de usar
    echo=False,                     # No loggear SQL en producción
)

session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
```

**Beneficio:** Reutiliza conexiones en lugar de crear nuevas (ahorra ~5-10ms por request y reduce RAM).

---

## 🛡️ Fase 4: Aislamiento de Fallos (Impacto: Crítico)

### Problema
Si un componente falla (ej: Outline server), puede arrastrar abajo todo el sistema.

### Solución: Systemd con Límites de Recursos

#### 4.1 WireGuard Server

**Archivo: `/etc/systemd/system/wg-quick@wg0.service.d/override.conf`**

```ini
[Service]
# Límites de recursos para WireGuard
LimitNOFILE=1024                    # Máximo de archivos abiertos
LimitNPROC=256                      # Máximo de procesos
MemoryMax=256M                      # Límite de RAM (si systemd lo soporta)
CPUQuota=50%                        # Máximo 50% de CPU

# Restart
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wireguard
```

#### 4.2 Outline Server

**Archivo: `/etc/systemd/system/outline-server.service.d/override.conf`**

```ini
[Service]
# Límites de recursos para Outline
LimitNOFILE=2048                    # Outline necesita más conexiones
LimitNPROC=512
MemoryMax=512M                      # Outline puede consumir más RAM
CPUQuota=75%                        # Hasta 75% de CPU bajo carga

# Restart
Restart=always
RestartSec=10

# Logging (reducir I/O)
StandardOutput=journal
StandardError=journal
SyslogIdentifier=outline
```

#### 4.3 Redis

**Archivo: `/etc/systemd/system/redis.service.d/override.conf`**

```ini
[Service]
# Límites estrictos para Redis
LimitNOFILE=4096
LimitNPROC=256
MemoryMax=256M                      # Redis nunca debe exceder esto
CPUQuota=25%                        # Redis es ligero, no necesita mucha CPU

# OOM Score - Prioridad baja para OOM killer
OOMScoreAdjust=100                  # Más probable de ser killed si hay OOM

# Restart
Restart=always
RestartSec=5
```

#### 4.4 PostgreSQL

**Archivo: `/etc/systemd/system/postgresql.service.d/override.conf`**

```ini
[Service]
# Límites para PostgreSQL
LimitNOFILE=8192                    # PostgreSQL necesita muchos FDs
LimitNPROC=1024
MemoryMax=512M                      # PostgreSQL con shared_buffers=128MB
CPUQuota=50%                        # No debe dominar la CPU

# OOM Score - Prioridad media-baja
OOMScoreAdjust=50

# Restart
Restart=always
RestartSec=10
```

---

## 📈 Fase 5: Monitoreo Ligero (Impacto: Medio)

### Problema
Prometheus + Grafana consumen ~500MB RAM. No cabe en el VPS.

### Solución: Monitoreo Minimalista con Alertas

#### 5.1 Script de Health Check Ligero

**Archivo: `/opt/usipipobot/scripts/health_check.sh`**

```bash
#!/bin/bash
# Health check ligero que consume ~5MB RAM y se ejecuta cada minuto

set -e

LOG_FILE="/var/log/usipipo/health_check.log"
ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${ADMIN_ID},
            \"text\": \"🚨 ALERTA VPS:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }" >> /dev/null
    log "ALERT: $message"
}

# Verificar servicios
check_service() {
    local service=$1
    if ! systemctl is-active --quiet "$service"; then
        alert "❌ Servicio <b>$service</b> está INACTIVO"
        return 1
    fi
    return 0
}

# Verificar uso de RAM
check_ram() {
    local ram_used=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    if [ "$ram_used" -gt 90 ]; then
        alert "⚠️ Uso de RAM: ${ram_used}% (CRÍTICO)"
    elif [ "$ram_used" -gt 80 ]; then
        log "Uso de RAM: ${ram_used}% (ALERTA)"
    fi
}

# Verificar espacio en disco
check_disk() {
    local disk_used=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_used" -gt 90 ]; then
        alert "⚠️ Espacio en disco: ${disk_used}% (CRÍTICO)"
    elif [ "$disk_used" -gt 80 ]; then
        log "Espacio en disco: ${disk_used}% (ALERTA)"
    fi
}

# Verificar PostgreSQL
check_postgres() {
    if ! pg_isready -q; then
        alert "❌ PostgreSQL no está respondiendo"
    fi
}

# Verificar Redis
check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        alert "❌ Redis no está respondiendo"
    fi
}

# Verificar Caddy
check_caddy() {
    if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
        alert "❌ Backend FastAPI no está respondiendo (HTTP != 200)"
    fi
}

# Ejecutar todos los checks
log "=== Iniciando health check ==="

check_service "postgresql" || true
check_service "redis" || true
check_service "caddy" || true
check_service "usipipo-backend" || true
check_service "usipipo-bot" || true
check_service "wg-quick@wg0" || true
check_service "outline-server" || true

check_ram
check_disk
check_postgres
check_redis
check_caddy

log "=== Health check completado ==="
```

**Configuración Cron (cada 2 minutos):**
```bash
sudo crontab -e

# Agregar:
*/2 * * * * /opt/usipipobot/scripts/health_check.sh
```

#### 5.2 Endpoint de Health del Backend

**Archivo: `infrastructure/api/routes_health.py`**

```python
from fastapi import APIRouter, status
from sqlalchemy import text
import redis.asyncio as redis
import time

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint para monitoreo.
    Retorna 200 si todos los servicios están sanos.
    """
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check PostgreSQL
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        health_status["checks"]["postgresql"] = {"status": "ok", "latency_ms": (time.time() - start_time) * 1000}
    except Exception as e:
        health_status["checks"]["postgresql"] = {"status": "error", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        r = redis.Redis()
        await r.ping()
        await r.close()
        health_status["checks"]["redis"] = {"status": "ok"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "error", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Outline API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.outline_api_url}/server", timeout=5) as resp:
                if resp.status == 200:
                    health_status["checks"]["outline"] = {"status": "ok"}
                else:
                    health_status["checks"]["outline"] = {"status": "degraded", "http_status": resp.status}
    except Exception as e:
        health_status["checks"]["outline"] = {"status": "error", "error": str(e)}
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status)


@router.get("/metrics/summary")
async def metrics_summary():
    """
    Métricas resumidas para monitoreo ligero.
    """
    async with get_session() as session:
        # Contar usuarios activos
        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE status = 'active'")
        )
        active_users = result.scalar()
        
        # Contar claves activas
        result = await session.execute(
            text("SELECT COUNT(*) FROM vpn_keys WHERE is_active = true")
        )
        active_keys = result.scalar()
        
        # Contar paquetes activos
        result = await session.execute(
            text("SELECT COUNT(*) FROM data_packages WHERE is_active = true")
        )
        active_packages = result.scalar()
    
    # Uso de RAM del proceso
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "active_users": active_users,
        "active_keys": active_keys,
        "active_packages": active_packages,
        "memory_rss_mb": memory_info.rss / 1024 / 1024,
        "memory_vms_mb": memory_info.vms / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
    }
```

---

## 🔄 Fase 6: Background Jobs Optimizados (Impacto: Alto)

### Problema
Los background jobs corren en el mismo proceso que el bot, consumiendo RAM y CPU.

### Solución: Jobs Asíncronos con Límites de Recursos

#### 6.1 Separar Jobs en Proceso Independiente

**Archivo: `systemd/usipipo-jobs.service`**

```ini
[Unit]
Description=uSipipo Background Jobs
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=usipipo
Group=usipipo
WorkingDirectory=/opt/usipipobot

Environment="PATH=/opt/usipipobot/venv/bin"
EnvironmentFile=/opt/usipipobot/.env

# Ejecutar jobs en proceso separado
ExecStart=/opt/usipipobot/venv/bin/python -m infrastructure.jobs.runner

# Restart
Restart=always
RestartSec=10

# Límites de recursos
LimitNOFILE=4096
LimitNPROC=256
# MemoryMax=256M                   # Descomentar si systemd lo soporta

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=usipipo-jobs

[Install]
WantedBy=multi-user.target
```

#### 6.2 Runner de Jobs Optimizado

**Archivo: `infrastructure/jobs/runner.py`**

```python
"""
Runner de background jobs optimizado para bajo consumo de RAM.
Ejecuta jobs en intervalos configurados con garbage collection agresivo.
"""
import asyncio
import gc
import signal
import sys
from datetime import datetime, timezone
from typing import Callable, Coroutine

from loguru import logger

from infrastructure.jobs.sync_vpn_usage_job import sync_vpn_usage
from infrastructure.jobs.key_cleanup_job import cleanup_inactive_keys
from infrastructure.jobs.expire_packages_job import expire_old_packages
from infrastructure.jobs.expire_crypto_orders_job import expire_crypto_orders
from infrastructure.jobs.memory_cleanup_job import cleanup_memory

# Configuración de intervalos (en segundos)
JOB_INTERVALS = {
    "sync_vpn_usage": 1800,        # 30 minutos
    "cleanup_inactive_keys": 3600, # 1 hora
    "expire_old_packages": 86400,  # 24 horas
    "expire_crypto_orders": 60,    # 1 minuto
    "memory_cleanup": 600,         # 10 minutos
}

# Última ejecución de cada job
last_run = {
    "sync_vpn_usage": 0,
    "cleanup_inactive_keys": 0,
    "expire_old_packages": 0,
    "expire_crypto_orders": 0,
    "memory_cleanup": 0,
}

running = True

def signal_handler(sig, frame):
    """Manejar señales de terminación gracefulmente."""
    global running
    logger.info(f"Señal {sig} recibida, cerrando jobs...")
    running = False

async def run_job_if_due(job_name: str, job_func: Callable[[], Coroutine], interval: int):
    """Ejecutar un job si ha pasado el intervalo desde la última ejecución."""
    global last_run
    
    current_time = datetime.now(timezone.utc).timestamp()
    
    if current_time - last_run[job_name] >= interval:
        logger.info(f"Ejecutando job: {job_name}")
        start_time = datetime.now(timezone.utc)
        
        try:
            await job_func()
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Job {job_name} completado en {elapsed:.2f}s")
            last_run[job_name] = current_time
        except Exception as e:
            logger.error(f"Error en job {job_name}: {e}")
            # No actualizar last_run para reintentar en el siguiente ciclo
        finally:
            # Garbage collection agresivo después de cada job
            gc.collect()
    
    await asyncio.sleep(0.1)  # Pequeña pausa para no bloquear el loop

async def main():
    """Loop principal del runner de jobs."""
    logger.info("Iniciando runner de background jobs")
    
    while running:
        await asyncio.gather(
            run_job_if_due("sync_vpn_usage", sync_vpn_usage, JOB_INTERVALS["sync_vpn_usage"]),
            run_job_if_due("cleanup_inactive_keys", cleanup_inactive_keys, JOB_INTERVALS["cleanup_inactive_keys"]),
            run_job_if_due("expire_old_packages", expire_old_packages, JOB_INTERVALS["expire_old_packages"]),
            run_job_if_due("expire_crypto_orders", expire_crypto_orders, JOB_INTERVALS["expire_crypto_orders"]),
            run_job_if_due("memory_cleanup", cleanup_memory, JOB_INTERVALS["memory_cleanup"]),
        )
        
        await asyncio.sleep(1)  # Chequear cada segundo
    
    logger.info("Runner de jobs detenido")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Runner de jobs terminado por usuario")
        sys.exit(0)
```

#### 6.3 Job de Limpieza de Memoria Optimizado

**Archivo: `infrastructure/jobs/memory_cleanup_job.py`**

```python
"""
Limpieza de memoria optimizada para VPS de 2GB.
Intenta liberar RAM sin afectar el rendimiento.
"""
import asyncio
import gc
from loguru import logger

async def cleanup_memory():
    """
    Limpieza de memoria que intenta liberar RAM del sistema.
    Solo funciona en Linux con permisos de root/sudo.
    """
    try:
        # 1. Garbage collection de Python
        gc.collect()
        
        # 2. Intentar liberar caché de página del kernel (requiere sudo)
        try:
            import subprocess
            # Sync primero para evitar pérdida de datos
            subprocess.run(['sync'], check=True, capture_output=True)
            # Liberar caché de página, dentries e inodes
            subprocess.run(
                ['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'],
                check=True,
                capture_output=True
            )
            logger.info("Limpieza de caché del kernel completada")
        except subprocess.CalledProcessError as e:
            logger.debug(f"No se pudo limpiar caché del kernel: {e}")
        except FileNotFoundError:
            logger.debug("Comando 'sync' no encontrado")
        
        # 3. Log de uso de memoria actual
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int([l for l in meminfo.split('\n') if 'MemTotal' in l][0].split()[1])
                mem_available = int([l for l in meminfo.split('\n') if 'MemAvailable' in l][0].split()[1])
                usage_percent = ((mem_total - mem_available) / mem_total) * 100
                logger.info(f"Uso de memoria del sistema: {usage_percent:.1f}%")
        except Exception as e:
            logger.debug(f"No se pudo leer /proc/meminfo: {e}")
            
    except Exception as e:
        logger.error(f"Error en limpieza de memoria: {e}")
```

---

## 📊 Fase 7: Optimización de Red (Impacto: Medio)

### Problema
Tráfico VPN + tráfico API comparten el mismo ancho de banda.

### Solución: Traffic Shaping con TC

**Archivo: `/opt/usipipobot/scripts/traffic_shaping.sh`**

```bash
#!/bin/bash
# Traffic shaping para priorizar tráfico API sobre tráfico VPN

# Configuración
INTERFACE=$(ip route | grep default | awk '{print $5}')  # Detectar interfaz automáticamente
API_PORT=8000
WG_PORT=51820
OUTLINE_PORT=443

# Limpiar reglas existentes
tc qdisc del dev $INTERFACE root 2>/dev/null || true

# Crear qdisc root con HTB (Hierarchical Token Bucket)
tc qdisc add dev $INTERFACE root handle 1: htb default 30

# Crear clases para diferentes tipos de tráfico
# Clase 1: Tráfico API (prioridad alta) - 40% del ancho de banda
tc class add dev $INTERFACE parent 1: classid 1:1 htb rate 40mbit ceil 100mbit prio 1

# Clase 2: Tráfico VPN (prioridad media) - 50% del ancho de banda
tc class add dev $INTERFACE parent 1: classid 1:2 htb rate 50mbit ceil 100mbit prio 2

# Clase 3: Otro tráfico (prioridad baja) - 10% del ancho de banda
tc class add dev $INTERFACE parent 1: classid 1:3 htb rate 10mbit ceil 50mbit prio 3

# Filtrar tráfico API hacia la clase 1
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 \
    match ip dport $API_PORT 0xffff flowid 1:1

tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 \
    match ip sport $API_PORT 0xffff flowid 1:1

# Filtrar tráfico VPN hacia la clase 2
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 \
    match ip dport $WG_PORT 0xffff flowid 1:2

tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 \
    match ip sport $WG_PORT 0xffff flowid 1:2

tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 \
    match ip dport $OUTLINE_PORT 0xffff flowid 1:2

tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 \
    match ip sport $OUTLINE_PORT 0xffff flowid 1:2

# Todo lo demás va a la clase 3 (default)

echo "Traffic shaping configurado en interfaz $INTERFACE"
echo "  - API (puerto $API_PORT): 40mbit (prioridad alta)"
echo "  - VPN (puertos $WG_PORT, $OUTLINE_PORT): 50mbit (prioridad media)"
echo "  - Otro tráfico: 10mbit (prioridad baja)"
```

**Ejecutar al inicio (agregar a /etc/rc.local):**
```bash
/opt/usipipobot/scripts/traffic_shaping.sh
```

**Beneficio:** El tráfico API siempre tiene prioridad sobre el tráfico VPN, asegurando que las respuestas del bot y la mini app sean rápidas incluso bajo carga VPN pesada.

---

## 📊 Resumen de Optimizaciones y Consumo Estimado

| Componente | RAM Antes | RAM Después | Ahorro |
|------------|-----------|-------------|--------|
| PostgreSQL | 500MB | 200MB | -300MB |
| Redis | 150MB | 100MB | -50MB |
| Backend FastAPI | 400MB | 350MB | -50MB |
| Bot Telegram | 200MB | 180MB | -20MB |
| WireGuard | 150MB | 150MB | 0 |
| Outline | 300MB | 300MB | 0 |
| Caddy | 50MB | 50MB | 0 |
| **TOTAL** | **1750MB** | **1330MB** | **-420MB** |

**Margen de seguridad:** 2000MB - 1330MB = **670MB libres** (33.5% de margen)

---

## ✅ Checklist de Implementación

### Semana 1: Optimización de Base de Datos
- [ ] Aplicar configuración optimizada de PostgreSQL
- [ ] Instalar y configurar PgBouncer (opcional)
- [ ] Aplicar configuración optimizada de Redis
- [ ] Verificar que todas las keys de Redis tengan TTL

### Semana 2: Optimización del Backend
- [ ] Separar backend en servicio systemd independiente
- [ ] Configurar Uvicorn con múltiples workers
- [ ] Instalar httptools y uvloop
- [ ] Configurar connection pooling de SQLAlchemy

### Semana 3: Aislamiento de Fallos
- [ ] Configurar overrides de systemd para todos los servicios
- [ ] Configurar límites de memoria y CPU
- [ ] Configurar OOM score para servicios críticos

### Semana 4: Monitoreo y Alertas
- [ ] Implementar script de health check
- [ ] Configurar cron para health check
- [ ] Implementar endpoint /health en el backend
- [ ] Probar alertas de Telegram

### Semana 5: Background Jobs
- [ ] Separar jobs en servicio independiente
- [ ] Implementar garbage collection agresivo
- [ ] Configurar intervals óptimos para cada job

### Semana 6: Optimización de Red
- [ ] Implementar traffic shaping con TC
- [ ] Probar bajo carga
- [ ] Ajustar límites según resultados

---

## 🎯 Métricas de Éxito

| Métrica | Antes | Después (Objetivo) |
|---------|-------|-------------------|
| RAM libre promedio | 200-400MB | 600-800MB |
| Latencia API (p95) | 300ms | <100ms |
| Tiempo de respuesta del bot | 2-3s | <1s |
| Caídas del servicio | 1-2/semana | 0/semana |
| Usuarios máx soportados | 200-300 | 500-1000 |

---

*Documento versión 1.0 - Fecha: Marzo 2026*
