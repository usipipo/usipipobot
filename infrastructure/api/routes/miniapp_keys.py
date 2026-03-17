"""
Rutas de gestión de claves VPN para la Mini App.

Incluye listado, creación y eliminación de claves.

Author: uSipipo Team
Version: 1.0.0
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from application.services.common.container import get_service
from application.services.vpn_service import VpnService
from config import settings
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.key_repository import PostgresKeyRepository
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.routes_common import MiniAppContext, get_current_user
from utils.logger import logger

router = APIRouter(tags=["Mini App Web - Keys"])

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "miniapp" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
