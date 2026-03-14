"""
Core del sistema de Spinner - Gestión de mensajes y operaciones.

Este módulo proporciona la clase SpinnerManager para gestionar
mensajes de spinner en operaciones asíncronas del bot.
"""

import time
from typing import Optional, cast

from telegram import Message, Update
from telegram.ext import ContextTypes

from utils.logger import logger
from utils.spinner_styles import SpinnerStyles


class SpinnerManager:
    """Gestiona los spinners para operaciones asíncronas."""

    @staticmethod
    def get_random_spinner_message(operation_type: str = "default") -> str:
        """Obtiene un mensaje de spinner con emoji animado."""
        base_message = SpinnerStyles.MESSAGES.get(operation_type, SpinnerStyles.MESSAGES["default"])

        try:
            frame_index = int(time.time() * 10) % len(SpinnerStyles.SPINNER_FRAMES)
            frame = SpinnerStyles.SPINNER_FRAMES[frame_index]
            return f"{frame} {base_message}"
        except AttributeError as e:
            logger.error(f"❌ Error en get_random_spinner_message: {e}")
            logger.error(f"Atributos disponibles en SpinnerStyles: {dir(SpinnerStyles)}")
            return f"🌀 {base_message}"

    @staticmethod
    async def replace_spinner_with_message(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None,
        text: str,
        reply_markup=None,
        parse_mode: str = "Markdown",
    ):
        """
        Reemplaza el spinner con el mensaje final del handler.

        Args:
            update: Objeto Update de Telegram
            context: Contexto del bot
            spinner_message_id: ID del mensaje spinner a eliminar
            text: Texto del mensaje final
            reply_markup: Teclado del mensaje final
            parse_mode: Modo de parseo
        """
        try:
            chat = update.effective_chat
            if chat is None:
                return
            chat_id = chat.id

            if spinner_message_id:
                logger.info(f"🗑️  Eliminando spinner ID: {spinner_message_id}")
                success = await SpinnerManager.delete_spinner_message(
                    context, chat_id, spinner_message_id
                )
                logger.info(f"🗑️  Spinner eliminado: {success}")

            if update.callback_query:
                try:
                    await update.callback_query.edit_message_text(
                        text=text, reply_markup=reply_markup, parse_mode=parse_mode
                    )
                except Exception as e:
                    error_msg = str(e).lower()
                    if "there is no text in the message" in error_msg:
                        logger.warning(
                            f"⚠️  Mensaje original no tiene texto, enviando nuevo mensaje: {e}"
                        )
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode,
                        )
                    elif "can't parse entities" in error_msg:
                        logger.warning(
                            f"⚠️  Error de parsing Markdown, reintentando sin parse_mode: {e}"
                        )
                        try:
                            await update.callback_query.edit_message_text(
                                text=text, reply_markup=reply_markup
                            )
                        except Exception as e2:
                            logger.warning(f"⚠️  Edit falló de nuevo, enviando mensaje nuevo: {e2}")
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=text,
                                reply_markup=reply_markup,
                            )
                    elif "message is not modified" in error_msg:
                        logger.debug("ℹ️  Mensaje no modificado (mismo contenido)")
                    else:
                        logger.warning(f"⚠️  Error editando mensaje, enviando nuevo: {e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode,
                        )
            elif update.message:
                try:
                    await update.message.reply_text(
                        text=text, reply_markup=reply_markup, parse_mode=parse_mode
                    )
                except Exception as e:
                    if "can't parse entities" in str(e).lower():
                        logger.warning(
                            f"⚠️  Error de parsing Markdown, reintentando sin parse_mode: {e}"
                        )
                        await update.message.reply_text(text=text, reply_markup=reply_markup)
                    else:
                        raise

        except Exception as e:
            logger.error(f"❌ Error reemplazando spinner: {e}")

    @staticmethod
    async def safe_reply_text(update: Update, text: str, parse_mode: str = "Markdown"):
        """
        Método seguro para responder mensajes.

        Args:
            update: Objeto Update de Telegram
            text: Texto del mensaje
            parse_mode: Modo de parseo
        """
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(text=text, parse_mode=parse_mode)
            elif update.message:
                await update.message.reply_text(text=text, parse_mode=parse_mode)
            else:
                logger.error(
                    "❌ No se puede responder: ni update.message ni update.callback_query disponibles"
                )
        except Exception as e:
            logger.error(f"❌ Error en safe_reply_text: {e}")

    @staticmethod
    async def send_spinner_message(
        update: Update,
        operation_type: str = "default",
        custom_message: Optional[str] = None,
    ) -> int:
        """
        Envía un mensaje de spinner y retorna el message_id.

        Args:
            update: Objeto Update de Telegram
            operation_type: Tipo de operación para mensaje predefinido
            custom_message: Mensaje personalizado (sobrescribe operation_type)

        Returns:
            message_id del spinner enviado
        """
        try:
            message_text = custom_message or SpinnerManager.get_random_spinner_message(
                operation_type
            )
            logger.info(f"🌀 Preparando spinner: {message_text}")

            spinner_message = None

            if update.callback_query:
                await update.callback_query.answer()
                callback_message = update.callback_query.message
                if callback_message is None:
                    logger.error(
                        "❌ No se puede enviar spinner: callback_query.message no disponible"
                    )
                    return -1
                if not isinstance(callback_message, Message):
                    logger.error(
                        "❌ No se puede enviar spinner: callback_query.message es MaybeInaccessibleMessage"
                    )
                    return -1
                msg = cast(Message, callback_message)
                spinner_message = await msg.reply_text(text=message_text, parse_mode="Markdown")
            elif update.message:
                spinner_message = await update.message.reply_text(
                    text=message_text, parse_mode="Markdown"
                )
            else:
                logger.error(
                    "❌ No se puede enviar spinner: ni update.message ni update.callback_query disponibles"
                )
                return -1

            logger.info(f"✅ Spinner enviado: {message_text} (ID: {spinner_message.message_id})")
            return spinner_message.message_id

        except Exception as e:
            logger.error(f"❌ Error enviando spinner: {e}")
            logger.error(f"Tipo de excepción: {type(e).__name__}")
            return -1

    @staticmethod
    async def update_spinner_message(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        message_id: int,
        operation_type: str = "default",
        custom_message: Optional[str] = None,
    ) -> bool:
        """
        Actualiza un mensaje de spinner existente.

        Args:
            context: Contexto del bot
            chat_id: ID del chat
            message_id: ID del mensaje a actualizar
            operation_type: Tipo de operación para mensaje predefinido
            custom_message: Mensaje personalizado

        Returns:
            True si se actualizó correctamente
        """
        try:
            message_text = custom_message or SpinnerManager.get_random_spinner_message(
                operation_type
            )

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message_text,
                parse_mode="Markdown",
            )

            return True

        except Exception as e:
            logger.error(f"Error actualizando spinner: {e}")
            return False

    @staticmethod
    async def delete_spinner_message(
        context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int
    ) -> bool:
        """
        Elimina un mensaje de spinner.

        Args:
            context: Contexto del bot
            chat_id: ID del chat
            message_id: ID del mensaje a eliminar

        Returns:
            True si se eliminó correctamente
        """
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            return True

        except Exception as e:
            logger.error(f"Error eliminando spinner: {e}")
            return False
