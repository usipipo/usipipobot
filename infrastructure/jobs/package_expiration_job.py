"""
Job para expirar paquetes de datos que han pasado su fecha de expiración.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import cast, Any, Dict

from telegram.ext import ContextTypes

from application.services.data_package_service import DataPackageService
from config import settings
from utils.logger import logger


async def expire_packages_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que desactiva paquetes expirados.

    Debe ser configurado para ejecutarse diariamente.
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    data_package_service: DataPackageService = data["data_package_service"]

    try:
        logger.info("📦 Iniciando job de expiración de paquetes...")

        expired_count = await data_package_service.expire_old_packages(
            admin_user_id=settings.ADMIN_ID
        )

        logger.info(f"✅ Job completado: {expired_count} paquetes expirados")

    except Exception as e:
        logger.error(f"❌ Error en job de expiración de paquetes: {e}")
