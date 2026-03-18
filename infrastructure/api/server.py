import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from infrastructure.api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from infrastructure.api.routes import (
    miniapp_admin_router,
    miniapp_keys_router,
    miniapp_payments_router,
    miniapp_public_router,
    miniapp_subscriptions_router,
    miniapp_user_router,
)
from infrastructure.api.webhooks import tron_dealer_router
from infrastructure.api.webhooks.tron_dealer import set_services
from infrastructure.persistence.database import close_database, get_session_context, init_database
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Initializing API server...")

    from telegram import Bot

    from application.services.crypto_payment_service import CryptoPaymentService
    from application.services.webhook_security_service import WebhookSecurityService
    from infrastructure.persistence.postgresql.crypto_order_repository import (
        PostgresCryptoOrderRepository,
    )
    from infrastructure.persistence.postgresql.crypto_transaction_repository import (
        PostgresCryptoTransactionRepository,
        PostgresWebhookTokenRepository,
    )
    from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
    from miniapp.services.miniapp_notification_service import init_notification_service

    # Initialize Telegram Bot for Mini App notifications
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    init_notification_service(bot)
    logger.info("✅ MiniApp Notification Service initialized with Telegram Bot")

    async with get_session_context() as session:
        token_repo = PostgresWebhookTokenRepository(session)
        crypto_repo = PostgresCryptoTransactionRepository(session)
        user_repo = PostgresUserRepository(session)
        crypto_order_repo = PostgresCryptoOrderRepository(session)

        security_service = WebhookSecurityService(
            webhook_secret=settings.TRON_DEALER_WEBHOOK_SECRET, token_repo=token_repo
        )

        payment_service = CryptoPaymentService(
            crypto_repo=crypto_repo,
            user_repo=user_repo,
            crypto_order_repo=crypto_order_repo,
        )

        set_services(security_service, payment_service)

    logger.info("✅ API server started")

    yield

    logger.info("🔌 Shutting down API server...")
    await bot.close()
    logger.info("✅ API server stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="uSipipo VPN API",
        description="API for uSipipo VPN webhook processing",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.API_RATE_LIMIT)

    # Register webhooks
    app.include_router(tron_dealer_router, prefix="/api/v1/webhooks")

    # ========================================================================
    # MINI APP ROUTES - TWO PARALLEL ROUTING SYSTEMS
    # ========================================================================
    #
    # We maintain TWO parallel route systems for different use cases:
    #
    # 1. API Routes with versioning prefix: /api/v1/miniapp/...
    #    - Used for: Programmatic API calls, external clients, SDKs
    #    - Authentication: Via X-Telegram-Init-Data header or query param
    #    - Example: /api/v1/miniapp/api/user, /api/v1/miniapp/transactions
    #    - Benefit: Clear API versioning, easy to evolve to v2 later
    #    - Backward compatibility: Existing integrations continue working
    #
    # 2. Direct Web Routes: /miniapp/...
    #    - Used for: Direct browser navigation, Telegram WebApp in-browser
    #    - Authentication: Via query params (tgWebAppData) or headers
    #    - Example: /miniapp/dashboard, /miniapp/purchase, /miniapp/api/user
    #    - Benefit: Clean URLs for web navigation, no version prefix needed
    #    - Required for: Telegram WebApp navigation flow
    #
    # BOTH systems point to the same handler functions, ensuring consistent
    # behavior regardless of which route is used.
    # ========================================================================

    # Register Mini App routes with /api/v1/miniapp prefix
    # These are API routes that require authentication via initData
    # Used for: External API clients, programmatic access, backward compatibility
    app.include_router(miniapp_user_router, prefix="/api/v1/miniapp")
    app.include_router(miniapp_keys_router, prefix="/api/v1/miniapp")
    app.include_router(miniapp_payments_router, prefix="/api/v1/miniapp")
    app.include_router(miniapp_subscriptions_router, prefix="/api/v1/miniapp")
    app.include_router(miniapp_admin_router, prefix="/api/v1/miniapp")
    app.include_router(miniapp_public_router, prefix="/api/v1/miniapp")

    # ========================================================================
    # DIRECT WEB ROUTES (without /api/v1 prefix)
    # ========================================================================
    # These routes are for direct browser navigation in Telegram WebApp.
    # They use the same handlers as the versioned API routes above.
    #
    # USE THESE ROUTES WHEN:
    # - User clicks navigation links in the UI (e.g., bottom nav bar)
    # - Browser needs to load a new page directly
    # - Telegram WebApp needs clean URLs without API version prefix
    #
    # DO NOT USE for:
    # - AJAX/fetch calls from JavaScript (use /miniapp/api/... instead)
    # - External API integrations (use /api/v1/miniapp/... instead)
    # ========================================================================

    # CRITICAL: Register direct web routes for Mini App navigation (without /api/v1/miniapp prefix)
    # These are required for Telegram WebApp in-browser navigation
    from infrastructure.api.routes.miniapp_admin import api_get_logs, logs_page
    from infrastructure.api.routes.miniapp_keys import (
        api_delete_key,
        api_get_keys,
        create_key_form,
        create_key_submit,
        keys_list,
    )
    from infrastructure.api.routes.miniapp_payments import (
        api_check_crypto_payment,
        api_check_stars_payment,
        api_confirm_payment,
        api_create_crypto_order,
        api_create_stars_invoice,
        get_transactions,
        invoice_page,
        payment_method_page,
        purchase_page,
        transactions_page,
    )
    from infrastructure.api.routes.miniapp_public import render_entry_html
    from infrastructure.api.routes.miniapp_user import (
        api_get_user,
        dashboard,
        miniapp_root,
        profile_page,
        settings_page,
    )

    app.add_api_route("/miniapp/", miniapp_root, methods=["GET"], include_in_schema=False)
    app.add_api_route("/miniapp/entry", render_entry_html, methods=["GET"], include_in_schema=False)
    app.add_api_route("/miniapp/dashboard", dashboard, methods=["GET"], include_in_schema=False)
    app.add_api_route("/miniapp/purchase", purchase_page, methods=["GET"], include_in_schema=False)
    app.add_api_route(
        "/miniapp/payment-method", payment_method_page, methods=["GET"], include_in_schema=False
    )
    app.add_api_route("/miniapp/invoice", invoice_page, methods=["GET"], include_in_schema=False)
    app.add_api_route(
        "/miniapp/transactions", transactions_page, methods=["GET"], include_in_schema=False
    )
    app.add_api_route("/miniapp/profile", profile_page, methods=["GET"], include_in_schema=False)
    app.add_api_route("/miniapp/settings", settings_page, methods=["GET"], include_in_schema=False)
    app.add_api_route("/miniapp/keys", keys_list, methods=["GET"], include_in_schema=False)
    app.add_api_route(
        "/miniapp/keys/create", create_key_form, methods=["GET"], include_in_schema=False
    )
    app.add_api_route("/miniapp/logs", logs_page, methods=["GET"], include_in_schema=False)

    # ========================================================================
    # API ROUTES FOR WEB NAVIGATION (under /miniapp/api/...)
    # ========================================================================
    # These routes are for AJAX/fetch calls from JavaScript in the browser.
    # They mirror the /api/v1/miniapp/api/... routes but without version prefix.
    #
    # USE THESE ROUTES WHEN:
    # - Making fetch()/XMLHttpRequest calls from frontend JavaScript
    # - Submitting forms via AJAX
    # - Loading data dynamically without page reload
    #
    # DO NOT USE for:
    # - Direct browser navigation (use /miniapp/... instead)
    # - External API integrations (use /api/v1/miniapp/... instead)
    # ========================================================================

    # CRITICAL: Register API routes under /miniapp prefix for web navigation compatibility
    # These are the same routes as /api/v1/miniapp but accessible without the version prefix
    app.add_api_route(
        "/miniapp/api/user",
        api_get_user,
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/create-stars-invoice",
        api_create_stars_invoice,
        methods=["POST"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/create-crypto-order",
        api_create_crypto_order,
        methods=["POST"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/confirm-payment",
        api_confirm_payment,
        methods=["POST"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/check-stars-payment",
        api_check_stars_payment,
        methods=["POST"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/check-crypto-payment",
        api_check_crypto_payment,
        methods=["POST"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/transactions",
        get_transactions,
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/keys",
        api_get_keys,
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/keys/delete",
        api_delete_key,
        methods=["POST"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/miniapp/api/logs",
        api_get_logs,
        methods=["GET"],
        include_in_schema=False,
    )

    # Mount static files for Mini App with new prefix
    miniapp_static_dir = Path(__file__).parent.parent.parent / "miniapp" / "static"
    if miniapp_static_dir.exists():
        app.mount(
            "/api/v1/miniapp/static",
            StaticFiles(directory=str(miniapp_static_dir)),
            name="miniapp-static",
        )
        # Also mount static files at /miniapp/static for direct web access
        app.mount(
            "/miniapp/static",
            StaticFiles(directory=str(miniapp_static_dir)),
            name="miniapp-static-direct",
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "usipipo-api"}

    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = Path(__file__).parent.parent.parent / "miniapp" / "static" / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/svg+xml")
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    return app


def run_api(host: str = "0.0.0.0", port: int = 8000):
    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)
