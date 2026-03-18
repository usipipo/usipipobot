"""
Server latency and metrics collector.

Collects server performance metrics (ping, CPU, RAM, WireGuard connections,
service status) and stores them in Redis cache for bot and API consumption.
"""

import asyncio
import json
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

import redis.asyncio as redis
from telegram.ext import ContextTypes

from config import settings
from infrastructure.cache.redis_client import get_redis_client
from infrastructure.cache.stats_cache import ServerStats, save_stats
from infrastructure.metrics import collect_server_stats
from utils.logger import logger


async def _run_command(cmd: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    """
    Run command asynchronously using asyncio.create_subprocess_exec.

    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds

    Returns:
        CompletedProcess with stdout/stderr
    """
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=process.returncode or 0,
        stdout=stdout.decode("utf-8", errors="replace"),
        stderr=stderr.decode("utf-8", errors="replace"),
    )


async def _collect_ping() -> float:
    """
    Collect ping latency to 1.1.1.1 (3 pings, average RTT).

    Returns:
        Average RTT in ms, or 999.0 if failed
    """
    try:
        result = await _run_command(["ping", "-c", "3", "-W", "2", "1.1.1.1"], timeout=10)

        if result.returncode != 0:
            logger.warning(f"⚠️ Ping command failed: {result.stderr.strip()}")
            return 999.0

        return _parse_ping_avg(result.stdout)
    except asyncio.TimeoutError:
        logger.warning("⚠️ Ping command timed out")
        return 999.0
    except Exception as e:
        logger.error(f"❌ Ping collection error: {e}")
        return 999.0


def _parse_ping_avg(output: str) -> float:
    """
    Extract average RTT from ping command output.

    Parses formats like:
    - "rtt min/avg/max/mdev = 12.3/15.6/18.9/2.1 ms"
    - "round-trip min/avg/max/stddev = 12.3/15.6/18.9/2.1 ms"

    Args:
        output: Raw ping command stdout

    Returns:
        Average RTT in ms, or 999.0 if parsing failed
    """
    # Pattern for rtt/round-trip statistics line
    patterns = [
        r"rtt\s+min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s*ms",
        r"round-trip\s+min/avg/max/stddev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s*ms",
    ]

    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            try:
                return float(match.group(2))
            except (ValueError, IndexError):
                break

    # Fallback: try to find any line with "avg" and numbers
    for line in output.splitlines():
        if "avg" in line.lower():
            # Try to extract number after "="
            parts = line.split("=")
            if len(parts) >= 2:
                numbers = re.findall(r"[\d.]+", parts[-1])
                if len(numbers) >= 2:
                    try:
                        return float(numbers[1])
                    except ValueError:
                        pass

    logger.warning("⚠️ Could not parse ping output")
    return 999.0


async def _collect_cpu_ram() -> tuple[float, float, int, int]:
    """
    Collect CPU and RAM usage using psutil.

    Returns:
        Tuple of (cpu_percent, ram_percent, ram_used_mb, ram_total_mb)
    """
    import psutil

    # Run in thread pool to avoid blocking
    cpu_percent = await asyncio.to_thread(psutil.cpu_percent, interval=1)
    ram = await asyncio.to_thread(psutil.virtual_memory)

    ram_used_mb = ram.used // (1024 * 1024)
    ram_total_mb = ram.total // (1024 * 1024)

    return cpu_percent, ram.percent, ram_used_mb, ram_total_mb


async def _collect_wireguard_peers() -> int:
    """
    Count active WireGuard peers (handshake in last 3 minutes).

    Returns:
        Number of active peers, or 0 if failed
    """
    try:
        result = await _run_command(
            ["wg", "show", settings.WG_INTERFACE, "latest-handshakes"], timeout=5
        )

        if result.returncode != 0:
            logger.debug(f"⚠️ WireGuard command failed: {result.stderr.strip()}")
            return 0

        now = int(datetime.now().timestamp())
        active_count = 0

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    handshake_time = int(parts[1])
                    # Active if handshake within last 3 minutes (180 seconds)
                    if handshake_time > 0 and (now - handshake_time) < 180:
                        active_count += 1
                except ValueError:
                    continue

        return active_count
    except Exception as e:
        logger.error(f"❌ WireGuard peer collection error: {e}")
        return 0


async def _check_service(service_name: str) -> bool:
    """
    Check if systemd service is active.

    Args:
        service_name: Name of the systemd service

    Returns:
        True if service is "active", False otherwise
    """
    try:
        result = await _run_command(["systemctl", "is-active", service_name], timeout=3)
        return result.stdout.strip() == "active"
    except Exception as e:
        logger.debug(f"⚠️ Service check failed for {service_name}: {e}")
        return False


async def _collect_service_status() -> tuple[bool, bool, bool]:
    """
    Collect status of Outline, WireGuard, and dnsproxy services.

    Returns:
        Tuple of (outline_up, wireguard_up, dnsproxy_up)
    """
    # Check Outline (could be outline-ss-server or shadowbox)
    outline_up = await _check_service("outline-ss-server")
    if not outline_up:
        outline_up = await _check_service("shadowbox")

    # Check WireGuard
    wireguard_up = await _check_service(f"wg-quick@{settings.WG_INTERFACE}")

    # Check dnsproxy (optional)
    dnsproxy_up = await _check_service("dnsproxy")

    return outline_up, wireguard_up, dnsproxy_up


