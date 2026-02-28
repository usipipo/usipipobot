"""
Job para expirar órdenes de pago crypto que han pasado su tiempo límite.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import Any, Dict, cast

from telegram.ext import ContextTypes

from application.services.crypto_payment_service import CryptoPaymentService
from utils.logger import logger


async def expire_crypto_orders_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que marca como expiradas las órdenes crypto pendientes
    que han pasado su tiempo límite y notifica a los usuarios.

    Debe ser configurado para ejecutarse cada minuto.
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    crypto_payment_service: CryptoPaymentService = data["crypto_payment_service"]
    bot = data.get("bot")

    try:
        logger.debug("💰 Iniciando job de expiración de órdenes crypto...")

        # Verificar que el repositorio esté disponible
        if not crypto_payment_service.crypto_order_repo:
            logger.warning("⚠️ Crypto order repository no disponible")
            return

        # Obtener órdenes pendientes
        pending_orders = await crypto_payment_service.crypto_order_repo.get_pending()

        expired_count = 0
        notified_count = 0

        for order in pending_orders:
            if order.is_expired:
                # Marcar como expirada en la base de datos
                success = await crypto_payment_service.crypto_order_repo.mark_expired(
                    order.id
                )

                if success:
                    expired_count += 1
                    logger.info(
                        f"⏰ Orden {order.id} marcada como expirada (user: {order.user_id})"
                    )

                    # Liberar wallet para reutilización
                    if order.wallet_address:
                        logger.info(
                            f"♻️ Wallet {order.wallet_address[:10]}... liberada "
                            f"para reutilización (orden expirada)"
                        )

                    # Notificar al usuario
                    if bot:
                        try:
                            # Determinar si era slots o paquete
                            product_name = "paquete de datos"
                            if order.package_type.startswith("slots_"):
                                slots = order.package_type.split("_")[1]
                                product_name = f"+{slots} claves"

                            message = (
                                f"⏰ *Orden Expirada*\n\n"
                                f"Tu orden de pago para *{product_name}* ha expirado "
                                f"porque no se recibió el pago en el tiempo límite (30 minutos).\n\n"
                                f"💰 Monto: {order.amount_usdt} USDT\n"
                                f"📋 Wallet: `{order.wallet_address[:10]}...{order.wallet_address[-8:]}`\n\n"
                                f"Si aún deseas adquirir el producto, por favor inicia una nueva orden."
                            )

                            await bot.send_message(
                                chat_id=order.user_id,
                                text=message,
                                parse_mode="Markdown",
                            )
                            notified_count += 1
                            logger.info(
                                f"📨 Usuario {order.user_id} notificado de orden expirada"
                            )
                        except Exception as e:
                            logger.error(
                                f"❌ Error notificando al usuario {order.user_id}: {e}"
                            )

        if expired_count > 0:
            logger.info(
                f"✅ Job completado: {expired_count} órdenes expiradas, {notified_count} usuarios notificados"
            )
        else:
            logger.debug("✅ No hay órdenes expiradas")

    except Exception as e:
        logger.error(f"❌ Error en job de expiración de órdenes crypto: {e}")
