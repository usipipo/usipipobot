"""
Job para limpieza automática de memoria RAM.
Libera caché y buffers cuando el uso de RAM supera los umbrales configurados.

Author: uSipipo Team
Version: 1.0.0
"""

import os
import subprocess
from typing import Any, Dict, cast

from telegram.ext import ContextTypes

from config import settings
from utils.logger import logger


def get_memory_info() -> Dict[str, Any]:
    """
    Obtiene información de uso de memoria desde /proc/meminfo.

    Returns:
        Dict con total, available, used, porcentajes y estadísticas
    """
    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()

        lines = meminfo.strip().split("\n")
        data: Dict[str, int] = {}

        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                try:
                    value = int(parts[1])
                    data[key] = value
                except ValueError:
                    continue

        total = data.get("MemTotal", 0)
        available = data.get("MemAvailable", data.get("MemFree", 0))
        buffers = data.get("Buffers", 0)
        cached = data.get("Cached", 0)
        sreclaimable = data.get("SReclaimable", 0)

        used = total - available
        used_percent = (used / total * 100) if total > 0 else 0
        available_percent = (available / total * 100) if total > 0 else 0

        return {
            "total_kb": total,
            "available_kb": available,
            "used_kb": used,
            "buffers_kb": buffers,
            "cached_kb": cached,
            "sreclaimable_kb": sreclaimable,
            "used_percent": round(used_percent, 2),
            "available_percent": round(available_percent, 2),
            "total_gb": round(total / 1024 / 1024, 2),
            "used_gb": round(used / 1024 / 1024, 2),
            "available_gb": round(available / 1024 / 1024, 2),
        }
    except Exception as e:
        logger.error(f"Error leyendo meminfo: {e}")
        return {}


def drop_caches(level: int = 1) -> bool:
    """
    Limpia cachés del sistema Linux.

    Args:
        level: 1 - pagecache, 2 - dentries/inodes, 3 - all

    Returns:
        True si tuvo éxito, False si falló
    """
    try:
        if level not in [1, 2, 3]:
            level = 1

        result = subprocess.run(
            ["sync"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.warning(f"sync falló: {result.stderr}")

        with open("/proc/sys/vm/drop_caches", "w") as f:
            f.write(str(level))

        return True
    except PermissionError:
        logger.error(
            "Permiso denegado para limpiar caché. "
            "Ejecutar como root o añadir a sudoers."
        )
        return False
    except Exception as e:
        logger.error(f"Error limpiando caché: {e}")
        return False


def compact_memory() -> bool:
    """
    Compacta la memoria para reducir fragmentación.

    Returns:
        True si tuvo éxito
    """
    try:
        with open("/proc/sys/vm/compact_memory", "w") as f:
            f.write("1")
        return True
    except Exception as e:
        logger.debug(f"No se pudo compactar memoria: {e}")
        return False


async def memory_cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que monitorea y limpia RAM cuando es necesario.

    Se ejecuta periódicamente según MEMORY_CLEANUP_INTERVAL_MINUTES.
    """
    if not settings.MEMORY_CLEANUP_ENABLED:
        logger.debug("🚫 Limpieza de RAM deshabilitada")
        return

    try:
        mem_info = get_memory_info()

        if not mem_info:
            logger.warning("⚠️ No se pudo obtener información de memoria")
            return

        used_percent = mem_info.get("used_percent", 0)
        threshold = settings.MEMORY_CLEANUP_THRESHOLD_PERCENT
        critical = settings.MEMORY_CLEANUP_CRITICAL_PERCENT

        logger.debug(
            f"🧠 RAM: {mem_info['used_gb']:.2f}/{mem_info['total_gb']:.2f} GB "
            f"({used_percent}%)"
        )

        if used_percent < threshold:
            return

        logger.info(
            f"🚨 RAM alta detectada: {used_percent}% "
            f"(umbral: {threshold}%)"
        )

        mem_before = dict(mem_info)

        if used_percent >= critical:
            logger.warning(f"🔥 Nivel CRÍTICO de RAM: {used_percent}%")
            success = drop_caches(level=3)
            compact_memory()
            level_str = "agresiva (nivel 3)"
        else:
            success = drop_caches(level=1)
            level_str = "estándar (nivel 1)"

        if not success:
            logger.error("❌ Falló la limpieza de RAM")
            return

        mem_after = get_memory_info()

        if mem_after:
            freed_kb = mem_after.get("available_kb", 0) - mem_before.get("available_kb", 0)
            freed_mb = freed_kb / 1024 if freed_kb > 0 else 0

            logger.info(
                f"✅ Limpieza {level_str} completada. "
                f"RAM liberada: {freed_mb:.1f} MB. "
                f"Ahora: {mem_after['used_percent']}%"
            )

            if settings.MEMORY_NOTIFY_ADMIN and context.bot:
                await notify_admin(context, mem_before, mem_after, level_str)
        else:
            logger.info(f"✅ Limpieza {level_str} completada")

    except Exception as e:
        logger.error(f"❌ Error en memory_cleanup_job: {e}")


async def notify_admin(
    context: ContextTypes.DEFAULT_TYPE,
    before: Dict[str, Any],
    after: Dict[str, Any],
    cleanup_type: str
) -> None:
    """
    Notifica al administrador sobre la limpieza de RAM.

    Args:
        context: Contexto de Telegram
        before: Estado de memoria antes de limpiar
        after: Estado de memoria después de limpiar
        cleanup_type: Tipo de limpieza realizada
    """
    try:
        freed_mb = (after.get("available_kb", 0) - before.get("available_kb", 0)) / 1024

        message = (
            f"🧹 *Limpieza de RAM ejecutada*\n\n"
            f"Tipo: `{cleanup_type}`\n"
            f"Antes: `{before.get('used_percent')}%` "
            f"({before.get('used_gb'):.2f} GB usados)\n"
            f"Después: `{after.get('used_percent')}%` "
            f"({after.get('used_gb'):.2f} GB usados)\n"
            f"Liberado: `{freed_mb:.1f} MB`"
        )

        await context.bot.send_message(
            chat_id=settings.ADMIN_ID,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"⚠️ No se pudo notificar al admin: {e}")


async def force_memory_cleanup(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
    """
    Fuerza una limpieza de RAM inmediata (para comando manual).

    Args:
        context: Contexto de Telegram

    Returns:
        Dict con resultados de la limpieza
    """
    try:
        mem_before = get_memory_info()

        if not mem_before:
            return {"success": False, "error": "No se pudo leer memoria"}

        success = drop_caches(level=3)
        compact_memory()

        if not success:
            return {"success": False, "error": "Falló drop_caches"}

        mem_after = get_memory_info()

        freed_kb = mem_after.get("available_kb", 0) - mem_before.get("available_kb", 0)
        freed_mb = freed_kb / 1024 if freed_kb > 0 else 0

        return {
            "success": True,
            "before_percent": mem_before.get("used_percent"),
            "after_percent": mem_after.get("used_percent"),
            "freed_mb": round(freed_mb, 2),
            "before_gb": mem_before.get("used_gb"),
            "after_gb": mem_after.get("used_gb"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
