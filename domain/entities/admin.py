"""
Entidades de administración para el bot uSipipo.

Author: uSipipo Team
Version: 2.0.0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AdminUserInfo:
    """Información de usuario para administración."""

    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    total_keys: int
    active_keys: int
    stars_balance: int = 0  # Deprecated - mantener por compatibilidad
    total_deposited: int = 0  # Ahora representa referral_credits
    referral_credits: int = 0
    registration_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None


@dataclass
class AdminKeyInfo:
    """Información de clave para administración."""

    key_id: str
    user_id: int
    user_name: str
    key_type: str
    key_name: str
    access_url: Optional[str]
    created_at: datetime
    last_used: Optional[datetime]
    data_limit: int
    data_used: int
    is_active: bool
    server_status: str


@dataclass
class ServerStatus:
    """Estado del servidor VPN."""

    server_type: str
    is_healthy: bool
    total_keys: int
    active_keys: int
    version: Optional[str]
    uptime: Optional[str]
    error_message: Optional[str] = None


@dataclass
class AdminOperationResult:
    """Resultado de operación administrativa."""

    success: bool
    operation: str
    target_id: str
    message: str
    details: Optional[Dict] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