async def _collect_uptime() -> float:
    """
    Get server uptime in hours since boot.

    Returns:
        Uptime in hours
    """
    import psutil

    boot_time = await asyncio.to_thread(psutil.boot_time)
    uptime_seconds = datetime.now().timestamp() - boot_time
    return round(uptime_seconds / 3600, 1)


async def collect_server_stats() -> ServerStats:
    """
    Collect all server metrics.

    Returns:
        ServerStats instance with current metrics
    """
    logger.debug("📊 Collecting server metrics...")

    # Collect all metrics concurrently where possible
    ping_ms = await _collect_ping()
    cpu_percent, ram_percent, ram_used_mb, ram_total_mb = await _collect_cpu_ram()
    active_wg = await _collect_wireguard_peers()
    outline_up, wg_up, dns_up = await _collect_service_status()
    uptime_hours = await _collect_uptime()

    stats = ServerStats(
        timestamp=datetime.now(timezone.utc).isoformat(),
        ping_ms=round(ping_ms, 1),
        cpu_percent=round(cpu_percent, 1),
        ram_percent=round(ram_percent, 1),
        ram_used_mb=ram_used_mb,
        ram_total_mb=ram_total_mb,
        active_wg_connections=active_wg,
        outline_status=outline_up,
        wireguard_status=wg_up,
        dnsproxy_status=dns_up,
        uptime_hours=uptime_hours,
    )

    icon, label = stats.status_label
    logger.debug(
        f"✅ Metrics collected: {icon} {label} | "
        f"Ping: {stats.ping_ms}ms | CPU: {stats.cpu_percent}% | "
        f"RAM: {stats.ram_percent}% | WG: {stats.active_wg_connections}"
    )

    return stats


# Alert cooldown tracking (prevents spam)
ALERT_COOLDOWNS: Dict[str, float] = {}
ALERT_COOLDOWN_SECONDS = 1800  # 30 minutes


def _can_send_alert(alert_type: str) -> bool:
    """
    Check if enough time has passed since last alert of this type.

    Args:
        alert_type: Type of alert (cpu, ram, latency, outline, wireguard)

    Returns:
        True if alert can be sent
    """
    now = datetime.now().timestamp()
    last_alert = ALERT_COOLDOWNS.get(alert_type, 0)

    if now - last_alert > ALERT_COOLDOWN_SECONDS:
        ALERT_COOLDOWNS[alert_type] = now
        return True
    return False


async def _send_admin_alerts(bot: Any, admin_chat_id: int, stats: ServerStats) -> None:
    """
    Send alerts to admin if metrics exceed thresholds.

    Thresholds:
    - CPU > 85%
    - RAM > 90%
    - Latency > 200ms
    - Outline DOWN
    - WireGuard DOWN

    Args:
        bot: Telegram bot instance
        admin_chat_id: Admin chat ID from settings
        stats: Current server stats
    """
    alerts = []

    if stats.cpu_percent > 85 and _can_send_alert("cpu"):
        alerts.append(f"🚨 CPU al `{stats.cpu_percent:.0f}%`")

    if stats.ram_percent > 90 and _can_send_alert("ram"):
        alerts.append(
            f"🚨 RAM al `{stats.ram_percent:.0f}%` "
            f"(`{stats.ram_used_mb}` / `{stats.ram_total_mb}` MB)"
        )

    if stats.ping_ms > 200 and _can_send_alert("latency"):
        alerts.append(f"🐢 Latencia alta: `{stats.ping_ms:.0f} ms`")

    if not stats.outline_status and _can_send_alert("outline"):
        alerts.append("❌ Outline está caído")

    if not stats.wireguard_status and _can_send_alert("wireguard"):
        alerts.append("❌ WireGuard está caído")

    if alerts:
        message = "🔔 *Alerta del servidor uSipipo*\n\n" + "\n\n".join(alerts)
        try:
            await bot.send_message(chat_id=admin_chat_id, text=message, parse_mode="Markdown")
            logger.warning(f"🚨 Admin alert sent: {len(alerts)} issues detected")
        except Exception as e:
            logger.error(f"❌ Failed to send admin alert: {e}")


async def latency_collector_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Background job that collects server metrics every 60 seconds.

    Runs continuously and:
    1. Collects all server metrics
    2. Saves to Redis cache
    3. Sends alerts to admin if thresholds exceeded

    Job data should include:
    - "bot": Telegram bot instance
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data not available")
        return

    job_data = context.job.data
    bot = job_data.get("bot")
    admin_chat_id = settings.ADMIN_ID

    # Get Redis client
    redis_client = get_redis_client()

    try:
        # Collect metrics
        stats = await collect_server_stats()

        # Save to cache
        await save_stats(stats, redis_client)

        # Send alerts if needed (admin only)
        if bot and admin_chat_id:
            await _send_admin_alerts(bot, admin_chat_id, stats)

    except Exception as e:
        logger.error(f"❌ Latency collector job error: {e}")
    finally:
        # Close Redis connection
        await redis_client.close()
