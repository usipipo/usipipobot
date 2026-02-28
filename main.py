"""
Punto de entrada principal del bot uSipipo VPN Manager.

Author: uSipipo Team
"""

import sys
import threading
from typing import Any

from telegram.ext import Application, ApplicationBuilder

from application.services.common.container import get_service
from application.services.crypto_payment_service import CryptoPaymentService
from application.services.data_package_service import DataPackageService
from application.services.referral_service import ReferralService
from application.services.vpn_service import VpnService
from config import settings
from infrastructure.jobs.crypto_order_expiration_job import expire_crypto_orders_job
from infrastructure.jobs.crypto_order_expiration_job import expire_crypto_orders_job
from infrastructure.jobs.key_cleanup_job import key_cleanup_job
from infrastructure.jobs.memory_cleanup_job import memory_cleanup_job
from infrastructure.jobs.package_expiration_job import expire_packages_job
from infrastructure.jobs.usage_sync import sync_vpn_usage_job
from infrastructure.persistence.database import close_database, init_database
from telegram_bot.handlers.handler_initializer import initialize_handlers
from utils.logger import logger
from version import __version__


async def startup():
    """Inicialización de la aplicación."""
    logger.info("🔌 Inicializando conexión a base de datos...")
    await init_database()
    logger.info("✅ Base de datos inicializada.")


async def shutdown():
    """Limpieza al cerrar la aplicación."""
    logger.info("🔌 Cerrando conexión a base de datos...")
    await close_database()


def run_api_server():
    """Ejecuta el servidor API en un hilo separado."""
    import asyncio

    import uvicorn

    from infrastructure.api.server import create_app

    app = create_app()
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
        access_log=True,
    )


def main():
    """Función principal del bot."""
    logger.info(f"🚀 Iniciando uSipipo VPN Manager v{__version__}...")

    if not settings.TELEGRAM_TOKEN:
        logger.error("❌ No se encontró el TELEGRAM_TOKEN en el archivo .env")
        sys.exit(1)

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    logger.info(f"🌐 API server iniciado en {settings.API_HOST}:{settings.API_PORT}")

    async def post_init_callback(app: Application) -> None:
        """Callback ejecutado después de inicializar la aplicación."""
        try:
            vpn_service = get_service(VpnService)
            referral_service = get_service(ReferralService)
            data_package_service = get_service(DataPackageService)
            crypto_payment_service = get_service(CryptoPaymentService)
            logger.info("✅ Contenedor de dependencias configurado correctamente.")
        except Exception as e:
            logger.critical(f"❌ Error al inicializar el contenedor: {e}")
            sys.exit(1)

        await startup()

        if settings.DUCKDNS_DOMAIN and settings.DUCKDNS_TOKEN:
            try:
                from infrastructure.dns.duckdns_service import DuckDNSService

                duckdns = DuckDNSService(
                    domain=settings.DUCKDNS_DOMAIN, token=settings.DUCKDNS_TOKEN
                )
                await duckdns.update_ip()
                logger.info(f"🌐 DuckDNS configurado: {duckdns.get_public_url()}")
                logger.info(f"📡 Webhook URL: {settings.webhook_url}")
                await duckdns.close()
            except Exception as e:
                logger.warning(f"⚠️ No se pudo actualizar DuckDNS: {e}")

        job_queue = app.job_queue
        if job_queue is None:
            logger.error("❌ Job queue no disponible")
            return

        job_queue.run_repeating(
            sync_vpn_usage_job,
            interval=1800,
            first=60,
            data={"vpn_service": vpn_service},
        )
        logger.info("⏰ Job de cuota programado.")

        job_queue.run_repeating(
            key_cleanup_job, interval=3600, first=30, data={"vpn_service": vpn_service}
        )
        logger.info("⏰ Job de limpieza de llaves programado.")

        job_queue.run_repeating(
            expire_packages_job,
            interval=86400,
            first=10,
            data={"data_package_service": data_package_service},
        )
        logger.info("⏰ Job de expiración de paquetes programado.")

        job_queue.run_repeating(
            expire_crypto_orders_job,
            interval=60,
            first=30,
            data={
                "crypto_payment_service": crypto_payment_service,
                "bot": app.bot,
            },
        )
        logger.info("⏰ Job de expiración de órdenes crypto programado.")

        interval_minutes = settings.MEMORY_CLEANUP_INTERVAL_MINUTES
        job_queue.run_repeating(
            memory_cleanup_job,
            interval=interval_minutes * 60,
            first=120,
            data={},
        )
        logger.info(
            f"⏰ Job de limpieza de RAM programado cada {interval_minutes} minutos "
            f"(umbral: {settings.MEMORY_CLEANUP_THRESHOLD_PERCENT}%)"
        )

        handlers = initialize_handlers(vpn_service, referral_service)
        for handler in handlers:
            app.add_handler(handler)

        logger.info("🤖 Bot en línea y escuchando mensajes...")

    async def post_stop_callback(app: Application) -> None:
        """Callback ejecutado después de detener la aplicación."""
        await shutdown()

    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_TOKEN)
        .post_init(post_init_callback)
        .post_stop(post_stop_callback)
        .build()
    )

    application.run_polling()


if __name__ == "__main__":
    main()
