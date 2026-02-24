import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from infrastructure.api.middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from infrastructure.api.webhooks import tron_dealer_router
from infrastructure.persistence.database import init_database, close_database
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Initializing API server...")
    await init_database()
    logger.info("✅ API server started")

    yield

    logger.info("🔌 Shutting down API server...")
    await close_database()
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
