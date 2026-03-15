"""
Handlers para comandos básicos del bot.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from utils.logger import logger

from .messages_basic import BasicMessages


class BasicHandler:
    """Handler para comandos básicos."""

    def __init__(self):
        logger.info("📋 BasicHandler inicializado")

    async def help_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """Muestra la lista de comandos disponibles."""
        user = update.effective_user
        if user is None:
            logger.warning("No user in update for /help command")
            return

        user_id = user.id
        logger.info(f"User {user_id} executed /help command")

        try:
            if update.message:
                await update.message.reply_text(text=BasicMessages.HELP_TEXT, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"❌ Error en /help para usuario {user_id}: {e}")


def get_basic_handlers():
    """Retorna los handlers de comandos básicos."""
    logger.debug("Registering basic command handlers")
    handler = BasicHandler()

    return [
        CommandHandler("help", handler.help_handler),
    ]


def get_basic_callback_handlers():
    """Retorna los handlers de callbacks para comandos básicos."""
    logger.debug("Registering basic callback handlers (none defined)")
    return []
