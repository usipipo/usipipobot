"""
Telegram Message Handler Utilities

This module provides the TelegramUtils class with safe message editing,
callback query handling, and error management for Telegram handlers.

Author: uSipipo Team
"""

from typing import Optional

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from telegram_bot.common.keyboards import CommonKeyboards
from telegram_bot.common.messages import CommonMessages
from utils.logger import logger


class TelegramUtils:
    """Telegram-specific utilities for handlers."""

    @staticmethod
    async def safe_edit_message(
        query,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        reply_markup=None,
        parse_mode: Optional[str] = None,
    ) -> bool:
        """
        Safely edit message with multiple fallback strategies.

        This enhanced version integrates with CommonMessages and CommonKeyboards
        for consistent error handling and navigation.

        Args:
            query: Callback query object
            context: Application context
            text: Message text
            reply_markup: Message keyboard markup
            parse_mode: Parse mode (Markdown, HTML, etc.)

        Returns:
            bool: True if successful, False if failed
        """
        try:
            await query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
            return True
        except BadRequest as e:
            err = str(e)
            logger.warning(f"safe_edit_message: edit failed: {err}")

            err_lower = err.lower()

            # Handle "no text in message" error - send new message instead
            if "there is no text in the message" in err_lower:
                logger.warning(
                    "safe_edit_message: message has no text, sending new message"
                )
                try:
                    await context.bot.send_message(
                        chat_id=query.message.chat.id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode,
                    )
                    return True
                except Exception as ex:
                    logger.error(f"safe_edit_message: send_message fallback failed: {ex}")
                    return False

            # Handle "message not modified" - not an error, just return True
            if "message is not modified" in err_lower:
                logger.debug("safe_edit_message: message not modified (same content)")
                return True

            # If the error is due to entity parsing, retry without parse_mode
            if "can't parse entities" in err_lower or (
                "character" in err_lower and "reserved" in err_lower
            ):
                try:
                    await query.edit_message_text(text=text, reply_markup=reply_markup)
                    return True
                except BadRequest as e2:
                    logger.warning(
                        f"safe_edit_message: retry without parse_mode failed: {e2}"
                    )

            try:
                # If the message has caption, try to edit caption
                if getattr(query.message, "caption", None) is not None:
                    await query.edit_message_caption(
                        caption=text, reply_markup=reply_markup, parse_mode=parse_mode
                    )
                else:
                    # Send new message as fallback
                    await context.bot.send_message(
                        chat_id=query.message.chat.id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode,
                    )
                return True
            except BadRequest as ex:
                # If the fallback failed due to parsing errors, retry without parse_mode
                if "can't parse entities" in str(ex).lower() or (
                    "character" in str(ex) and "reserved" in str(ex)
                ):
                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat.id,
                            text=text,
                            reply_markup=reply_markup,
                        )
                        return True
                    except Exception as ex2:
                        logger.error(f"safe_edit_message fallback failed: {ex2}")
                else:
                    logger.error(f"safe_edit_message fallback failed: {ex}")
                return False
        except Exception as e:
            logger.error(f"safe_edit_message: unexpected error: {e}")
            return False

    @staticmethod
    async def safe_answer_query(query) -> bool:
        """
        Safely answer callback query.

        Args:
            query: Callback query object

        Returns:
            bool: True if successful, False if failed
        """
        if query is None:
            return False

        try:
            await query.answer()
            return True
        except Exception as e:
            logger.warning(f"safe_answer_query: failed to answer: {e}")
            return False

    @staticmethod
    def get_user_id(update: Update) -> Optional[int]:
        """
        Get user ID from update.

        Args:
            update: Telegram Update object

        Returns:
            Optional[int]: User ID or None if cannot be obtained
        """
        try:
            return update.effective_user.id if update.effective_user else None
        except Exception as e:
            logger.error(f"get_user_id: error getting user ID: {e}")
            return None

    @staticmethod
    def get_chat_id(update: Update) -> Optional[int]:
        """
        Get chat ID from update.

        Args:
            update: Telegram Update object

        Returns:
            Optional[int]: Chat ID or None if cannot be obtained
        """
        try:
            return update.effective_chat.id if update.effective_chat else None
        except Exception as e:
            logger.error(f"get_chat_id: error getting chat ID: {e}")
            return None

    @staticmethod
    async def validate_callback_query(
        query, context: ContextTypes.DEFAULT_TYPE, update: Update
    ) -> bool:
        """
        Validate callback query and handle errors.

        This enhanced version uses CommonMessages and CommonKeyboards for
        consistent error handling and navigation.

        Args:
            query: Callback query object to validate
            context: Application context
            update: Telegram Update object

        Returns:
            bool: True if query is valid, False if None
        """
        if query is None:
            logger.error("Error: query es None")
            try:
                chat_id = update.effective_chat.id if update.effective_chat else None
                if chat_id is None:
                    return False
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=CommonMessages.Error.SYSTEM_ERROR,
                    reply_markup=CommonKeyboards.back_to_main_menu(),
                )
            except Exception as e:
                logger.error(f"Error al enviar mensaje de fallback: {e}")
            return False
        return True

    @staticmethod
    async def handle_generic_error(
        context: ContextTypes.DEFAULT_TYPE,
        update: Update,
        error: Exception,
        custom_message: Optional[str] = None,
    ) -> bool:
        """
        Handle generic errors consistently.

        This enhanced version uses CommonMessages and CommonKeyboards for
        standardized error responses.

        Args:
            context: Application context
            update: Telegram Update object
            error: Exception that occurred
            custom_message: Optional custom error message

        Returns:
            bool: True if successful, False if failed
        """
        try:
            chat_id = TelegramUtils.get_chat_id(update)
            if chat_id is None:
                logger.error(f"handle_generic_error: cannot get chat_id")
                return False

            error_text = custom_message or str(error)
            await context.bot.send_message(
                chat_id=chat_id,
                text=CommonMessages.Error.SYSTEM_ERROR,
                reply_markup=CommonKeyboards.back_to_main_menu(),
            )
            return True
        except Exception as e:
            logger.error(f"handle_generic_error: failed to handle error: {e}")
            return False


# Create TelegramHandlerUtils as an alias for backward compatibility
TelegramHandlerUtils = TelegramUtils
