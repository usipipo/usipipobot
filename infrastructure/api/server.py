import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import settings
from infrastructure.api.middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from infrastructure.api.webhooks import tron_dealer_router
from infrastructure.api.webhooks.tron_dealer import set_services
from infrastructure.persistence.database import get_session_context, init_database, close_database
from miniapp import router as miniapp_router
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Initializing API server...")
    
    from application.services.webhook_security_service import WebhookSecurityService
    from application.services.crypto_payment_service import CryptoPaymentService
    from infrastructure.persistence.postgresql.crypto_transaction_repository import (
        PostgresCryptoTransactionRepository,
        PostgresWebhookTokenRepository
    )
    
    async with get_session_context() as session:
        token_repo = PostgresWebhookTokenRepository(session)
        crypto_repo = PostgresCryptoTransactionRepository(session)
        
        security_service = WebhookSecurityService(
            webhook_secret=settings.TRON_DEALER_WEBHOOK_SECRET,
            token_repo=token_repo
        )
        
        payment_service = CryptoPaymentService(
            crypto_repo=crypto_repo,
            user_repo=None
        )
        
        set_services(security_service, payment_service)
    
    logger.info("✅ API server started")

    yield

    logger.info("🔌 Shutting down API server...")
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

    app.include_router(tron_dealer_router, prefix="/api/v1/webhooks")
    app.include_router(miniapp_router)

    miniapp_static_dir = Path(__file__).parent.parent.parent / "miniapp" / "static"
    if miniapp_static_dir.exists():
        app.mount("/miniapp/static", StaticFiles(directory=str(miniapp_static_dir)), name="miniapp-static")

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

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
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
