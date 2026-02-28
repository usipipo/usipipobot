"""
Router FastAPI para Telegram Mini App Web.

Define los endpoints para servir las páginas de la Mini App
y las APIs para interactuar con el backend.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from application.services.common.container import get_service
from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from application.services.vpn_service import VpnService
from config import settings
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.data_package_repository import (
    PostgresDataPackageRepository,
)
from infrastructure.persistence.postgresql.key_repository import PostgresKeyRepository
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.services.miniapp_auth import (
    MiniAppAuthService,
    TelegramUser,
    get_miniapp_auth_service,
)
from miniapp.services.miniapp_payment_service import MiniAppPaymentService
from utils.logger import logger

router = APIRouter(prefix="/miniapp", tags=["Mini App"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class PaymentRequest(BaseModel):
    """Request model for payment endpoints."""

    product_type: str = Field(..., description="Type of product: 'package' or 'slots'")
    product_id: str = Field(..., description="Product identifier (e.g., 'basic', 'slots_3')")


@router.get("/entry", response_class=HTMLResponse)
async def miniapp_entry(request: Request):
    """
    Página de entrada pública para la Mini App.

    Esta página se carga sin autenticación para obtener initData
    del SDK de Telegram y redirigir al dashboard autenticado.
    """
    return templates.TemplateResponse(
        "entry.html",
        {
            "request": request,
            "bot_username": settings.BOT_USERNAME,
        },
    )


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """
    Página pública de Política de Privacidad.

    Requerido por Telegram para bots con Mini Apps.
    Esta página es accesible sin autenticación.
    """
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
        },
    )


class MiniAppContext:
    """Contexto de autenticación para Mini App."""

    def __init__(self, user: TelegramUser, query_id: Optional[str] = None):
        self.user = user
        self.query_id = query_id


async def get_current_user(
    request: Request,
    auth_service: MiniAppAuthService = Depends(get_miniapp_auth_service),
) -> MiniAppContext:
    """
    Dependencia para obtener el usuario actual desde initData.

    Soporta tanto query params (GET) como form data (POST).
    Asegura que el usuario exista en la base de datos local.
    """
    init_data = request.query_params.get("tgWebAppData")

    if not init_data:
        init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        form_data = await request.form()
        form_value = form_data.get("tgWebAppData")
        if isinstance(form_value, str):
            init_data = form_value

    if not init_data:
        raise HTTPException(status_code=401, detail="No autorizado: initData requerido")

    result = auth_service.validate_init_data(init_data)

    if not result.success or not result.user:
        raise HTTPException(status_code=401, detail=f"No autorizado: {result.error}")

    # CRITICAL: Verify user is registered in bot first
    # MiniApp only works for users who have already used /start in the bot
    try:
        async with get_session_context() as session:
            user_repo = PostgresUserRepository(session)
            existing_user = await user_repo.get_by_id(result.user.id, result.user.id)

            if not existing_user:
                logger.warning(
                    f"User {result.user.id} tried to access MiniApp but is not registered. "
                    f"They must use /start in the bot first."
                )
                raise HTTPException(status_code=403, detail="USER_NOT_REGISTERED")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error verificando usuario. Por favor intenta nuevamente.",
        )

    return MiniAppContext(user=result.user, query_id=result.query_id)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """
    Dashboard principal de la Mini App.

    Muestra métricas de consumo, claves activas y estado del usuario.
    """
    logger.info(f"📊 MiniApp dashboard accessed by user {ctx.user.id}")
    try:
        async with get_session_context() as session:
            user_repo = PostgresUserRepository(session)
            key_repo = PostgresKeyRepository(session)

            user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            if not user:
                user = await user_repo.get_by_id(settings.ADMIN_ID, ctx.user.id)

            keys = await key_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            total_used_bytes = sum(k.used_bytes for k in keys if k.is_active)
            total_limit_bytes = sum(k.data_limit_bytes for k in keys if k.is_active)
            active_keys = [k for k in keys if k.is_active]

            remaining_bytes = max(0, total_limit_bytes - total_used_bytes)

            usage_percent = (
                (total_used_bytes / total_limit_bytes * 100) if total_limit_bytes > 0 else 0
            )

            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "user": ctx.user,
                    "db_user": user,
                    "keys": active_keys,
                    "total_used_gb": round(total_used_bytes / (1024**3), 2),
                    "total_limit_gb": round(total_limit_bytes / (1024**3), 2),
                    "remaining_gb": round(remaining_bytes / (1024**3), 2),
                    "usage_percent": round(usage_percent, 1),
                    "keys_count": len(active_keys),
                    "max_keys": user.max_keys if user else 2,
                    "bot_username": settings.BOT_USERNAME,
                },
            )
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/keys", response_class=HTMLResponse)
async def keys_list(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página de gestión de claves VPN."""
    logger.info(f"🔑 MiniApp keys list accessed by user {ctx.user.id}")
    try:
        async with get_session_context() as session:
            key_repo = PostgresKeyRepository(session)
            user_repo = PostgresUserRepository(session)

            keys = await key_repo.get_by_user_id(ctx.user.id, ctx.user.id)
            user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)

            can_create = user.can_create_more_keys() if user else True

            return templates.TemplateResponse(
                "keys.html",
                {
                    "request": request,
                    "user": ctx.user,
                    "keys": keys,
                    "can_create": can_create,
                    "max_keys": user.max_keys if user else 2,
                    "bot_username": settings.BOT_USERNAME,
                },
            )
    except Exception as e:
        logger.error(f"Error en keys list: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/keys/create", response_class=HTMLResponse)
