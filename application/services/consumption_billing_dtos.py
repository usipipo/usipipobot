"""
DTOs para el servicio de facturación por consumo.

Contiene los objetos de transferencia de datos utilizados como
respuestas del servicio de facturación por consumo.

Author: uSipipo Team
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ConsumptionSummary:
    """DTO para resumen de consumo actual."""

    billing_id: Optional[uuid.UUID]
    mb_consumed: Decimal
    gb_consumed: Decimal
    total_cost_usd: Decimal
    days_active: int
    is_active: bool
    formatted_cost: str
    formatted_consumption: str


@dataclass
class ActivationResult:
    """DTO para resultado de activación del modo consumo."""

    success: bool
    billing_id: Optional[uuid.UUID] = None
    error_message: Optional[str] = None


@dataclass
class CancellationResult:
    """DTO para resultado de cancelación del modo consumo."""

    success: bool
    billing_id: Optional[uuid.UUID] = None
    mb_consumed: Decimal = Decimal("0")
    total_cost_usd: Decimal = Decimal("0")
    days_active: int = 0
    had_debt: bool = False
    error_message: Optional[str] = None
