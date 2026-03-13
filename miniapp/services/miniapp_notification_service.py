"""
Service for sending payment notifications from Mini App to Telegram Bot.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import Optional

from telegram import Bot

from config import settings
from utils.logger import logger


class MiniAppNotificationService:
    """
    Service for sending notifications from Mini App to Telegram users.
    
    This service bridges the Mini App web interface with the Telegram Bot,
    allowing the bot to send payment invoices and notifications to users.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_stars_invoice(
        self,
        user_id: int,
        title: str,
        description: str,
        payload: str,
        amount: int,
    ) -> bool:
        """
        Send a Telegram Stars invoice to a user.

        Args:
            user_id: Telegram user ID
            title: Invoice title
            description: Invoice description
            payload: Unique payload for tracking
            amount: Amount in Stars

        Returns:
            True if invoice was sent successfully, False otherwise
        """
        try:
            from telegram import LabeledPrice

            await self.bot.send_invoice(
                chat_id=user_id,
                title=title,
                description=description,
                payload=payload,
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # Telegram Stars currency
                prices=[LabeledPrice(title, amount)],
            )

            logger.info(
                f"⭐ Stars invoice sent to user {user_id}: {title} ({amount} XTR)"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending stars invoice to user {user_id}: {e}", exc_info=True
            )
            return False

    async def send_crypto_payment_notification(
        self,
        user_id: int,
        order_id: str,
        wallet_address: str,
        amount_usdt: float,
        qr_code_url: str,
        product_name: str,
    ) -> bool:
        """
        Send crypto payment notification with QR code to user.

        Args:
            user_id: Telegram user ID
            order_id: Order identifier
            wallet_address: USDT wallet address
            amount_usdt: Amount to pay in USDT
            qr_code_url: URL to QR code image
            product_name: Name of product being purchased

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            from pathlib import Path

            # Build full QR code URL
            full_qr_url = f"{settings.PUBLIC_URL or 'http://localhost:8000'}{qr_code_url}"

            message = (
                f"💰 *Pago con USDT - {product_name}*\n\n"
                f"📋 Orden: `{order_id}`\n\n"
                f"💳 Wallet:\n"
                f"`{wallet_address}`\n\n"
                f"💵 Monto: *{amount_usdt:.2f} USDT*\n\n"
                f"⚠️ *Importante:*\n"
                f"• Usa la red *BSC (BEP20)*\n"
                f"• Envía el monto *exacto*\n"
                f"• El pago se confirmará en ~5 minutos\n\n"
                f"📱 Escanea el QR o copia la dirección"
            )

            # Send photo with QR code
            await self.bot.send_photo(
                chat_id=user_id,
                photo=full_qr_url,
                caption=message,
                parse_mode="Markdown",
            )

            logger.info(
                f"💰 Crypto payment notification sent to user {user_id}: "
                f"order {order_id}, {amount_usdt} USDT"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending crypto payment notification to user {user_id}: {e}",
                exc_info=True,
            )
            return False

    async def send_payment_confirmation(
        self,
        user_id: int,
        product_name: str,
        payment_method: str,
    ) -> bool:
        """
        Send payment confirmation notification.

        Args:
            user_id: Telegram user ID
            product_name: Name of purchased product
            payment_method: Payment method used (Stars/Crypto)

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            emoji = "⭐" if payment_method == "stars" else "💰"

            message = (
                f"✅ *¡Pago Confirmado!*\n\n"
                f"{emoji} Producto: *{product_name}*\n"
                f"💳 Método: *{payment_method}*\n\n"
                f"Tu producto ha sido activado inmediatamente.\n"
                f"Revisa tu sección de claves VPN para ver los cambios."
            )

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
            )

            logger.info(
                f"✅ Payment confirmation sent to user {user_id}: "
                f"{product_name} via {payment_method}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending payment confirmation to user {user_id}: {e}",
                exc_info=True,
            )
            return False

    async def send_payment_pending(
        self,
        user_id: int,
        product_name: str,
        payment_method: str,
        estimated_time: str = "5 minutos",
    ) -> bool:
        """
        Send payment pending notification (for crypto payments).

        Args:
            user_id: Telegram user ID
            product_name: Name of purchased product
            payment_method: Payment method used
            estimated_time: Estimated confirmation time

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            message = (
                f"⏳ *Pago Pendiente de Confirmación*\n\n"
                f"💰 Producto: *{product_name}*\n"
                f"💳 Método: *{payment_method}*\n\n"
                f"Tu pago está siendo procesado en la blockchain.\n"
                f"⏱️ Tiempo estimado: *{estimated_time}*\n\n"
                f"Te notificaremos cuando sea confirmado."
            )

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
            )

            logger.info(
                f"⏳ Payment pending notification sent to user {user_id}: "
                f"{product_name} via {payment_method}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending payment pending notification to user {user_id}: {e}",
                exc_info=True,
            )
            return False


# Global instance (initialized when API starts)
_notification_service: Optional[MiniAppNotificationService] = None


def get_notification_service() -> Optional[MiniAppNotificationService]:
    """
    Get the notification service instance.
    
    Returns:
        MiniAppNotificationService instance or None if not initialized
    """
    return _notification_service


def init_notification_service(bot: Bot) -> MiniAppNotificationService:
    """
    Initialize the notification service with a bot instance.
    
    Args:
        bot: Telegram Bot instance
    
    Returns:
        MiniAppNotificationService instance
    """
    global _notification_service
    _notification_service = MiniAppNotificationService(bot)
    logger.info("📬 MiniApp Notification Service initialized")
    return _notification_service