async def create_key_form(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Formulario para crear nueva clave VPN."""
    logger.info(f"➕ MiniApp create key form accessed by user {ctx.user.id}")
    try:
        async with get_session_context() as session:
            user_repo = PostgresUserRepository(session)
            user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            can_create = user.can_create_more_keys() if user else True

            return templates.TemplateResponse(
                "create_key.html",
                {
                    "request": request,
                    "user": ctx.user,
                    "can_create": can_create,
                    "max_keys": user.max_keys if user else 2,
                    "wireguard_enabled": settings.wireguard_enabled,
                    "outline_enabled": settings.outline_enabled,
                    "bot_username": settings.BOT_USERNAME,
                },
            )
    except Exception as e:
        logger.error(f"Error en create key form: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/keys/create")
async def create_key_submit(
    request: Request,
    key_type: str = Form(...),
    key_name: str = Form(...),
    ctx: MiniAppContext = Depends(get_current_user),
):
    """Procesa la creación de una nueva clave VPN."""
    try:
        vpn_service = get_service(VpnService)

        new_key = await vpn_service.create_key(
            telegram_id=ctx.user.id,
            key_type=key_type,
            key_name=key_name,
            current_user_id=ctx.user.id,
        )

        logger.info(f"🔑 Nueva clave creada via Mini App: {new_key.id} para {ctx.user.id}")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "key_id": new_key.id,
                "key_name": new_key.name,
                "key_type": new_key.key_type.value,
            },
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)},
        )
    except Exception as e:
        logger.error(f"Error creando clave: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Error interno del servidor"},
        )


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


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página de perfil del usuario."""
    logger.info(f"👤 MiniApp profile page accessed by user {ctx.user.id}")
    try:
        async with get_session_context() as session:
            user_repo = PostgresUserRepository(session)
            key_repo = PostgresKeyRepository(session)

            user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            keys = await key_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            total_used_bytes = sum(k.used_bytes for k in keys if k.is_active)
            total_limit_bytes = sum(k.data_limit_bytes for k in keys if k.is_active)
            remaining_bytes = max(0, total_limit_bytes - total_used_bytes)

            stats = {
                "keys_count": len([k for k in keys if k.is_active]),
                "total_used_gb": round(total_used_bytes / (1024**3), 2),
                "total_limit_gb": round(total_limit_bytes / (1024**3), 2),
                "remaining_gb": round(remaining_bytes / (1024**3), 2),
                "active_packages": 0,
            }

            profile_info = None
            transactions = []

            if user:
                profile_info = {
                    "created_at": user.created_at,
                    "status": (
                        user.status.value if hasattr(user.status, "value") else str(user.status)
                    ),
                    "max_keys": user.max_keys,
                    "referral_code": getattr(user, "referral_code", None),
                    "total_referrals": getattr(user, "total_referrals", 0),
                }

                try:
                    from infrastructure.persistence.postgresql.transaction_repository import (
                        PostgresTransactionRepository,
                    )

                    tx_repo = PostgresTransactionRepository(session)
                    transactions = await tx_repo.get_user_transactions(ctx.user.id, limit=10)
                except Exception as tx_error:
                    logger.warning(f"Could not fetch transactions: {tx_error}")

            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": ctx.user,
                    "stats": stats,
                    "profile_info": profile_info,
                    "transactions": transactions,
                    "bot_username": settings.BOT_USERNAME,
                },
            )
    except Exception as e:
        logger.error(f"Error en profile page: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página de ajustes del usuario."""
    is_admin = ctx.user.id == int(settings.ADMIN_ID)
    logger.info(f"⚙️ User {ctx.user.id} accessed settings (admin={is_admin})")
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": ctx.user,
            "bot_username": settings.BOT_USERNAME,
            "is_admin": is_admin,
        },
    )


