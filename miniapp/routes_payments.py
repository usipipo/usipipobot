"""
Rutas de pagos para la Mini App.

Incluye compra de paquetes, facturas Stars y pagos con crypto.

Author: uSipipo Team
Version: 1.0.0
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from application.services.crypto_payment_service import CryptoPaymentService
from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from config import settings
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
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.routes_common import MiniAppContext, PaymentRequest, get_current_user
from miniapp.services.miniapp_payment_service import MiniAppPaymentService
from pydantic import BaseModel, Field
from utils.logger import logger


class ConfirmPaymentRequest(BaseModel):
    """Request model for confirming a payment."""

    product_type: str = Field(..., description="Type of product: 'package' or 'slots'")
    product_id: str = Field(
        ..., description="Product identifier (e.g., 'basic', 'slots_3')"
    )
    transaction_id: str = Field(
        ..., description="Unique transaction ID from invoice creation"
    )


router = APIRouter(tags=["Mini App - Payments"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/purchase", response_class=HTMLResponse)
async def purchase_page(
    request: Request, ctx: MiniAppContext = Depends(get_current_user)
):
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
                logger.error(
                    f"User {ctx.user.id} not found in database - cannot create invoice"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Usuario no encontrado. Por favor reinicia la aplicación.",
                    },
                )

            data_package_service = DataPackageService(package_repo, user_repo)
            payment_service = MiniAppPaymentService(data_package_service)

            # Generate unique transaction ID for this purchase
            import uuid

            transaction_id = str(uuid.uuid4())[:16]

            invoice_url = payment_service.create_stars_invoice_url(
                user_id=ctx.user.id,
                product_type=payment_req.product_type,
                product_id=payment_req.product_id,
                transaction_id=transaction_id,
            )

            if not invoice_url:
                logger.warning(
                    f"Failed to create Stars invoice for user {ctx.user.id}: service returned None"
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
                "invoice_url": invoice_url,
                "transaction_id": transaction_id,
            }

    except Exception as e:
        logger.error(
            f"Error creating stars invoice for user {ctx.user.id}: {e}", exc_info=True
        )
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

            logger.info(
                f"Successfully created crypto order for user {ctx.user.id}: "
                f"order_id={order_data.get('order_id')}"
            )
            return {
                "success": True,
                **order_data,
            }

    except Exception as e:
        logger.error(
            f"Error creating crypto order for user {ctx.user.id}: {e}", exc_info=True
        )
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
                logger.error(
                    f"User {ctx.user.id} not found in database - cannot confirm payment"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Usuario no encontrado. Por favor reinicia la aplicación.",
                    },
                )

            data_package_service = DataPackageService(package_repo, user_repo)
            payment_service = MiniAppPaymentService(data_package_service)

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

                return {
                    "success": True,
                    "message": "Paquete comprado exitosamente",
                    "package_id": str(package.id),
                    "data_bytes": package.remaining_bytes,
                    "expires_at": (
                        package.expires_at.isoformat() if package.expires_at else None
                    ),
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
                    logger.warning(
                        f"Invalid slots option for user {ctx.user.id}: {slots}"
                    )
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

                return {
                    "success": True,
                    "message": "Slots comprados exitosamente",
                    "slots_added": result["slots_added"],
                    "new_max_keys": result["new_max_keys"],
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
        logger.error(
            f"Error confirming payment for user {ctx.user.id}: {e}", exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )
