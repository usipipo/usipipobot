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
from domain.entities.user import User, UserRole
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from miniapp.services.miniapp_auth import MiniAppAuthService, TelegramUser, get_miniapp_auth_service
from utils.logger import logger


class PaymentRequest(BaseModel):
    """Request model for payment endpoints."""

    product_type: str = Field(..., description="Type of product: 'package' or 'slots'")
    product_id: str = Field(..., description="Product identifier (e.g., 'basic', 'slots_3')")


class MiniAppContext:
    """Contexto de autenticación para Mini App."""

    def __init__(
        self,
        user: TelegramUser,
        db_user: Optional[User] = None,
        query_id: Optional[str] = None,
    ):
        self.user = user
        self.db_user = db_user
        self.query_id = query_id

    @property
    def is_admin(self) -> bool:
        """
        Verifica si el usuario es administrador.

        Checks:
        1. User's role in database (if db_user is available)
        2. Fallback to ADMIN_ID from settings
        """
        # Check role from database first
        if self.db_user and self.db_user.role == UserRole.ADMIN:
            return True

        # Fallback to ADMIN_ID check
        return self.user.id == int(settings.ADMIN_ID)


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

    # CRITICAL: Verify user is registered in bot first and load DB user
    # MiniApp only works for users who have already used /start in the bot
    try:
        async with get_session_context() as session:
            user_repo = PostgresUserRepository(session)
            db_user = await user_repo.get_by_id(result.user.id, result.user.id)

            if not db_user:
                logger.warning(
                    f"User {result.user.id} tried to access MiniApp but is not registered. "
                    f"They must use /start in the bot first."
                )
                raise HTTPException(status_code=403, detail="USER_NOT_REGISTERED")

            # Pass db_user to context so is_admin can check role from database
            return MiniAppContext(user=result.user, db_user=db_user, query_id=result.query_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error verificando usuario. Por favor intenta nuevamente.",
        )


async def require_admin(
    ctx: MiniAppContext = Depends(get_current_user),
) -> MiniAppContext:
    """Dependencia que requiere que el usuario sea administrador."""
    if not ctx.is_admin:
        logger.warning(f"🚫 User {ctx.user.id} attempted admin action without privileges")
        raise HTTPException(status_code=403, detail="Acceso denegado: solo administradores")
    return ctx
