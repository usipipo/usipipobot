from fastapi import APIRouter

from infrastructure.api.android.auth import router as auth_router
from infrastructure.api.android.dashboard import router as dashboard_router

android_router = APIRouter(prefix="/api/v1", tags=["Android APK"])

# Register sub-routers
android_router.include_router(auth_router)
android_router.include_router(dashboard_router)
