# Plan 3: Medidor de Latencia y Estado del Servidor
**Fecha:** 16 de Marzo 2026
**Proyecto:** uSipipo VPN — usipipobot
**Estado:** Borrador — pendiente aprobación
**Prioridad:** 🟠 Alta (segunda tarea después del bug de checkout)
**Tiempo estimado:** 4-6 horas

---

## Contexto

Con un solo VPS disponible, la transparencia sobre el estado del servidor es un diferenciador de confianza clave. Los usuarios necesitan saber si el servidor está rápido o saturado antes de conectarse. Este plan implementa un sistema de monitoreo liviano que expone métricas en tiempo real tanto en el bot de Telegram como en la mini app web.

---

## 1. Métricas a recopilar

| Métrica | Descripción | Fuente |
|---------|-------------|--------|
| **Latencia RTT** | Ping promedio del VPS hacia exterior | `subprocess ping 1.1.1.1` |
| **CPU %** | Porcentaje de uso del procesador | `psutil.cpu_percent()` |
| **RAM %** | Porcentaje de memoria usada | `psutil.virtual_memory()` |
| **RAM usada (MB)** | Megabytes consumidos | `psutil.virtual_memory().used` |
| **Conexiones WireGuard** | Peers activos en `wg0` | `wg show wg0 peers` |
| **Estado Outline** | UP / DOWN | `systemctl is-active` |
| **Estado WireGuard** | UP / DOWN | `systemctl is-active` |
| **Estado dnsproxy** | UP / DOWN (si está implementado) | `systemctl is-active` |
| **Uptime** | Horas desde el último reinicio | `psutil.boot_time()` |

---

## 2. Arquitectura de componentes

```
┌─────────────────────────────────────────────────────┐
│  Background Job (cada 60 segundos)                   │
│  latency_collector_job.py                            │
│                                                      │
│  1. ping 1.1.1.1 (3 intentos, promedio)              │
│  2. psutil → CPU, RAM                                │
│  3. wg show → peers activos                          │
│  4. systemctl → estado servicios                     │
│                ↓                                     │
│  ServerStats dataclass                               │
│                ↓                                     │
│  Redis cache (TTL: 5 min)                            │
│  Historial rolling 10 puntos                         │
└─────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌──────────────────────┐
│  Bot Telegram   │      │  Mini App Web         │
│  /status        │      │  GET /api/status      │
│  Botón en menú  │      │  Widget en pantalla   │
└─────────────────┘      └──────────────────────┘
         │
         ▼
┌─────────────────┐
│  Alertas Admin  │
│  CPU > 85%      │
│  RAM > 90%      │
│  Latencia >200ms│
└─────────────────┘
```

---

## 3. Implementación

### 3.1 Dataclass ServerStats

```python
# infrastructure/jobs/latency_collector_job.py

import asyncio
import subprocess
import psutil
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

@dataclass
class ServerStats:
    timestamp: str              # ISO 8601
    ping_ms: float              # RTT promedio en ms
    cpu_percent: float          # 0-100
    ram_percent: float          # 0-100
    ram_used_mb: int            # MB consumidos
    ram_total_mb: int           # MB totales del VPS
    active_wg_connections: int  # Peers WireGuard con handshake reciente
    outline_status: bool        # True = UP
    wireguard_status: bool      # True = UP
    dnsproxy_status: bool       # True = UP (si está instalado)
    uptime_hours: float         # Horas desde boot

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @property
    def quality_score(self) -> int:
        """Score de 0-100 basado en métricas clave."""
        score = 100
        if self.ping_ms > 200: score -= 40
        elif self.ping_ms > 100: score -= 20
        elif self.ping_ms > 50: score -= 10
        if self.cpu_percent > 85: score -= 30
        elif self.cpu_percent > 60: score -= 15
        if self.ram_percent > 90: score -= 30
        elif self.ram_percent > 75: score -= 15
        return max(0, score)

    @property
    def status_label(self) -> tuple[str, str]:
        """Retorna (emoji, texto) según el score."""
        score = self.quality_score
        if score >= 75:
            return "🟢", "Excelente"
        elif score >= 50:
            return "🟡", "Normal"
        else:
            return "🔴", "Alta carga"
```

### 3.2 Collector function

