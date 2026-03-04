"""
Utilidades y modelos compartidos para los routers de la Mini App.

Contiene el contexto de autenticación, dependencias comunes y modelos Pydantic.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import Optional

from fastapi import Depends, Form, HTTPException, Request
from pydantic import BaseModel, Field

from config import settings
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.services.miniapp_auth import (
    MiniAppAuthService,
    TelegramUser,
    get_miniapp_auth_service,
)
from utils.logger import logger


class PaymentRequest(BaseModel):
    """Request model for payment endpoints."""

    product_type: str = Field(..., description="Type of product: 'package' or 'slots'")
    product_id: str = Field(..., description="Product identifier (e.g., 'basic', 'slots_3')")


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


async def require_admin(ctx: MiniAppContext = Depends(get_current_user)) -> MiniAppContext:
    """Dependencia que requiere que el usuario sea administrador."""
    if ctx.user.id != int(settings.ADMIN_ID):
        logger.warning(f"🚫 User {ctx.user.id} attempted admin action without privileges")
        raise HTTPException(status_code=403, detail="Acceso denegado: solo administradores")
    return ctx
