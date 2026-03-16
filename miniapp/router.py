"""
Router FastAPI para Telegram Mini App Web.

Define los endpoints para servir las páginas de la Mini App
y las APIs para interactuar con el backend.

Este archivo es el punto de entrada que combina todos los
routers específicos por dominio.

Author: uSipipo Team
Version: 1.0.0
"""

from fastapi import APIRouter

# Import routers from domain-specific modules
from miniapp.routes_admin import router as admin_router
from miniapp.routes_common import MiniAppContext, PaymentRequest, get_current_user
from miniapp.routes_keys import router as keys_router
from miniapp.routes_payments import router as payments_router
from miniapp.routes_public import router as public_router
from miniapp.routes_subscriptions import router as subscriptions_router
from miniapp.routes_user import router as user_router

# Main router with prefix
router = APIRouter(prefix="/miniapp", tags=["Mini App"])

# Include all domain routers
# Note: The order matters for route matching
router.include_router(public_router)
router.include_router(user_router)
router.include_router(keys_router)
router.include_router(payments_router)
router.include_router(subscriptions_router)
router.include_router(admin_router)

# Re-export for backwards compatibility and external use
__all__ = [
    "router",
    "get_current_user",
    "MiniAppContext",
    "PaymentRequest",
]
