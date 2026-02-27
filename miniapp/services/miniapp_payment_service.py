"""
Service for handling payments in Mini App.

Author: uSipipo Team
Version: 1.0.0
"""

import urllib.parse
from typing import Optional

from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from utils.logger import logger


class MiniAppPaymentService:
    """Service for creating payment intents in Mini App."""

    def __init__(self, data_package_service: DataPackageService):
        self.data_package_service = data_package_service

    def get_package_option(self, package_type: str):
        """Get package option by type."""
        for opt in PACKAGE_OPTIONS:
            if opt.package_type.value == package_type:
                return opt
        return None

    def get_slot_option(self, slots: int):
        """Get slot option by count."""
        for opt in SLOT_OPTIONS:
            if opt.slots == slots:
                return opt
        return None

    def create_stars_invoice_url(
        self,
        user_id: int,
        product_type: str,
        product_id: str,
    ) -> Optional[str]:
        """
        Create a Telegram Stars invoice URL for Mini App.

        Returns a direct invoice URL that can be opened with Telegram.WebApp.openInvoice()
        """
        try:
            if product_type == "package":
                package_opt = self.get_package_option(product_id)
                if not package_opt:
                    logger.error(f"Package not found: {product_id}")
                    return None

                # Create invoice parameters
                title = f"Paquete {package_opt.name}"
                description = f"{package_opt.data_gb} GB de datos VPN"
                payload = f"data_package_{product_id}_{user_id}"
                amount = package_opt.stars

            elif product_type == "slots":
                # Parse slots count from product_id (format: "slots_N")
                slots_str = product_id.replace("slots_", "")
                slots = int(slots_str)
                slot_opt = self.get_slot_option(slots)

                if not slot_opt:
                    logger.error(f"Slot option not found: {slots}")
                    return None

                title = slot_opt.name
                description = f"Añade {slots} claves VPN adicionales"
                payload = f"key_slots_{slots}_{user_id}"
                amount = slot_opt.stars
            else:
                logger.error(f"Invalid product type: {product_type}")
                return None

            # Build invoice URL for Telegram WebApp
            # Format: tg://invoice?provider_token=&currency=XTR&prices=[...]
            import json

            prices = [{"label": title, "amount": amount}]
            prices_json = urllib.parse.quote(json.dumps(prices))

            # Create the invoice URL for Telegram Mini App
            # This will be handled by the Telegram WebApp's openInvoice method
            invoice_url = (
                f"tg://invoice?"
                f"title={urllib.parse.quote(title)}&"
                f"description={urllib.parse.quote(description)}&"
                f"payload={urllib.parse.quote(payload)}&"
                f"provider_token=&"
                f"currency=XTR&"
                f"prices={prices_json}"
            )

            logger.info(
                f"Created Stars invoice for user {user_id}: {product_type}={product_id}, amount={amount}"
            )
            return invoice_url

        except Exception as e:
            logger.error(f"Error creating Stars invoice: {e}")
            return None

    async def create_crypto_order(
        self,
        user_id: int,
        product_type: str,
        product_id: str,
    ) -> Optional[dict]:
        """
        Create a crypto payment order.

        Returns order details including wallet address and QR code.
        """
        try:
            from application.services.common.container import get_service
            from application.services.crypto_payment_service import CryptoPaymentService
            from application.services.wallet_management_service import (
                WalletManagementService,
            )
            from utils.qr_generator import QrGenerator

            wallet_service = get_service(WalletManagementService)
            payment_service = get_service(CryptoPaymentService)

            # Assign wallet to user
            wallet = await wallet_service.assign_wallet(
                user_id, label=f"miniapp-user-{user_id}"
            )

            if not wallet:
                logger.error(f"Could not assign wallet to user {user_id}")
                return None

            # Determine product details and amount
            if product_type == "package":
                package_opt = self.get_package_option(product_id)
                if not package_opt:
                    logger.error(f"Package not found: {product_id}")
                    return None

                amount_usdt = package_opt.data_gb / 10  # 1 USDT = 10 GB

                # Create order
                order = await payment_service.create_order(
                    user_id=user_id,
                    package_type=product_id,
                    amount_usdt=amount_usdt,
                    wallet_address=wallet.address,
                )

            elif product_type == "slots":
                slots_str = product_id.replace("slots_", "")
                slots = int(slots_str)
                slot_opt = self.get_slot_option(slots)

                if not slot_opt:
                    logger.error(f"Slot option not found: {slots}")
                    return None

                # Tasa: 1 USDT = 120 Stars
                amount_usdt = slot_opt.stars / 120

                # Create order
                order = await payment_service.create_order(
                    user_id=user_id,
                    package_type=f"slots_{slots}",
                    amount_usdt=amount_usdt,
                    wallet_address=wallet.address,
                )
            else:
                logger.error(f"Invalid product type: {product_type}")
                return None

            # Generate QR code
            qr_filename = f"miniapp_payment_{order.id}"
            qr_path = QrGenerator.generate_payment_qr(
                wallet_address=wallet.address,
                amount=amount_usdt,
                filename=qr_filename
            )

            # Build QR code URL (relative to Mini App)
            qr_url = f"/miniapp/static/qr/{qr_filename}.png"

            logger.info(
                f"Created crypto order {order.id} for user {user_id}: {product_type}={product_id}, amount={amount_usdt} USDT"
            )

            return {
                "order_id": str(order.id),
                "wallet_address": wallet.address,
                "amount_usdt": amount_usdt,
                "qr_code_url": qr_url,
                "expires_at": order.expires_at.isoformat() if order.expires_at else None,
            }

        except Exception as e:
            logger.error(f"Error creating crypto order: {e}", exc_info=True)
            return None
