"""
Punto de entrada principal del bot uSipipo VPN Manager.

Author: uSipipo Team
Version: 2.0.0
"""

import sys
import asyncio
from utils.logger import logger
from telegram.ext import ApplicationBuilder

from config import settings
from application.services.common.container import get_service
from application.services.vpn_service import VpnService
from application.services.payment_service import PaymentService

from infrastructure.persistence.database import init_database, close_database
from telegram_bot.handlers.handler_initializer import initialize_handlers
from infrastructure.jobs.usage_sync import sync_vpn_usage_job
from infrastructure.jobs.key_cleanup_job import key_cleanup_job
from infrastructure.jobs.package_expiration_job import expire_packages_job
from application.services.data_package_service import DataPackageService


async def startup():
    """Inicialización de la aplicación."""
    logger.info("🔌 Inicializando conexión a base de datos...")
    await init_database()


async def shutdown():
    """Limpieza al cerrar la aplicación."""
    logger.info("🔌 Cerrando conexión a base de datos...")
    await close_database()


def main():
    """Función principal del bot."""
    logger.info("🚀 Iniciando uSipipo VPN Manager Bot...")

    try:
        vpn_service = get_service(VpnService)
        payment_service = get_service(PaymentService)
        data_package_service = get_service(DataPackageService)
        logger.info("✅ Contenedor de dependencias configurado correctamente.")
    except Exception as e:
        logger.critical(f"❌ Error al inicializar el contenedor: {e}")
        sys.exit(1)

    if not settings.TELEGRAM_TOKEN:
        logger.error("❌ No se encontró el TELEGRAM_TOKEN en el archivo .env")
        sys.exit(1)

    async def post_init_callback(app):
        """Callback ejecutado después de inicializar la aplicación."""
        await startup()

    async def post_shutdown_callback(app):
        """Callback ejecutado después de cerrar la aplicación."""
        await shutdown()

    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_TOKEN)
        .post_init(post_init_callback)
        .post_shutdown(post_shutdown_callback)
        .build()
    )

    job_queue = application.job_queue

    job_queue.run_repeating(
        sync_vpn_usage_job,
        interval=1800,
        first=60,
        data={'vpn_service': vpn_service}
    )
    logger.info("⏰ Job de cuota programado.")

    job_queue.run_repeating(
        key_cleanup_job,
        interval=3600,
        first=30,
        data={'vpn_service': vpn_service}
    )
    logger.info("⏰ Job de limpieza de llaves programado.")

    job_queue.run_repeating(
        expire_packages_job,
        interval=86400,
        first=10,
        data={'data_package_service': data_package_service}
    )
    logger.info("⏰ Job de expiración de paquetes programado.")

    handlers = initialize_handlers(vpn_service, payment_service)
    for handler in handlers:
        application.add_handler(handler)

    logger.info("🤖 Bot en línea y escuchando mensajes...")
    application.run_polling()


if __name__ == "__main__":
    main()
