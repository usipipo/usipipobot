"""
Modulo de compra de GB con Telegram Stars.

Author: uSipipo Team
Version: 1.0.0
"""

from .handlers_buy_gb import (
    get_buy_gb_handlers,
    get_buy_gb_callback_handlers,
    get_buy_gb_payment_handlers
)

__all__ = [
    "get_buy_gb_handlers",
    "get_buy_gb_callback_handlers",
    "get_buy_gb_payment_handlers"
]
