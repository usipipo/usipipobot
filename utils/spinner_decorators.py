"""
Decoradores del sistema de Spinner.

Este módulo proporciona decoradores para agregar spinners a funciones
asíncronas, incluyendo spinners animados y especializados por tipo de operación.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional

from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger
from utils.spinner_core import SpinnerManager


def _extract_update_context(
    args: tuple, kwargs: dict
) -> tuple[Optional[Update], Optional[Any]]:
    """Extrae update y context de los argumentos de una función."""
    update = None
    context = None
    for arg in args:
        if isinstance(arg, Update):
            update = arg
        elif hasattr(arg, "bot"):
            context = arg
    if "context" in kwargs and hasattr(kwargs["context"], "bot"):
        context = kwargs["context"]
    if "update" in kwargs and isinstance(kwargs["update"], Update):
        update = kwargs["update"]
    return update, context


def with_spinner(
    operation_type: str = "default",
    custom_message: Optional[str] = None,
    show_duration: bool = False,
):
    """Decorador para agregar spinner a funciones asíncronas."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            update, context = _extract_update_context(args, kwargs)
            if not update:
                return await func(*args, **kwargs)
            chat = update.effective_chat
            if chat is None:
                return await func(*args, **kwargs)
            chat_id = chat.id
            spinner_message_id = None
            start_time = None
            try:
                logger.info(f"🌀 Iniciando spinner para {func.__name__}")
                spinner_message_id = await SpinnerManager.send_spinner_message(
                    update, operation_type, custom_message
                )
                logger.info(f"🌀 Spinner enviado con ID: {spinner_message_id}")
                if show_duration:
                    start_time = asyncio.get_event_loop().time()
                result = await func(*args, **kwargs)
                if show_duration and start_time:
                    duration = asyncio.get_event_loop().time() - start_time
                    if duration < 1.0:
                        await asyncio.sleep(1.0 - duration)
                if spinner_message_id and context:
                    if update.callback_query:
                        logger.info(
                            f"🔄 Spinner para callback será reemplazado por el handler"
                        )
                    else:
                        logger.info(f"🗑️  Eliminando spinner ID: {spinner_message_id}")
                        success = await SpinnerManager.delete_spinner_message(
                            context, chat_id, spinner_message_id
                        )
                        logger.info(f"🗑️  Spinner eliminado: {success}")
                else:
                    logger.warning(
                        f"⚠️  No se pudo eliminar spinner - ID: {spinner_message_id}, Context: {context is not None}"
                    )
                if show_duration and start_time and context:
                    duration = asyncio.get_event_loop().time() - start_time
                    await SpinnerManager.safe_reply_text(
                        update, f"✅ Operación completada en {duration:.2f}s"
                    )
                return result
            except Exception as e:
                logger.error(f"❌ Error en función con spinner {func.__name__}: {e}")
                logger.error(f"❌ Tipo de excepción: {type(e).__name__}")
                if spinner_message_id and context:
                    try:
                        logger.info(f"🗑️  Intentando eliminar spinner después de error")
                        await SpinnerManager.delete_spinner_message(
                            context, chat_id, spinner_message_id
                        )
                        await SpinnerManager.safe_reply_text(
                            update,
                            "❌ Ocurrió un error durante la operación. Por favor, intenta nuevamente.",
                        )
                    except Exception as delete_error:
                        logger.error(f"❌ Error eliminando spinner: {delete_error}")
                raise e

        return wrapper

    return decorator


def with_animated_spinner(
    operation_type: str = "default",
    custom_message: Optional[str] = None,
    update_interval: float = 0.5,
):
    """Decorador para spinner animado que se actualiza periódicamente."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            update, context = _extract_update_context(args, kwargs)
            if not update:
                return await func(*args, **kwargs)
            chat = update.effective_chat
            if chat is None:
                return await func(*args, **kwargs)
            chat_id = chat.id
            spinner_message_id = None
            animation_task = None

            async def animate_spinner():
                while True:
                    if spinner_message_id and context:
                        await SpinnerManager.update_spinner_message(
                            context,
                            chat_id,
                            spinner_message_id,
                            operation_type,
                            custom_message,
                        )
                    await asyncio.sleep(update_interval)

            try:
                spinner_message_id = await SpinnerManager.send_spinner_message(
                    update, operation_type, custom_message
                )
                animation_task = asyncio.create_task(animate_spinner())
                result = await func(*args, **kwargs)
                if animation_task:
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass
                if spinner_message_id and context:
                    await SpinnerManager.delete_spinner_message(
                        context, chat_id, spinner_message_id
                    )
                return result
            except Exception as e:
                logger.error(
                    f"Error en función con spinner animado {func.__name__}: {e}"
                )
                if animation_task:
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass
                if spinner_message_id and context:
                    try:
                        await SpinnerManager.delete_spinner_message(
                            context, chat_id, spinner_message_id
                        )
                        await SpinnerManager.safe_reply_text(
                            update,
                            "❌ Ocurrió un error durante la operación. Por favor, intenta nuevamente.",
                        )
                    except:
                        pass
                raise e

        return wrapper

    return decorator


def _create_callback_spinner_decorator(operation_type: str):
    """Factory para crear decoradores de spinner específicos para callbacks."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            update, context = _extract_update_context(args, kwargs)
            if not update or not update.callback_query:
                return await with_spinner("loading")(func)(self, *args, **kwargs)
            chat = update.effective_chat
            if chat is None:
                return await with_spinner("loading")(func)(self, *args, **kwargs)
            chat_id = chat.id
            spinner_message_id = None
            try:
                logger.info(f"🌀 Iniciando spinner para {func.__name__}")
                spinner_message_id = await SpinnerManager.send_spinner_message(
                    update, operation_type
                )
                logger.info(f"🌀 Spinner enviado con ID: {spinner_message_id}")
                result = await func(
                    self, update, context, spinner_message_id, *args[3:], **kwargs
                )
                return result
            except Exception as e:
                logger.error(
                    f"❌ Error en función con spinner callback {func.__name__}: {e}"
                )
                if spinner_message_id and context:
                    try:
                        logger.info(f"🗑️  Intentando eliminar spinner después de error")
                        await SpinnerManager.delete_spinner_message(
                            context, chat_id, spinner_message_id
                        )
                        await SpinnerManager.safe_reply_text(
                            update,
                            "❌ Ocurrió un error durante la operación. Por favor, intenta nuevamente.",
                        )
                    except Exception as delete_error:
                        logger.error(f"❌ Error eliminando spinner: {delete_error}")
                raise e

        return wrapper

    return decorator


# Decoradores específicos para tipos de operaciones comunes
def database_spinner(func: Callable) -> Callable:
    """Spinner específico para operaciones de base de datos."""
    return with_spinner("database")(func)


def vpn_spinner(func: Callable) -> Callable:
    """Spinner específico para operaciones VPN."""
    return with_spinner("vpn")(func)


def registration_spinner(func: Callable) -> Callable:
    """Spinner específico para registro de usuarios."""
    return with_spinner("register", show_duration=True)(func)


def payment_spinner(func: Callable) -> Callable:
    """Spinner específico para operaciones de pago."""
    return with_spinner("payment")(func)


# Decoradores específicos para callbacks
shop_spinner_callback = _create_callback_spinner_decorator("loading")
admin_spinner_callback = _create_callback_spinner_decorator("loading")
database_spinner_callback = _create_callback_spinner_decorator("database")
