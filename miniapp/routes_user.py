"""
Rutas de usuario para la Mini App.

Incluye dashboard, perfil, ajustes y API de usuario.

Author: uSipipo Team
Version: 1.0.0
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.key_repository import PostgresKeyRepository
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.routes_common import MiniAppContext, get_current_user
from utils.logger import logger

router = APIRouter(tags=["Mini App - User"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