```python
async def collect_server_stats() -> ServerStats:
    # --- Latencia ---
    try:
        result = subprocess.run(
            ["ping", "-c", "3", "-W", "2", "1.1.1.1"],
            capture_output=True, text=True, timeout=10
        )
        ping_ms = _parse_ping_avg(result.stdout)
    except Exception:
        ping_ms = 999.0  # Sin respuesta

    # --- CPU y RAM ---
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()

    # --- Peers WireGuard activos ---
    try:
        wg_result = subprocess.run(
            ["wg", "show", "wg0", "latest-handshakes"],
            capture_output=True, text=True, timeout=5
        )
        # Contar peers con handshake en los últimos 3 minutos
        now = int(datetime.now().timestamp())
        active = sum(
            1 for line in wg_result.stdout.splitlines()
            if len(line.split()) == 2 and (now - int(line.split()[1])) < 180
        )
    except Exception:
        active = 0

    # --- Estado de servicios ---
    def is_service_active(name: str) -> bool:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", name],
                capture_output=True, text=True, timeout=3
            )
            return r.stdout.strip() == "active"
        except Exception:
            return False

    outline_up = is_service_active("outline-ss-server") or is_service_active("shadowbox")
    wg_up = is_service_active("wg-quick@wg0")
    dns_up = is_service_active("dnsproxy")

    # --- Uptime ---
    uptime_h = (datetime.now().timestamp() - psutil.boot_time()) / 3600

    return ServerStats(
        timestamp=datetime.now(timezone.utc).isoformat(),
        ping_ms=round(ping_ms, 1),
        cpu_percent=round(cpu, 1),
        ram_percent=round(ram.percent, 1),
        ram_used_mb=ram.used // (1024 * 1024),
        ram_total_mb=ram.total // (1024 * 1024),
        active_wg_connections=active,
        outline_status=outline_up,
        wireguard_status=wg_up,
        dnsproxy_status=dns_up,
        uptime_hours=round(uptime_h, 1),
    )

def _parse_ping_avg(output: str) -> float:
    """Extrae el RTT promedio del output de ping."""
    for line in output.splitlines():
        if "avg" in line or "rtt" in line:
            # Formato: rtt min/avg/max/mdev = 12.3/15.6/18.9/2.1 ms
            parts = line.split("=")[-1].strip().split("/")
            if len(parts) >= 2:
                return float(parts[1])
    return 999.0
```

### 3.3 Cache en Redis

```python
# infrastructure/cache/stats_cache.py

STATS_LATEST_KEY = "server:stats:latest"
STATS_HISTORY_KEY = "server:stats:history"
STATS_TTL = 300  # 5 minutos

async def save_stats(stats: ServerStats, redis):
    await redis.setex(STATS_LATEST_KEY, STATS_TTL, stats.to_json())
    await redis.lpush(STATS_HISTORY_KEY, stats.to_json())
    await redis.ltrim(STATS_HISTORY_KEY, 0, 9)  # Últimas 10 mediciones

async def get_latest_stats(redis) -> Optional[ServerStats]:
    raw = await redis.get(STATS_LATEST_KEY)
    if not raw:
        return None
    data = json.loads(raw)
    return ServerStats(**data)

async def get_stats_history(redis) -> list[ServerStats]:
    items = await redis.lrange(STATS_HISTORY_KEY, 0, 9)
    return [ServerStats(**json.loads(item)) for item in items]
```

### 3.4 Background job con scheduler

```python
# infrastructure/jobs/latency_collector_job.py

async def run_stats_collector(redis, bot, admin_chat_id: int):
    """Job que corre cada 60 segundos."""
    while True:
        try:
            stats = await collect_server_stats()
            await save_stats(stats, redis)
            await check_and_send_alerts(stats, bot, admin_chat_id)
        except Exception as e:
            logger.error(f"Stats collector error: {e}")

        await asyncio.sleep(60)
```

---

## 4. Handler del bot: comando `/status`

```python
# telegram_bot/features/status/handlers.py

async def server_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = await get_latest_stats(context.bot_data["redis"])

    if not stats:
        await update.message.reply_text("⏳ Recopilando datos del servidor, intenta en 1 minuto.")
        return

    icon, label = stats.status_label

    protocol_lines = []
    if stats.outline_status:
        protocol_lines.append("✅ Outline")
    else:
        protocol_lines.append("❌ Outline (caído)")

    if stats.wireguard_status:
        wg_line = f"✅ WireGuard ({stats.active_wg_connections} activos)"
        if stats.dnsproxy_status:
            wg_line += " + 🛡️ AdBlock"
        protocol_lines.append(wg_line)
    else:
        protocol_lines.append("❌ WireGuard (caído)")

    protocols_text = "\n".join(protocol_lines)

    message = f"""
📡 *Estado del Servidor uSipipo*

{icon} *{label}*

⚡ Latencia: `{stats.ping_ms:.0f} ms`
🖥️ CPU: `{stats.cpu_percent:.0f}%`
💾 RAM: `{stats.ram_percent:.0f}%` \
(`{stats.ram_used_mb}` / `{stats.ram_total_mb}` MB)

*Protocolos:*
{protocols_text}

⏰ Uptime: `{stats.uptime_hours:.0f} horas`
🕐 Medido hace: `< 60 segundos`
"""

    keyboard = [[InlineKeyboardButton("🔄 Actualizar", callback_data="refresh_status")]]
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
```

