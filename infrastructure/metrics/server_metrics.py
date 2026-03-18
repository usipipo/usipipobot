"""
Server metrics collection.

Collects server performance metrics (ping, CPU, RAM, WireGuard connections,
service status) using async subprocess calls.
"""

import asyncio
import re
import subprocess
from datetime import datetime, timezone
from typing import Dict

from config import settings
from infrastructure.cache.stats_cache import ServerStats
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

    for line in output.splitlines():
        if "avg" in line.lower():
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
    outline_up = await _check_service("outline-ss-server")
    if not outline_up:
        outline_up = await _check_service("shadowbox")

    wireguard_up = await _check_service(f"wg-quick@{settings.WG_INTERFACE}")
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
