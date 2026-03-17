"""
Routes package for uSipipo API.

This package contains all API route handlers organized by domain.
"""

from infrastructure.api.routes.miniapp_admin import router as miniapp_admin_router
from infrastructure.api.routes.miniapp_keys import router as miniapp_keys_router
from infrastructure.api.routes.miniapp_payments import router as miniapp_payments_router
from infrastructure.api.routes.miniapp_public import router as miniapp_public_router
from infrastructure.api.routes.miniapp_subscriptions import router as miniapp_subscriptions_router
from infrastructure.api.routes.miniapp_user import router as miniapp_user_router

__all__ = [
    "miniapp_user_router",
    "miniapp_keys_router",
    "miniapp_payments_router",
    "miniapp_subscriptions_router",
    "miniapp_admin_router",
    "miniapp_public_router",
]
