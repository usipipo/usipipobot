"""
Rutas de pagos para la Mini App.

Incluye compra de paquetes, facturas Stars y pagos con crypto.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from application.services.crypto_payment_service import CryptoPaymentService
from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from config import settings
from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from domain.entities.data_package import DataPackage
from domain.entities.subscription_plan import SubscriptionPlan
from infrastructure.api.routes.miniapp_common import (
    MiniAppContext,
    PaymentRequest,
    get_current_user,
)
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.crypto_order_repository import (
    PostgresCryptoOrderRepository,
)
from infrastructure.persistence.postgresql.crypto_transaction_repository import (
    PostgresCryptoTransactionRepository,
)
from infrastructure.persistence.postgresql.data_package_repository import (
    PostgresDataPackageRepository,
)
from infrastructure.persistence.postgresql.subscription_repository import (
    PostgresSubscriptionRepository,
)
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.services.miniapp_payment_service import MiniAppPaymentService
from utils.logger import logger


class ConfirmPaymentRequest(BaseModel):
    """Request model for confirming a payment."""

    product_type: str = Field(..., description="Type of product: 'package' or 'slots'")
    product_id: str = Field(..., description="Product identifier (e.g., 'basic', 'slots_3')")
    transaction_id: str = Field(..., description="Unique transaction ID from invoice creation")


class TransactionResponse(BaseModel):
    """Response model for a single transaction in history."""

    id: str = Field(..., description="Transaction ID")
    type: str = Field(..., description="Transaction type: 'package', 'crypto', 'subscription'")
    description: str = Field(..., description="Human-readable description")
    amount: int = Field(..., description="Amount in stars (negative for spending)")
    status: str = Field(
        ..., description="Transaction status: 'completed', 'pending', 'failed', 'expired'"
    )
    created_at: str = Field(..., description="Transaction creation timestamp")
    payment_method: str = Field(..., description="Payment method: 'stars' or 'crypto'")
    amount_usdt: float | None = Field(None, description="Amount in USDT for crypto transactions")


class PaginationResponse(BaseModel):
    """Pagination metadata response."""

    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")


class TransactionHistoryResponse(BaseModel):
    """Response model for transaction history with pagination."""

    success: bool = True
    transactions: list[TransactionResponse] = Field(default_factory=list)
    pagination: PaginationResponse


router = APIRouter(tags=["Mini App Web - Payments"])

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "miniapp" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/purchase", response_class=HTMLResponse)
async def purchase_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página para comprar paquetes de datos y slots."""
    logger.info(f"💎 MiniApp purchase page accessed by user {ctx.user.id}")
    # Convert PackageOption objects to dict for template
    packages = [
        {
            "id": opt.package_type.value,
            "name": opt.name,
            "data_gb": opt.data_gb,
            "price_stars": opt.stars,
            "description": f"{opt.data_gb} GB de datos",
            "bonus_percent": opt.bonus_percent,
        }
        for opt in PACKAGE_OPTIONS
    ]

    # Convert SlotOption objects to dict for template
    slots = [
        {
            "id": f"slots_{opt.slots}",
            "name": opt.name,
            "slots": opt.slots,
            "price_stars": opt.stars,
        }
        for opt in SLOT_OPTIONS
    ]

    return templates.TemplateResponse(
        "purchase.html",
        {
            "request": request,
            "user": ctx.user,
            "packages": packages,
            "slots": slots,
            "bot_username": settings.BOT_USERNAME,
        },
    )


# ============================================================================
# TRANSACTIONS
# ============================================================================


