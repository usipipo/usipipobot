#!/usr/bin/env python3
"""
Test script for server metrics collection.

Validates that all server metrics can be collected successfully:
- Ping latency
- CPU and RAM usage
- WireGuard peers
- Service status (systemctl)
- Uptime

Run this script to verify your VPS is properly configured before
deploying the latency monitoring feature.

Usage:
    python scripts/test_server_metrics.py
"""

import asyncio
import subprocess
import sys
from datetime import datetime


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    if details:
        print(f"       {details}")


async def test_ping():
    """Test ping latency collection."""
    print_header("TEST 1: Ping Latency")

    try:
        process = await asyncio.create_subprocess_exec(
            "ping",
            "-c",
            "3",
            "-W",
            "2",
            "1.1.1.1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)

        if process.returncode == 0:
            output = stdout.decode()
            # Parse average ping
            for line in output.splitlines():
                if "avg" in line or "rtt" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        stats = parts[-1].strip().split("/")
                        if len(stats) >= 2:
                            avg_ping = stats[1]
                            print_result("Ping to 1.1.1.1", True, f"Average RTT: {avg_ping} ms")
                            return True

            print_result("Ping parsing", False, "Could not parse ping output")
            return False
        else:
            print_result("Ping command", False, f"Return code: {process.returncode}")
            return False

    except asyncio.TimeoutError:
        print_result("Ping command", False, "Timeout after 10 seconds")
        return False
    except Exception as e:
        print_result("Ping command", False, str(e))
        return False


async def test_cpu_ram():
    """Test CPU and RAM collection."""
    print_header("TEST 2: CPU and RAM Usage")

    try:
        import psutil

        cpu = await asyncio.to_thread(psutil.cpu_percent, interval=1)
        ram = await asyncio.to_thread(psutil.virtual_memory)

        ram_used_mb = ram.used // (1024 * 1024)
        ram_total_mb = ram.total // (1024 * 1024)

        print_result("CPU Usage", True, f"{cpu:.1f}%")
        print_result("RAM Usage", True, f"{ram.percent:.1f}% ({ram_used_mb} / {ram_total_mb} MB)")
        return True

    except Exception as e:
        print_result("CPU/RAM collection", False, str(e))
        return False


async def test_wireguard_peers():
    """Test WireGuard peers collection."""
    print_header("TEST 3: WireGuard Active Peers")

    try:
        process = await asyncio.create_subprocess_exec(
            "wg",
            "show",
            "wg0",
            "latest-handshakes",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)

        if process.returncode == 0:
            output = stdout.decode()
            now = int(datetime.now().timestamp())
            active_count = 0

            for line in output.splitlines():
                parts = line.split()
                if len(parts) == 2:
                    try:
                        handshake_time = int(parts[1])
                        if handshake_time > 0 and (now - handshake_time) < 180:
                            active_count += 1
                    except ValueError:
                        continue

            print_result(
                "WireGuard peers", True, f"{active_count} peers with recent handshake (< 3 min)"
            )
            return True
        else:
            print_result(
                "WireGuard command",
                False,
                stderr.decode().strip() or f"Return code: {process.returncode}",
            )
            return False

    except asyncio.TimeoutError:
        print_result("WireGuard command", False, "Timeout after 5 seconds")
        return False
    except Exception as e:
        print_result("WireGuard command", False, str(e))
        return False


async def test_service_status():
    """Test service status collection."""
    print_header("TEST 4: Service Status (systemctl)")

    services = {
        "WireGuard": "wg-quick@wg0",
        "Outline": "outline-ss-server",
        "dnsproxy": "dnsproxy",
    }

    all_passed = True

    for name, service in services.items():
        try:
            process = await asyncio.create_subprocess_exec(
                "systemctl",
                "is-active",
                service,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=3)

            status = stdout.decode().strip()
            is_active = status == "active"

            if is_active:
                print_result(f"{name} ({service})", True, "ACTIVE")
            else:
                print_result(f"{name} ({service})", True, f"inactive (normal si no lo usas)")

        except asyncio.TimeoutError:
            print_result(f"{name} ({service})", False, "Timeout")
            all_passed = False
        except Exception as e:
            print_result(f"{name} ({service})", False, str(e))
            all_passed = False

    return all_passed


async def test_uptime():
    """Test uptime collection."""
    print_header("TEST 5: Server Uptime")

    try:
        import psutil

        boot_time = await asyncio.to_thread(psutil.boot_time)
        uptime_seconds = datetime.now().timestamp() - boot_time
        uptime_hours = uptime_seconds / 3600

        print_result("Uptime", True, f"{uptime_hours:.1f} hours ({uptime_hours/24:.1f} days)")
        return True

    except Exception as e:
        print_result("Uptime collection", False, str(e))
        return False


async def test_redis():
    """Test Redis connection."""
    print_header("TEST 6: Redis Connection")

    try:
        import redis.asyncio as redis

        from config import settings

        client = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Test connection
        await client.ping()

        # Test set/get
        test_key = "test:latency:check"
        await client.setex(test_key, 60, "test_value")
        value = await client.get(test_key)
        await client.delete(test_key)

        await client.close()

        if value == "test_value":
            print_result("Redis connection", True, f"Connected to {settings.REDIS_URL}")
            return True
        else:
            print_result("Redis test", False, "Get/Set mismatch")
            return False

    except Exception as e:
        print_result("Redis connection", False, str(e))
        return False


async def main():
    """Run all tests."""
    print("\n" + "█" * 50)
    print("  SERVER METRICS VALIDATION TEST")
    print("  uSipipo VPN - Latency Monitoring")
    print("█" * 50)
    print(f"\n  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Server: {subprocess.getoutput('hostname').strip()}")

    results = []

    # Run tests
    results.append(("Ping", await test_ping()))
    results.append(("CPU/RAM", await test_cpu_ram()))
    results.append(("WireGuard", await test_wireguard_peers()))
    results.append(("Services", await test_service_status()))
    results.append(("Uptime", await test_uptime()))
    results.append(("Redis", await test_redis()))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    print("\n" + "-" * 50)
    print(f"  Total: {passed}/{total} tests passed")
    print("-" * 50)

    if passed == total:
        print("\n✅ All tests passed! Your VPS is ready for latency monitoring.")
        print("\nNext steps:")
        print("  1. Start the bot: python main.py")
        print("  2. Use /latency command to view metrics")
        print("  3. Check Mini App API: GET /api/v1/miniapp/latency")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        print("\nReview the errors above and fix before deploying.")
        print("Some failures may be acceptable (e.g., Outline/dnsproxy if not used).")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
