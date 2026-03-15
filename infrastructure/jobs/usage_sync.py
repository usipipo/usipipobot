import uuid
from typing import Any, Dict, cast

from telegram.ext import ContextTypes

from application.services.vpn_service import VpnService
from utils.logger import logger


async def sync_vpn_usage_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Consulta el consumo de datos en los servidores VPN
    y actualiza la base de datos local cada 30 minutos.
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    vpn_service: VpnService = data["vpn_service"]

    try:
        logger.info("📊 Iniciando sincronización de consumo de datos...")

        keys = await vpn_service.get_all_active_keys()

        if not keys:
            logger.info("ℹ️ No hay llaves activas para sincronizar.")
            return

        synced_count = 0
        error_count = 0

        for key in keys:
            try:
                current_usage = await vpn_service.fetch_real_usage(key)
                if key.id is not None:
                    await vpn_service.update_key_usage(uuid.UUID(key.id), current_usage)
                    synced_count += 1
                else:
                    logger.warning(f"⚠️ Llave sin ID, omitiendo: {key.name}")

            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error sincronizando llave {key.id}: {e}")

        logger.info(
            f"✅ Sincronización completada. " f"Exitosas: {synced_count}, Errores: {error_count}"
        )

    except Exception as e:
        logger.error(f"❌ Error crítico en sync_vpn_usage_job: {e}")
