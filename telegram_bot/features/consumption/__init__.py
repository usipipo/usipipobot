"""Módulo de tarifa por consumo (Pay-as-You-Go)."""

from telegram_bot.features.consumption.handlers_consumption import (
    ConsumptionHandler,
    get_consumption_callback_handlers,
    get_consumption_handlers,
)
from telegram_bot.features.consumption.keyboards_consumption import (
    ConsumptionKeyboards,
)
from telegram_bot.features.consumption.messages_consumption import (
    ConsumptionMessages,
)

__all__ = [
    "ConsumptionHandler",
    "ConsumptionKeyboards",
    "ConsumptionMessages",
    "get_consumption_handlers",
    "get_consumption_callback_handlers",
]