@router.get("/transactions", response_model=TransactionHistoryResponse)
async def get_transactions(
    ctx: MiniAppContext = Depends(get_current_user),
    page: int = 1,
    limit: int = 20,
    type: str | None = None,
    status: str | None = None,
):
    """
    API: Get user's complete transaction history with pagination and filters.

    Fetches DataPackage, CryptoOrder, and SubscriptionPlan records,
    combines them into a unified transaction list, sorts by created_at descending,
    applies pagination and optional filters.

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - type: Filter by type: "package", "crypto", "subscription"
    - status: Filter by status: "completed", "pending", "failed", "expired"

    Returns unified transaction history with pagination metadata.
    """
    try:
        # Validate and cap limit
        limit = min(max(limit, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * limit

        logger.info(
            f"Fetching transaction history for user {ctx.user.id}: "
            f"page={page}, limit={limit}, type={type}, status={status}"
        )

        async with get_session_context() as session:
            # Initialize repositories
            package_repo = PostgresDataPackageRepository(session)
            crypto_order_repo = PostgresCryptoOrderRepository(session)
            subscription_repo = PostgresSubscriptionRepository(session)

            # Fetch all transactions from all sources
            packages = await package_repo.get_by_user_paginated(
                ctx.user.id, limit=1000, offset=0, current_user_id=ctx.user.id
            )
            crypto_orders = await crypto_order_repo.get_by_user_paginated(
                ctx.user.id, limit=1000, offset=0, current_user_id=ctx.user.id
            )
            subscriptions = await subscription_repo.get_by_user_paginated(
                ctx.user.id, limit=1000, offset=0, current_user_id=ctx.user.id
            )

            # Convert to transaction responses
            transactions: list[TransactionResponse] = []

            for pkg in packages:
                tx = _entity_to_transaction_response(pkg)
                transactions.append(tx)

            for crypto in crypto_orders:
                tx = _entity_to_transaction_response(crypto)
                transactions.append(tx)

            for sub in subscriptions:
                tx = _entity_to_transaction_response(sub)
                transactions.append(tx)

            # Apply type filter if provided
            if type:
                transactions = [tx for tx in transactions if tx.type == type]

            # Apply status filter if provided
            if status:
                transactions = [tx for tx in transactions if tx.status == status]

            # Sort by created_at descending (newest first)
            transactions.sort(key=lambda x: x.created_at, reverse=True)

            # Get total count before pagination
            total = len(transactions)

            # Apply pagination
            paginated_transactions = transactions[offset : offset + limit]

            # Calculate total pages
            pages = (total + limit - 1) // limit if total > 0 else 0

            logger.info(
                f"Transaction history fetched for user {ctx.user.id}: "
                f"total={total}, page={page}, pages={pages}"
            )

            return TransactionHistoryResponse(
                success=True,
                transactions=paginated_transactions,
                pagination=PaginationResponse(
                    page=page,
                    limit=limit,
                    total=total,
                    pages=pages,
                ),
            )

    except Exception as e:
        logger.error(
            f"Error fetching transaction history for user {ctx.user.id}: {e}", exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )


@router.get("/transactions-page", response_class=HTMLResponse)
async def transactions_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página de historial de transacciones del usuario."""
    logger.info(f"💳 MiniApp transactions page accessed by user {ctx.user.id}")
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "user": ctx.user,
            "bot_username": settings.BOT_USERNAME,
        },
    )


@router.post("/api/create-stars-invoice")
async def api_create_stars_invoice(
    payment_req: PaymentRequest,
    ctx: MiniAppContext = Depends(get_current_user),
):
    """API: Crea una factura de Telegram Stars para pago en Mini App."""
    try:
        logger.info(
            f"Creating Stars invoice for user {ctx.user.id}: "
            f"{payment_req.product_type}={payment_req.product_id}"
        )

        async with get_session_context() as session:
            package_repo = PostgresDataPackageRepository(session)
            user_repo = PostgresUserRepository(session)

            # DEFENSE: Verify user exists before creating invoice
            existing_user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            if not existing_user:
                logger.error(f"User {ctx.user.id} not found in database - cannot create invoice")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Usuario no encontrado. Por favor reinicia la aplicación.",
                    },
                )

            data_package_service = DataPackageService(package_repo, user_repo)
            payment_service = MiniAppPaymentService(data_package_service)

            # Get notification service to send invoice via Telegram Bot
            from miniapp.services.miniapp_notification_service import get_notification_service

            notification_service = get_notification_service()
            if not notification_service:
                logger.error("Notification service not initialized")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "Servicio de notificaciones no disponible. Intenta nuevamente.",
                    },
                )

            # Generate unique transaction ID for this purchase
            import uuid

            transaction_id = str(uuid.uuid4())[:16]

            # Get product details for invoice
            if payment_req.product_type == "package":
                package_opt = payment_service.get_package_option(payment_req.product_id)
                if not package_opt:
                    logger.error(f"Package not found: {payment_req.product_id}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Paquete no válido.",
                        },
                    )

                title = f"Paquete {package_opt.name}"
                description = f"{package_opt.data_gb} GB de datos VPN"
                payload = f"data_package_{payment_req.product_id}_{ctx.user.id}_{transaction_id}"
                amount = package_opt.stars

            elif payment_req.product_type == "slots":
                slots_str = payment_req.product_id.replace("slots_", "")
                slots = int(slots_str)
                slot_opt = payment_service.get_slot_option(slots)

                if not slot_opt:
                    logger.error(f"Slot option not found: {slots}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Opción de slots no válida.",
                        },
                    )

                title = slot_opt.name
                description = f"Añade {slots} claves VPN adicionales"
                payload = f"key_slots_{slots}_{ctx.user.id}_{transaction_id}"
                amount = slot_opt.stars

            elif payment_req.product_type == "subscription":
                # Handle subscription plans
                from application.services.common.container import get_service
                from application.services.subscription_service import SubscriptionService

                subscription_service = get_service(SubscriptionService)
                plan_opt = subscription_service.get_plan_option(payment_req.product_id)

                if not plan_opt:
                    logger.error(f"Subscription plan not found: {payment_req.product_id}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Plan de suscripción no válido.",
                        },
                    )

                title = f"Suscripción {plan_opt.name}"
                description = f"{plan_opt.duration_months} meses de datos ilimitados"
                payload = f"subscription_{payment_req.product_id}_{ctx.user.id}_{transaction_id}"
                amount = plan_opt.stars

            else:
                logger.error(f"Invalid product type: {payment_req.product_type}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Tipo de producto no válido.",
                    },
                )

            # Send invoice via Telegram Bot
            invoice_sent = await notification_service.send_stars_invoice(
                user_id=ctx.user.id,
                title=title,
                description=description,
                payload=payload,
                amount=amount,
            )

            if not invoice_sent:
                logger.warning(
                    f"Failed to create Stars invoice for user {ctx.user.id}: notification service returned None"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": (
                            "No se pudo crear la factura. "
                            "Verifica que el producto seleccionado sea válido."
                        ),
                    },
                )

            logger.info(
                f"Successfully created Stars invoice for user {ctx.user.id}: "
                f"transaction_id={transaction_id}"
            )
            return {
                "success": True,
                "message": "Factura enviada a tu Telegram. Revisa tu chat para pagar.",
                "transaction_id": transaction_id,
            }

    except Exception as e:
        logger.error(f"Error creating stars invoice for user {ctx.user.id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )


@router.post("/api/create-crypto-order")
async def api_create_crypto_order(
    payment_req: PaymentRequest,
    ctx: MiniAppContext = Depends(get_current_user),
):
    """API: Crea una orden de pago con crypto para Mini App."""
    try:
        logger.info(
            f"Creating crypto order for user {ctx.user.id}: "
            f"{payment_req.product_type}={payment_req.product_id}"
        )

        async with get_session_context() as session:
            package_repo = PostgresDataPackageRepository(session)
            user_repo = PostgresUserRepository(session)

            # DEFENSE: Verify user exists before creating order (prevents ForeignKeyViolationError)
            existing_user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            if not existing_user:
                logger.error(
                    f"User {ctx.user.id} not found in database - cannot create crypto order"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Usuario no encontrado. Por favor reinicia la aplicación.",
                    },
                )

            # Create crypto repositories with the same session context
            crypto_repo = PostgresCryptoTransactionRepository(session)
            crypto_order_repo = PostgresCryptoOrderRepository(session)

            # Create CryptoPaymentService with session context (fixes session closed error)
            crypto_payment_service = CryptoPaymentService(
                crypto_repo=crypto_repo,
                user_repo=user_repo,
                crypto_order_repo=crypto_order_repo,
            )

            data_package_service = DataPackageService(package_repo, user_repo)
            miniapp_payment_service = MiniAppPaymentService(data_package_service)

            # Get notification service
            from miniapp.services.miniapp_notification_service import get_notification_service

            notification_service = get_notification_service()

            order_data = await miniapp_payment_service.create_crypto_order(
                user_id=ctx.user.id,
                product_type=payment_req.product_type,
                product_id=payment_req.product_id,
                payment_service=crypto_payment_service,
            )

            if not order_data:
                logger.warning(
                    f"Failed to create crypto order for user {ctx.user.id}: service returned None"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": (
                            "No se pudo crear la orden de pago. "
                            "El servicio de pagos crypto no está disponible "
                            "o el producto seleccionado es inválido."
                        ),
                    },
                )

            # Send notification via Telegram Bot with QR code
            if notification_service:
                product_name = (
                    f"Paquete {payment_req.product_id.upper()}"
                    if payment_req.product_type == "package"
                    else f"+{payment_req.product_id.replace('slots_', '')} Claves"
                )

                await notification_service.send_crypto_payment_notification(
                    user_id=ctx.user.id,
                    order_id=order_data.get("order_id", "N/A"),
                    wallet_address=order_data["wallet_address"],
                    amount_usdt=order_data["amount_usdt"],
                    qr_code_url=order_data["qr_code_url"],
                    product_name=product_name,
                )

            logger.info(
                f"Successfully created crypto order for user {ctx.user.id}: "
                f"order_id={order_data.get('order_id')}"
            )
            return {
                "success": True,
                "message": "Orden crypto creada. Revisa tu Telegram para pagar.",
                **order_data,
            }

    except Exception as e:
        logger.error(f"Error creating crypto order for user {ctx.user.id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )


@router.post("/api/confirm-payment")
async def api_confirm_payment(
    confirm_req: ConfirmPaymentRequest,
    ctx: MiniAppContext = Depends(get_current_user),
):
    """API: Confirma un pago exitoso y entrega el producto."""
    try:
        logger.info(
            f"Confirming payment for user {ctx.user.id}: "
            f"{confirm_req.product_type}={confirm_req.product_id}, "
            f"transaction_id={confirm_req.transaction_id}"
        )

        async with get_session_context() as session:
            package_repo = PostgresDataPackageRepository(session)
            user_repo = PostgresUserRepository(session)

            # Verify user exists
            existing_user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            if not existing_user:
                logger.error(f"User {ctx.user.id} not found in database - cannot confirm payment")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Usuario no encontrado. Por favor reinicia la aplicación.",
                    },
                )

            data_package_service = DataPackageService(package_repo, user_repo)
            payment_service = MiniAppPaymentService(data_package_service)

            # Get notification service
            from miniapp.services.miniapp_notification_service import get_notification_service

            notification_service = get_notification_service()

            if confirm_req.product_type == "package":
                # Validate package exists
                package_opt = payment_service.get_package_option(confirm_req.product_id)
                if not package_opt:
                    logger.warning(
                        f"Invalid package type for user {ctx.user.id}: {confirm_req.product_id}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Paquete no válido.",
                        },
                    )

                # Process package purchase
                package, bonus_breakdown = await data_package_service.purchase_package(
                    user_id=ctx.user.id,
                    package_type=confirm_req.product_id,
                    telegram_payment_id=f"miniapp_{confirm_req.transaction_id}",
                    current_user_id=ctx.user.id,
                )

                logger.info(
                    f"Package purchased successfully for user {ctx.user.id}: "
                    f"{confirm_req.product_id}, package_id={package.id}"
                )

                # Send confirmation notification via Telegram
                if notification_service:
                    product_name = f"Paquete {package_opt.name} ({package_opt.data_gb} GB)"
                    await notification_service.send_payment_confirmation(
                        user_id=ctx.user.id,
                        product_name=product_name,
                        payment_method="Telegram Stars",
                    )

                return {
                    "success": True,
                    "message": "Paquete comprado exitosamente",
                    "package_id": str(package.id),
                    "data_bytes": package.remaining_bytes,
                    "expires_at": (package.expires_at.isoformat() if package.expires_at else None),
                }

            elif confirm_req.product_type == "slots":
                # Parse slots count from product_id
                slots_str = confirm_req.product_id.replace("slots_", "")
                try:
                    slots = int(slots_str)
                except ValueError:
                    logger.warning(
                        f"Invalid slots format for user {ctx.user.id}: {confirm_req.product_id}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Formato de slots inválido.",
                        },
                    )

                # Validate slots option exists
                slot_opt = payment_service.get_slot_option(slots)
                if not slot_opt:
                    logger.warning(f"Invalid slots option for user {ctx.user.id}: {slots}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Opción de slots no válida.",
                        },
                    )

                # Process slots purchase
                result = await data_package_service.purchase_key_slots(
                    user_id=ctx.user.id,
                    slots=slots,
                    telegram_payment_id=f"miniapp_{confirm_req.transaction_id}",
                    current_user_id=ctx.user.id,
                )

                logger.info(
                    f"Slots purchased successfully for user {ctx.user.id}: "
                    f"+{result['slots_added']} slots, new_max={result['new_max_keys']}"
                )

                # Send confirmation notification via Telegram
                if notification_service:
                    product_name = f"+{slots} Claves VPN"
                    await notification_service.send_payment_confirmation(
                        user_id=ctx.user.id,
                        product_name=product_name,
                        payment_method="Telegram Stars",
                    )

                return {
                    "success": True,
                    "message": "Slots comprados exitosamente",
                    "slots_added": result["slots_added"],
                    "new_max_keys": result["new_max_keys"],
                }

            elif confirm_req.product_type == "subscription":
                # Handle subscription activation
                from application.services.common.container import get_service
                from application.services.subscription_service import SubscriptionService

                subscription_service = get_service(SubscriptionService)

                # Validate subscription plan
                plan_opt = subscription_service.get_plan_option(confirm_req.product_id)
                if not plan_opt:
                    logger.warning(
                        f"Invalid subscription plan for user {ctx.user.id}: {confirm_req.product_id}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Plan de suscripción no válido.",
                        },
                    )

                # Check if user already has active subscription
                is_premium = await subscription_service.is_premium_user(ctx.user.id, ctx.user.id)
                if is_premium:
                    logger.warning(f"User {ctx.user.id} already has active subscription")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Ya tienes una suscripción activa.",
                        },
                    )

                # Activate subscription
                subscription = await subscription_service.activate_subscription(
                    user_id=ctx.user.id,
                    plan_type=confirm_req.product_id,
                    stars_paid=plan_opt.stars,
                    payment_id=f"miniapp_{confirm_req.transaction_id}",
                    current_user_id=ctx.user.id,
                )

                logger.info(
                    f"Subscription activated successfully for user {ctx.user.id}: "
                    f"{confirm_req.product_id}, subscription_id={subscription.id}"
                )

                # Send confirmation notification via Telegram
                if notification_service:
                    product_name = f"Suscripción {plan_opt.name} ({plan_opt.duration_months} meses)"
                    await notification_service.send_payment_confirmation(
                        user_id=ctx.user.id,
                        product_name=product_name,
                        payment_method="Telegram Stars",
                    )

                return {
                    "success": True,
                    "message": "Suscripción activada exitosamente",
                    "subscription_id": str(subscription.id),
                    "plan_type": subscription.plan_type.value,
                    "expires_at": (
                        subscription.expires_at.isoformat() if subscription.expires_at else None
                    ),
                    "days_remaining": subscription.days_remaining,
                }

            else:
                logger.warning(
                    f"Invalid product type for user {ctx.user.id}: {confirm_req.product_type}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Tipo de producto no válido.",
                    },
                )

    except Exception as e:
        logger.error(f"Error confirming payment for user {ctx.user.id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )


@router.get("/api/payment-status/{transaction_id}")
async def get_payment_status(
    transaction_id: str,
    ctx: MiniAppContext = Depends(get_current_user),
):
    """
    API: Check payment completion status for Mini App frontend polling.

    Checks DataPackage, CryptoOrder, and Subscription tables for matching transaction_id.
    Returns status: "completed", "pending", or "not_found".

    Response formats:
    - Completed package: {success, status, type, product_id, data_gb, activated_at}
    - Completed crypto: {success, status, type, amount_usdt, confirmed_at}
    - Completed subscription: {success, status, type, plan_type, activated_at}
    - Pending crypto: {success, status, type, amount_usdt, confirmed_at: None}
    - Not found: {success, status: "pending", message}
    """
    try:
        logger.info(f"Checking payment status for transaction: {transaction_id}")

        async with get_session_context() as session:
            # Initialize repositories
            package_repo = PostgresDataPackageRepository(session)
            crypto_order_repo = PostgresCryptoOrderRepository(session)
            subscription_repo = PostgresSubscriptionRepository(session)

            # 1. Check DataPackage table for matching telegram_payment_id
            package = await package_repo.get_by_telegram_payment_id(
                f"miniapp_{transaction_id}", ctx.user.id
            )

            if package:
                # Calculate data_gb from data_limit_bytes
                data_gb = package.data_limit_bytes // (1024**3)

                return {
                    "success": True,
                    "status": "completed",
                    "type": "package",
                    "product_id": package.package_type.value,
                    "data_gb": data_gb,
                    "activated_at": (
                        package.purchased_at.isoformat() if package.purchased_at else None
                    ),
                }

            # 2. Check CryptoOrder table for matching tron_dealer_order_id
            crypto_order = await crypto_order_repo.get_by_tron_dealer_order_id(
                transaction_id, ctx.user.id
            )

            if crypto_order:
                is_completed = crypto_order.status == CryptoOrderStatus.COMPLETED

                return {
                    "success": True,
                    "status": "completed" if is_completed else "pending",
                    "type": "crypto",
                    "amount_usdt": crypto_order.amount_usdt,
                    "confirmed_at": (
                        crypto_order.confirmed_at.isoformat() if crypto_order.confirmed_at else None
                    ),
                }

            # 3. Check Subscription table for matching payment_id
            subscription = await subscription_repo.get_by_payment_id(
                f"miniapp_{transaction_id}", ctx.user.id
            )

            if subscription:
                return {
                    "success": True,
                    "status": "completed",
                    "type": "subscription",
                    "plan_type": subscription.plan_type.value,
                    "activated_at": (
                        subscription.starts_at.isoformat() if subscription.starts_at else None
                    ),
                }

            # 4. Transaction not found - payment not yet detected
            logger.info(f"Payment not detected for transaction: {transaction_id}")
            return {
                "success": True,
                "status": "pending",
                "message": "Payment not yet detected. Please complete payment in Telegram.",
            }

    except Exception as e:
        logger.error(f"Error checking payment status for {transaction_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )


def _entity_to_transaction_response(
    entity: DataPackage | CryptoOrder | SubscriptionPlan,
) -> TransactionResponse:
    """Convert domain entity to transaction response."""
    if isinstance(entity, DataPackage):
        # Calculate data GB from bytes
        data_gb = entity.data_limit_bytes // (1024**3)
        description = f"Paquete {data_gb} GB"

        # Determine status
        if not entity.is_active:
            status = "failed"
        elif entity.is_expired:
            status = "expired"
        else:
            status = "completed"

        return TransactionResponse(
            id=str(entity.id),
            type="package",
            description=description,
            amount=-entity.stars_paid,  # Negative for money spent
            status=status,
            created_at=(
                entity.purchased_at.isoformat()
                if entity.purchased_at
                else datetime.now(timezone.utc).isoformat()
            ),
            payment_method="stars",
        )

    elif isinstance(entity, CryptoOrder):
        # Map crypto order status
        status = entity.status.value

        return TransactionResponse(
            id=str(entity.id),
            type="crypto",
            description=f"Pago crypto - {entity.package_type}",
            amount=0,  # Crypto payments don't use stars
            status=status,
            created_at=(
                entity.created_at.isoformat()
                if entity.created_at
                else datetime.now(timezone.utc).isoformat()
            ),
            payment_method="crypto",
            amount_usdt=entity.amount_usdt,
        )

    elif isinstance(entity, SubscriptionPlan):
        # Calculate duration in months
        duration_months = entity.duration_days // 30

        # Determine status
        if not entity.is_active:
            status = "failed"
        elif entity.is_expired:
            status = "expired"
        else:
            status = "completed"

        return TransactionResponse(
            id=str(entity.id),
            type="subscription",
            description=f"Suscripción {duration_months} mes(es)",
            amount=-entity.stars_paid,
            status=status,
            created_at=(
                entity.created_at.isoformat()
                if entity.created_at
                else datetime.now(timezone.utc).isoformat()
            ),
            payment_method="stars",
        )

    raise ValueError(f"Unknown entity type: {type(entity)}")
