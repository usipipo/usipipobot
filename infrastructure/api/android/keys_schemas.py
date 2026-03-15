"""
Schemas for VPN keys endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VpnKeyListItem(BaseModel):
    """Schema for VPN key list item."""

    id: str
    name: str
    key_type: str  # "outline" | "wireguard"
    server: str
    is_active: bool
    used_bytes: int
    data_limit_bytes: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class VpnKeyDetail(BaseModel):
    """Schema for VPN key detail with full information."""

    id: str
    name: str
    key_type: str  # "outline" | "wireguard"
    key_data: str  # Connection string (ss://... or WireGuard config)
    server: str
    is_active: bool
    used_bytes: int
    data_limit_bytes: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    billing_reset_at: Optional[datetime] = None
    external_id: Optional[str] = None


class CreateKeyRequest(BaseModel):
    """Request schema for creating a VPN key."""

    key_type: str = Field(..., description="outline | wireguard")
    name: str = Field(..., min_length=1, max_length=30, description="Key name (max 30 chars)")


class CreateKeyResponse(BaseModel):
    """Response schema for created VPN key."""

    id: str
    name: str
    key_type: str
    key_data: str
    qr_data: str  # Same as key_data, for QR display
    server: str
    is_active: bool
    data_limit_bytes: int
    created_at: datetime


class RenameKeyRequest(BaseModel):
    """Request schema for renaming a VPN key."""

    name: str = Field(..., min_length=1, max_length=30, description="New key name (max 30 chars)")


class CanCreateKeyResponse(BaseModel):
    """Response schema for key creation capability check."""

    can_create: bool
    can_create_outline: bool
    can_create_wireguard: bool
    current_count: int
    max_keys: int
    reason: Optional[str] = None


class KeysListResponse(BaseModel):
    """Response schema for listing VPN keys."""

    keys: List[VpnKeyListItem]
    total_count: int
    active_count: int
    max_keys: int


class KeyUsageInfo(BaseModel):
    """Schema for key usage information."""

    used_bytes: int
    data_limit_bytes: int
    remaining_bytes: int
    usage_percentage: float
    billing_reset_at: datetime


class KeyConnectionInfo(BaseModel):
    """Schema for key connection information."""

    key_data: str
    qr_image_base64: Optional[str] = None  # QR code as base64 image
    connection_instructions: str
