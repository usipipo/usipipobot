from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text, func
from datetime import datetime, timezone, timedelta
from loguru import logger

from infrastructure.api.android.dashboard_schemas import (
    DashboardSummaryResponse,
    UserInfo,
    DataSummaryInfo,
    ActiveKeyInfo,
    ActivePackageInfo
)
from infrastructure.api.android.deps import get_current_user
from infrastructure.persistence.database import get_session_context


router = APIRouter(prefix="/dashboard", tags=["Android Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(payload: dict = Depends(get_current_user)):
    """
    Get complete dashboard summary in a single call.
    
    Returns all data needed to render the dashboard:
    - User information with referral credits
    - Data usage summary (aggregated across all keys)
    - List of active VPN keys
    - Active package information (if any)
    
    **Authentication:** Requires valid JWT token
    
    **Caching:** Client should cache for 15 minutes
    """
    telegram_id = int(payload["sub"])
    
    async with get_session_context() as session:
        # Fetch user data
        user_result = await session.execute(
            text("""
                SELECT 
                    telegram_id, username, full_name, photo_url, status, role,
                    referral_credits, has_pending_debt, consumption_mode_enabled,
                    last_login
                FROM users
                WHERE telegram_id = :telegram_id
            """),
            {"telegram_id": telegram_id}
        )
        user_row = user_result.first()
        
        if not user_row:
            logger.warning(f"User {telegram_id} not found")
            raise HTTPException(
                status_code=404,
                detail={"error": "user_not_found", "message": "Usuario no encontrado"}
            )
        
        # Fetch VPN keys (active and recent, max 10)
        keys_result = await session.execute(
            text("""
                SELECT 
                    id, name, key_type, is_active,
                    COALESCE(data_used_bytes, 0) as used_bytes,
                    data_limit_bytes, expires_at, last_seen_at
                FROM vpn_keys
                WHERE telegram_id = :telegram_id
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"telegram_id": telegram_id}
        )
        keys_rows = keys_result.all()
        
        # Calculate total data usage from all keys
        total_used_bytes = sum(key.used_bytes for key in keys_rows)
        
        # Fetch active package (if any)
        package_result = await session.execute(
            text("""
                SELECT 
                    package_type, data_limit_bytes, 
                    COALESCE(data_used_bytes, 0) as data_used_bytes,
                    expires_at
                FROM data_packages
                WHERE telegram_id = :telegram_id
                  AND is_active = TRUE
                  AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"telegram_id": telegram_id}
        )
        package_row = package_result.first()
        
        # Determine data limit source
        if package_row and package_row.data_limit_bytes:
            total_limit_bytes = package_row.data_limit_bytes
            data_source = "package"
        else:
            # Free tier: 5 GB default
            total_limit_bytes = 5 * 1024 * 1024 * 1024  # 5 GB
            data_source = "free_tier"
        
        # Build active keys list
        active_keys = []
        for key_row in keys_rows:
            active_keys.append(ActiveKeyInfo(
                id=str(key_row.id),
                name=key_row.name or "Sin nombre",
                key_type=key_row.key_type,
                is_active=key_row.is_active,
                used_bytes=key_row.used_bytes,
                data_limit_bytes=key_row.data_limit_bytes,
                expires_at=key_row.expires_at,
                last_seen_at=key_row.last_seen_at
            ))
        
        # Build active package info
        active_package = None
        if package_row:
            days_remaining = None
            if package_row.expires_at:
                delta = package_row.expires_at - datetime.now(timezone.utc)
                days_remaining = max(0, delta.days)
            
            active_package = ActivePackageInfo(
                package_type=package_row.package_type,
                data_limit_bytes=package_row.data_limit_bytes,
                data_used_bytes=package_row.data_used_bytes,
                expires_at=package_row.expires_at,
                days_remaining=days_remaining
            )
        
        logger.info(f"Dashboard summary fetched for user {telegram_id}")
        
        return DashboardSummaryResponse(
            user=UserInfo(
                telegram_id=user_row.telegram_id,
                username=user_row.username,
                full_name=user_row.full_name,
                photo_url=user_row.photo_url,
                status=user_row.status,
                role=user_row.role or "user",
                referral_credits=user_row.referral_credits or 0,
                has_pending_debt=user_row.has_pending_debt or False,
                consumption_mode_enabled=user_row.consumption_mode_enabled or False,
                last_login=user_row.last_login
            ),
            data_summary=DataSummaryInfo(
                total_used_bytes=total_used_bytes,
                total_limit_bytes=total_limit_bytes,
                source=data_source
            ),
            active_keys=active_keys,
            active_package=active_package,
            referral_credits=user_row.referral_credits or 0,
            has_pending_debt=user_row.has_pending_debt or False,
            consumption_mode_enabled=user_row.consumption_mode_enabled or False
        )
