"""
Service for handling payments in Mini App.

Author: uSipipo Team
Version: 1.0.0
"""

import urllib.parse
from typing import TYPE_CHECKING, Optional

from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from infrastructure.api_clients.client_tron_dealer import TronDealerApiError
from utils.logger import logger

if TYPE_CHECKING:
    from application.services.crypto_payment_service import CryptoPaymentService


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
        transaction_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a Telegram Stars invoice URL for Mini App.

        Args:
            user_id: Telegram user ID
            product_type: 'package' or 'slots'
            product_id: Package type or slots identifier
            transaction_id: Optional unique transaction ID for tracking

        Returns:
            Invoice URL that can be opened with Telegram.WebApp.openInvoice()
        """
        try:
            # Generate transaction ID if not provided
            if transaction_id is None:
                import uuid

                transaction_id = str(uuid.uuid4())[:8]

            if product_type == "package":
                package_opt = self.get_package_option(product_id)
                if not package_opt:
                    logger.error(f"Package not found: {product_id}")
                    return None

                # Create invoice parameters
                title = f"Paquete {package_opt.name}"
                description = f"{package_opt.data_gb} GB de datos VPN"
                payload = f"data_package_{product_id}_{user_id}_{transaction_id}"
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
                payload = f"key_slots_{slots}_{user_id}_{transaction_id}"
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

        except ValueError as e:
            logger.error(
                f"Validation error creating Stars invoice for user {user_id}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error creating Stars invoice for user {user_id}: {e}",
                exc_info=True,
            )
            return None

    async def create_crypto_order(
        self,
        user_id: int,
        product_type: str,
        product_id: str,
        payment_service: "CryptoPaymentService",
    ) -> Optional[dict]:
        """
        Create a crypto payment order.

        Args:
            user_id: Telegram user ID
            product_type: 'package' or 'slots'
            product_id: Package type or slots identifier
            payment_service: CryptoPaymentService instance with session context

        Returns:
            Order details including wallet address and QR code.
        """
        try:
            from application.services.wallet_management_service import (
                WalletManagementService,
            )
            from utils.qr_generator import QrGenerator

            logger.info(
                f"Starting crypto order creation for user {user_id}: {product_type}={product_id}"
            )

            # Get wallet service (doesn't require immediate persistence)
            from application.services.common.container import get_service

            wallet_service = get_service(WalletManagementService)

            # Assign wallet to user
            logger.debug(f"Assigning wallet for user {user_id}")
            wallet = await wallet_service.assign_wallet(
                user_id, label=f"miniapp-user-{user_id}"
            )

            if not wallet:
                logger.error(
                    f"Could not assign wallet to user {user_id} - wallet service returned None"
                )
                return None

            # Determine product details and amount
            if product_type == "package":
                package_opt = self.get_package_option(product_id)
                if not package_opt:
                    logger.error(f"Package not found: {product_id}")
                    return None

                # Tasa: 1 USDT = 120 Stars
                amount_usdt = package_opt.stars / 120

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
            QrGenerator.generate_payment_qr(
                wallet_address=wallet.address, amount=amount_usdt, filename=qr_filename
            )

            # Build QR code URL (relative to Mini App)
            qr_url = f"/miniapp/static/qr/{qr_filename}.png"

            logger.info(
                f"Created crypto order {order.id} for user {user_id}: "
                f"{product_type}={product_id}, amount={amount_usdt} USDT"
            )

            return {
                "order_id": str(order.id),
                "wallet_address": wallet.address,
                "amount_usdt": amount_usdt,
                "qr_code_url": qr_url,
                "expires_at": (
                    order.expires_at.isoformat() if order.expires_at else None
                ),
            }

        except TronDealerApiError as e:
            logger.error(
                f"TronDealer API error for user {user_id}: "
                f"{e.status_code} - {e.message}"
            )
            return None
        except ValueError as e:
            logger.error(
                f"Validation error creating crypto order for user {user_id}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error creating crypto order for user {user_id}: {e}",
                exc_info=True,
            )
            return None
