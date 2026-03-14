from fastapi import APIRouter

from infrastructure.api.android.auth import router as auth_router

android_router = APIRouter(prefix="/api/v1", tags=["Android APK"])

# Se irán agregando los sub-routers en cada fase
android_router.include_router(auth_router)
