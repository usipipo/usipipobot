"""
Handlers para comandos básicos del bot.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.logger import logger
from .messages_basic import BasicMessages
from telegram_bot.keyboards import MainMenuKeyboard
from config import settings
from application.services.vpn_service import VpnService


class BasicHandler:
    """Handler para comandos básicos."""

    def __init__(self, vpn_service: VpnService):
        self.vpn_service = vpn_service
        logger.info("📋 BasicHandler inicializado")

    async def help_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """Muestra la lista de comandos disponibles."""
        logger.info(f"📋 /help ejecutado por usuario {update.effective_user.id}")
        
        await update.message.reply_text(
            text=BasicMessages.HELP_TEXT,
            parse_mode="Markdown"
        )


def get_basic_handlers(vpn_service: VpnService):
    """Retorna los handlers de comandos básicos."""
    handler = BasicHandler(vpn_service)

    return [
        CommandHandler("help", handler.help_handler),
    ]


def get_basic_callback_handlers(vpn_service: VpnService):
    """Retorna los handlers de callbacks para comandos básicos."""
    return []
