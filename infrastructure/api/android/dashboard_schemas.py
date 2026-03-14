from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserInfo(BaseModel):
    """User information for dashboard."""
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    role: str = "user"
    referral_credits: int = 0
    has_pending_debt: bool = False
    consumption_mode_enabled: bool = False
    last_login: Optional[datetime] = None


class DataSummaryInfo(BaseModel):
    """Data usage summary."""
    total_used_bytes: int = 0
    total_limit_bytes: int = 0
    source: str = "free_tier"  # free_tier | package


class ActiveKeyInfo(BaseModel):
    """Active VPN key information."""
    id: str
    name: str
    key_type: str  # outline | wireguard
    is_active: bool = True
    used_bytes: int = 0
    data_limit_bytes: Optional[int] = None
    expires_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class ActivePackageInfo(BaseModel):
    """Active data package information."""
    package_type: Optional[str] = None  # basic | standard | advanced | premium
    data_limit_bytes: Optional[int] = None
    data_used_bytes: int = 0
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None


class DashboardSummaryResponse(BaseModel):
    """
    Complete dashboard summary response.

    Contains all data needed to render the dashboard in a single call.
    """
    user: UserInfo
    data_summary: DataSummaryInfo
    active_keys: List[ActiveKeyInfo] = Field(default_factory=list)
    active_package: Optional[ActivePackageInfo] = None
    referral_credits: int = 0
    has_pending_debt: bool = False
    consumption_mode_enabled: bool = False
    max_keys: int = 2  # Maximum number of VPN keys allowed per user

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "telegram_id": 123456789,
                    "username": "juanperez",
                    "full_name": "Juan Pérez",
                    "photo_url": "https://t.me/i/userpic/320/abc123.jpg",
                    "status": "active",
                    "role": "user",
                    "referral_credits": 12,
                    "has_pending_debt": False,
                    "consumption_mode_enabled": False,
                    "last_login": "2026-02-15T14:00:00Z"
                },
                "data_summary": {
                    "total_used_bytes": 2361393152,
                    "total_limit_bytes": 5368709120,
                    "source": "free_tier"
                },
                "active_keys": [
                    {
                        "id": "uuid-1234-5678",
                        "name": "Mi iPhone",
                        "key_type": "outline",
                        "is_active": True,
                        "used_bytes": 1288490188,
                        "data_limit_bytes": 5368709120,
                        "expires_at": None,
                        "last_seen_at": "2026-02-15T12:00:00Z"
                    }
                ],
                "active_package": {
                    "package_type": "estandar",
                    "data_limit_bytes": 16106127360,
                    "data_used_bytes": 1288490188,
                    "expires_at": "2026-03-15T00:00:00Z",
                    "days_remaining": 28
                },
                "max_keys": 2
            }
        }
    }
