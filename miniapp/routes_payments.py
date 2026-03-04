"""
Rutas de pagos para la Mini App.

Incluye compra de paquetes, facturas Stars y pagos con crypto.

Author: uSipipo Team
Version: 1.0.0
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from config import settings
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.data_package_repository import (
    PostgresDataPackageRepository,
)
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.routes_common import MiniAppContext, PaymentRequest, get_current_user
from miniapp.services.miniapp_payment_service import MiniAppPaymentService
from utils.logger import logger

router = APIRouter(tags=["Mini App - Payments"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
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

            invoice_url = payment_service.create_stars_invoice_url(
                user_id=ctx.user.id,
                product_type=payment_req.product_type,
                product_id=payment_req.product_id,
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

            logger.info(f"Successfully created Stars invoice for user {ctx.user.id}")
            return {
                "success": True,
                "invoice_url": invoice_url,
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

            data_package_service = DataPackageService(package_repo, user_repo)
            payment_service = MiniAppPaymentService(data_package_service)

            order_data = await payment_service.create_crypto_order(
                user_id=ctx.user.id,
                product_type=payment_req.product_type,
                product_id=payment_req.product_id,
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
        logger.error(f"Error creating crypto order for user {ctx.user.id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor. Por favor intenta nuevamente.",
            },
        )