---

## 5. Endpoint FastAPI para la mini app web

```python
# api/routes/status.py

from fastapi import APIRouter
router = APIRouter()

@router.get("/api/status")
async def get_server_status(redis=Depends(get_redis)):
    stats = await get_latest_stats(redis)
    history = await get_stats_history(redis)

    if not stats:
        return {"status": "collecting", "message": "Recopilando datos..."}

    icon, label = stats.status_label

    return {
        "status": "ok",
        "current": stats.to_dict(),
        "quality_score": stats.quality_score,
        "status_icon": icon,
        "status_label": label,
        "history": [s.to_dict() for s in history],
    }
```

Widget en la mini app web:

```
╔══════════════════════════════╗
║  📡 Estado del Servidor      ║
╠══════════════════════════════╣
║                              ║
║   🟢  Excelente              ║
║                              ║
║   Latencia:    23 ms  ↓      ║
║   CPU:         42%           ║
║   RAM:         61%  (1.2GB)  ║
║   Conexiones:  12 activos    ║
║                              ║
║   [Outline ✅]  [WG ✅]      ║
║   [AdBlock 🛡️ ACTIVO]        ║
║                              ║
║   Actualizado: hace 38s      ║
╚══════════════════════════════╝
```

---

## 6. Alertas automáticas al administrador

```python
# infrastructure/jobs/latency_collector_job.py

ALERT_COOLDOWN = {}  # Evitar spam de alertas (una por tipo cada 30 min)

async def check_and_send_alerts(stats: ServerStats, bot, admin_chat_id: int):
    now = datetime.now().timestamp()

    alerts = []

    if stats.cpu_percent > 85 and _can_alert("cpu", now):
        alerts.append(f"⚠️ CPU al `{stats.cpu_percent:.0f}%`")

    if stats.ram_percent > 90 and _can_alert("ram", now):
        alerts.append(f"🚨 RAM al `{stats.ram_percent:.0f}%` ({stats.ram_used_mb} MB)")

    if stats.ping_ms > 200 and _can_alert("latency", now):
        alerts.append(f"🐢 Latencia alta: `{stats.ping_ms:.0f} ms`")

    if not stats.outline_status and _can_alert("outline", now):
        alerts.append("❌ Outline está caído")

    if not stats.wireguard_status and _can_alert("wireguard", now):
        alerts.append("❌ WireGuard está caído")

    if alerts:
        msg = "🔔 *Alerta del servidor uSipipo*\n\n" + "\n".join(alerts)
        await bot.send_message(admin_chat_id, msg, parse_mode="Markdown")

def _can_alert(key: str, now: float) -> bool:
    last = ALERT_COOLDOWN.get(key, 0)
    if now - last > 1800:  # 30 minutos
        ALERT_COOLDOWN[key] = now
        return True
    return False
```

---

## 7. Archivos a crear / modificar

| Archivo | Acción |
|---------|--------|
| `infrastructure/jobs/latency_collector_job.py` | CREAR |
| `infrastructure/cache/stats_cache.py` | CREAR |
| `telegram_bot/features/status/handlers.py` | CREAR |
| `telegram_bot/features/status/keyboards.py` | CREAR |
| `api/routes/status.py` | CREAR |
| `telegram_bot/bot.py` | MODIFICAR — registrar handler `/status` |
| `infrastructure/scheduler.py` | MODIFICAR — agregar `run_stats_collector` al loop |

---

## 8. Criterios de éxito

- [ ] `/status` en el bot responde en menos de 2 segundos
- [ ] La latencia que muestra corresponde a la real del servidor (±10ms)
- [ ] El estado de Outline y WireGuard refleja si los servicios están activos
- [ ] El widget en la mini app se actualiza automáticamente
- [ ] El admin recibe alertas cuando CPU > 85% o RAM > 90%
- [ ] El job collector NO consume más de 2% de CPU adicional
- [ ] Sin crash en el bot si Redis no está disponible (fallback graceful)

---

**Fin del documento**
*Siguiente paso al aprobar: invocar writing-plans para plan de implementación detallado.*