@router.get("/api/user")
async def api_get_user(ctx: MiniAppContext = Depends(get_current_user)):
    """API: Obtiene datos del usuario actual."""
    logger.debug(f"📡 API /user called by user {ctx.user.id}")
    try:
        async with get_session_context() as session:
            user_repo = PostgresUserRepository(session)
            key_repo = PostgresKeyRepository(session)

            user = await user_repo.get_by_id(ctx.user.id, ctx.user.id)
            keys = await key_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            total_used = sum(k.used_bytes for k in keys if k.is_active)
            total_limit = sum(k.data_limit_bytes for k in keys if k.is_active)

            return {
                "success": True,
                "user": {
                    "id": ctx.user.id,
                    "username": ctx.user.username,
                    "first_name": ctx.user.first_name,
                    "is_premium": ctx.user.is_premium,
                },
                "stats": {
                    "keys_count": len([k for k in keys if k.is_active]),
                    "max_keys": user.max_keys if user else 2,
                    "total_used_gb": round(total_used / (1024**3), 2),
                    "total_limit_gb": round(total_limit / (1024**3), 2),
                },
            }
    except Exception as e:
        logger.error(f"Error en API user: {e}")
        return {"success": False, "error": "Error interno"}


@router.get("/api/keys")
async def api_get_keys(ctx: MiniAppContext = Depends(get_current_user)):
    """API: Obtiene lista de claves del usuario."""
    logger.debug(f"📡 API /keys called by user {ctx.user.id}")
    try:
        async with get_session_context() as session:
            key_repo = PostgresKeyRepository(session)

            keys = await key_repo.get_by_user_id(ctx.user.id, ctx.user.id)

            return {
                "success": True,
                "keys": [
                    {
                        "id": k.id,
                        "name": k.name,
                        "type": k.key_type.value,
                        "is_active": k.is_active,
                        "used_gb": round(k.used_gb, 2),
                        "limit_gb": round(k.data_limit_gb, 2),
                        "remaining_gb": round(k.remaining_bytes / (1024**3), 2),
                        "created_at": (k.created_at.isoformat() if k.created_at else None),
                        "last_seen": (k.last_seen_at.isoformat() if k.last_seen_at else None),
                    }
                    for k in keys
                ],
            }
    except Exception as e:
        logger.error(f"Error en API keys: {e}")
        return {"success": False, "error": "Error interno"}


@router.post("/api/keys/delete")
async def api_delete_key(
    request: Request,
    ctx: MiniAppContext = Depends(get_current_user),
):
    """API: Elimina una clave VPN (SOLO ADMIN)."""
    try:
        # Only admins can delete keys
        if ctx.user.id != int(settings.ADMIN_ID):
            logger.warning(f"User {ctx.user.id} attempted to delete key without admin privileges")
            raise HTTPException(
                status_code=403, detail="Solo administradores pueden eliminar claves"
            )

        data = await request.json()
        key_id = data.get("key_id")

        if not key_id:
            return {"success": False, "error": "key_id requerido"}

        vpn_service = get_service(VpnService)
        success = await vpn_service.delete_key(key_id, ctx.user.id)

        return {"success": success}
    except HTTPException:
        raise
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error eliminando clave: {e}")
        return {"success": False, "error": "Error interno"}


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


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página de logs del sistema (solo administrador)."""
    if ctx.user.id != int(settings.ADMIN_ID):
        logger.warning(f"🚫 User {ctx.user.id} tried to access logs page without admin privileges")
        raise HTTPException(status_code=403, detail="Acceso denegado: solo administradores")

    logger.info(f"🖥️ Admin {ctx.user.id} accessed logs page")
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "user": ctx.user,
        },
    )


@router.get("/api/logs")
async def api_get_logs(
    lines: int = 100,
    ctx: MiniAppContext = Depends(get_current_user)
):
    """API: Obtiene los últimos logs del sistema (solo administrador)."""
    if ctx.user.id != int(settings.ADMIN_ID):
        logger.warning(f"🚫 User {ctx.user.id} tried to access logs API without admin privileges")
        raise HTTPException(status_code=403, detail="Acceso denegado: solo administradores")

    try:
        from utils.logger import logger as app_logger

        log_lines = app_logger.get_last_logs(lines=lines)

        # Parse log lines into structured format
        parsed_logs = []
        for line in log_lines.strip().split('\n'):
            if not line.strip():
                continue

            # Try to parse log format: "YYYY-MM-DD HH:mm:ss | LEVEL | message"
            parts = line.split(' | ', 2)
            if len(parts) >= 3:
                timestamp = parts[0].strip()
                level = parts[1].strip()
                message = parts[2].strip()
            elif len(parts) == 2:
                timestamp = parts[0].strip()
                level = "INFO"
                message = parts[1].strip()
            else:
                timestamp = datetime.now().isoformat()
                level = "INFO"
                message = line

            parsed_logs.append({
                "timestamp": timestamp,
                "level": level,
                "message": message,
            })

        logger.debug(f"📋 Admin {ctx.user.id} fetched {len(parsed_logs)} log lines")
        return {
            "logs": parsed_logs,
            "total": len(parsed_logs),
        }

    except Exception as e:
        logger.error(f"Error fetching logs for admin {ctx.user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al obtener logs")
