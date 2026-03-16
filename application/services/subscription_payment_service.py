"""Subscription payment service for orchestrating subscription payments (Stars + Crypto)."""

import uuid
from typing import TYPE_CHECKING, Optional

from telegram import Bot

from config import settings
from utils.logger import logger

if TYPE_CHECKING:
    from application.services.crypto_payment_service import CryptoPaymentService
    from application.services.subscription_service import SubscriptionService


class SubscriptionPaymentService:
    """Orchestrates subscription payments via Telegram Stars and Crypto."""

    def __init__(
        self,
        subscription_service: "SubscriptionService",
        crypto_payment_service: Optional["CryptoPaymentService"] = None,
    ):
        self.subscription_service = subscription_service
        self.crypto_payment_service = crypto_payment_service

    async def create_stars_invoice(
        self,
        user_id: int,
        plan_type: str,
        transaction_id: str,
    ) -> dict:
        """
        Create a Telegram Stars invoice for a subscription.

        Args:
            user_id: Telegram user ID
            plan_type: Type of plan (one_month, three_months, six_months)
            transaction_id: Unique transaction identifier

        Returns:
            dict with success status and invoice details

        Raises:
            ValueError: If plan is invalid or user already has subscription
        """
        plan_option = self.subscription_service.get_plan_option(plan_type)

        if not plan_option:
            raise ValueError(f"Plan no válido: {plan_type}")

        # Check existing subscription
        is_premium = await self.subscription_service.is_premium_user(user_id, user_id)
        if is_premium:
            raise ValueError("Ya tienes una suscripción activa")

        # Create invoice payload
        payload = f"subscription_{plan_type}_{user_id}_{transaction_id}"

        # Send invoice via Telegram Bot
        invoice_sent = await self._send_stars_invoice(
            user_id=user_id,
            title=f"Suscripción {plan_option.name}",
            description=f"{plan_option.duration_months} meses de datos ilimitados",
            payload=payload,
            amount=plan_option.stars,
        )

        if not invoice_sent:
            raise Exception("No se pudo crear la factura")

        logger.info(
            f"⭐ Stars invoice created for subscription: "
            f"user {user_id}, plan {plan_type}, {plan_option.stars} stars"
        )

        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount_stars": plan_option.stars,
            "payload": payload,
        }

    async def _send_stars_invoice(
        self,
        user_id: int,
        title: str,
        description: str,
        payload: str,
        amount: int,
    ) -> bool:
        """Send Telegram Stars invoice to user."""
        try:
            from telegram import LabeledPrice

            bot = Bot(token=settings.TELEGRAM_TOKEN)

            await bot.send_invoice(
                chat_id=user_id,
                title=title,
                description=description,
                payload=payload,
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # Telegram Stars currency
                prices=[LabeledPrice(title, amount)],
            )

            await bot.close()

            logger.info(f"⭐ Stars invoice sent to user {user_id}: {title} ({amount} XTR)")
            return True

        except Exception as e:
            logger.error(f"Error sending stars invoice to user {user_id}: {e}", exc_info=True)
            return False

    async def create_crypto_order(
        self,
        user_id: int,
        plan_type: str,
        transaction_id: str,
    ) -> dict:
        """
        Create a crypto payment order for a subscription.

        Args:
            user_id: Telegram user ID
            plan_type: Type of plan (one_month, three_months, six_months)
            transaction_id: Unique transaction identifier

        Returns:
            dict with order details and payment instructions

        Raises:
            ValueError: If plan is invalid or user already has subscription
        """
        plan_option = self.subscription_service.get_plan_option(plan_type)

        if not plan_option:
            raise ValueError(f"Plan no válido: {plan_type}")

        # Check existing subscription
        is_premium = await self.subscription_service.is_premium_user(user_id, user_id)
        if is_premium:
            raise ValueError("Ya tienes una suscripción activa")

        # Calculate USDT amount
        usdt_amount = plan_option.usdt

        # Generate wallet address and QR code URL
        # For now, use a placeholder - in production this would come from a payment gateway
        wallet_address = (
            settings.TRON_DEALER_WALLET_ADDRESS
            if hasattr(settings, "TRON_DEALER_WALLET_ADDRESS")
            else "0x..."
        )
        qr_code_url = f"/api/v1/crypto/qr/{transaction_id}"

        logger.info(
            f"💰 Crypto order created for subscription: "
            f"user {user_id}, plan {plan_type}, {usdt_amount} USDT"
        )

        return {
            "success": True,
            "transaction_id": transaction_id,
            "plan_type": plan_type,
            "amount_usdt": usdt_amount,
            "wallet_address": wallet_address,
            "qr_code_url": qr_code_url,
        }
