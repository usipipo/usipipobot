"""
Registro de handlers para panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactored from handlers_admin.py
"""

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from application.services.admin_service import AdminService

from .handlers_admin import AdminHandler
from .handlers_keys_actions import CONFIRMING_KEY_DELETE, VIEWING_KEY_DETAILS
from .handlers_keys_list import VIEWING_KEYS
from .handlers_settings import VIEWING_MAINTENANCE, VIEWING_SETTINGS
from .handlers_tickets_actions import REPLYING_TO_TICKET
from .handlers_tickets_list import VIEWING_TICKETS
from .handlers_users_actions import CONFIRMING_USER_DELETE, VIEWING_USER_DETAILS
from .handlers_users_list import ADMIN_MENU, VIEWING_USERS


def get_admin_handlers(admin_service: AdminService):
    """Retorna los handlers administrativos."""
    handler = AdminHandler(admin_service)

    return [
        CommandHandler("admin", handler.admin_menu),
        CommandHandler("logs", handler.logs_handler),
    ]


def get_admin_callback_handlers(admin_service: AdminService):
    """Retorna los handlers de callbacks para administración."""
    handler = AdminHandler(admin_service)

    return [
        CallbackQueryHandler(handler.show_users, pattern="^admin_show_users$"),
        CallbackQueryHandler(handler.show_keys, pattern="^admin_show_keys$"),
        CallbackQueryHandler(handler.show_dashboard, pattern="^admin_server_status$"),
        CallbackQueryHandler(handler.logs_handler, pattern="^admin_logs$"),
        CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
        CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
        CallbackQueryHandler(handler.users_page, pattern=r"^users_page_\d+$"),
        CallbackQueryHandler(handler.show_user_details, pattern=r"^user_details_\d+$"),
        CallbackQueryHandler(handler.suspend_user, pattern=r"^user_suspend_\d+$"),
        CallbackQueryHandler(handler.reactivate_user, pattern=r"^user_reactivate_\d+$"),
        CallbackQueryHandler(handler.confirm_delete_user, pattern=r"^user_delete_\d+$"),
        CallbackQueryHandler(
            handler.execute_delete_user, pattern=r"^confirm_delete_user_\d+$"
        ),
        CallbackQueryHandler(
            handler.cancel_user_action, pattern=r"^cancel_delete_user$"
        ),
        CallbackQueryHandler(handler.keys_page, pattern=r"^keys_page_\d+$"),
        CallbackQueryHandler(handler.keys_filter, pattern=r"^keys_filter_\w+$"),
        CallbackQueryHandler(
            handler.show_key_details, pattern=r"^admin_key_details_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.suspend_key, pattern=r"^admin_key_suspend_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.reactivate_key, pattern=r"^admin_key_reactivate_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.confirm_delete_key, pattern=r"^admin_key_delete_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.execute_delete_key, pattern=r"^confirm_delete_key_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(handler.cancel_key_action, pattern=r"^cancel_delete_key$"),
        CallbackQueryHandler(handler.show_settings, pattern="^admin_settings$"),
        CallbackQueryHandler(handler.show_maintenance, pattern="^admin_maintenance$"),
        CallbackQueryHandler(handler.show_tickets_menu, pattern="^admin_tickets_menu$"),
        CallbackQueryHandler(handler.show_open_tickets, pattern="^admin_tickets_open$"),
        CallbackQueryHandler(handler.show_all_tickets, pattern="^admin_tickets$"),
        CallbackQueryHandler(
            handler.show_category_filter, pattern="^admin_tickets_filter$"
        ),
        CallbackQueryHandler(
            handler.filter_tickets_by_category, pattern="^admin_tickets_filter_"
        ),
        CallbackQueryHandler(
            handler.view_admin_ticket, pattern=r"^admin_ticket_[0-9a-f\-]+$"
        ),
        CallbackQueryHandler(
            handler.start_ticket_reply, pattern=r"^admin_ticket_resp_\d+$"
        ),
        CallbackQueryHandler(
            handler.close_admin_ticket, pattern=r"^admin_ticket_close_\d+$"
        ),
        CallbackQueryHandler(
            handler.reopen_admin_ticket, pattern=r"^admin_ticket_reopen_\d+$"
        ),
        CallbackQueryHandler(
            handler.show_server_settings, pattern="^settings_servers$"
        ),
        CallbackQueryHandler(handler.show_limits_settings, pattern="^settings_limits$"),
        CallbackQueryHandler(handler.clear_logs, pattern="^clear_logs$"),
        CallbackQueryHandler(handler.backup_database, pattern="^backup_db$"),
    ]


def get_admin_conversation_handler(
    admin_service: AdminService,
) -> ConversationHandler:
    """Retorna el ConversationHandler para administración."""
    handler = AdminHandler(admin_service)

    return ConversationHandler(
        entry_points=[CommandHandler("admin", handler.admin_menu)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(handler.show_users, pattern="^admin_show_users$"),
                CallbackQueryHandler(handler.show_keys, pattern="^admin_show_keys$"),
                CallbackQueryHandler(
                    handler.show_dashboard, pattern="^admin_server_status$"
                ),
                CallbackQueryHandler(handler.show_settings, pattern="^admin_settings$"),
                CallbackQueryHandler(
                    handler.show_maintenance, pattern="^admin_maintenance$"
                ),
                CallbackQueryHandler(
                    handler.show_tickets_menu, pattern="^admin_tickets_menu$"
                ),
                CallbackQueryHandler(handler.logs_handler, pattern="^admin_logs$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_USERS: [
                CallbackQueryHandler(handler.users_page, pattern=r"^users_page_\d+$"),
                CallbackQueryHandler(
                    handler.show_user_details, pattern=r"^user_details_\d+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_USER_DETAILS: [
                CallbackQueryHandler(handler.show_users, pattern="^admin_show_users$"),
                CallbackQueryHandler(
                    handler.suspend_user, pattern=r"^user_suspend_\d+$"
                ),
                CallbackQueryHandler(
                    handler.reactivate_user, pattern=r"^user_reactivate_\d+$"
                ),
                CallbackQueryHandler(
                    handler.confirm_delete_user, pattern=r"^user_delete_\d+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            CONFIRMING_USER_DELETE: [
                CallbackQueryHandler(
                    handler.execute_delete_user, pattern=r"^confirm_delete_user_\d+$"
                ),
                CallbackQueryHandler(
                    handler.cancel_user_action, pattern=r"^cancel_delete_user$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
            ],
            VIEWING_KEYS: [
                CallbackQueryHandler(handler.keys_page, pattern=r"^keys_page_\d+$"),
                CallbackQueryHandler(handler.keys_filter, pattern=r"^keys_filter_\w+$"),
                CallbackQueryHandler(
                    handler.show_key_details, pattern=r"^admin_key_details_[a-f0-9\-]+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_KEY_DETAILS: [
                CallbackQueryHandler(handler.show_keys, pattern="^admin_show_keys$"),
                CallbackQueryHandler(
                    handler.suspend_key, pattern=r"^admin_key_suspend_[a-f0-9\-]+$"
                ),
                CallbackQueryHandler(
                    handler.reactivate_key,
                    pattern=r"^admin_key_reactivate_[a-f0-9\-]+$",
                ),
                CallbackQueryHandler(
                    handler.confirm_delete_key,
                    pattern=r"^admin_key_delete_[a-f0-9\-]+$",
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            CONFIRMING_KEY_DELETE: [
                CallbackQueryHandler(
                    handler.execute_delete_key,
                    pattern=r"^confirm_delete_key_[a-f0-9\-]+$",
                ),
                CallbackQueryHandler(
                    handler.cancel_key_action, pattern=r"^cancel_delete_key$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
            ],
            VIEWING_SETTINGS: [
                CallbackQueryHandler(
                    handler.show_server_settings, pattern="^settings_servers$"
                ),
                CallbackQueryHandler(
                    handler.show_limits_settings, pattern="^settings_limits$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_MAINTENANCE: [
                CallbackQueryHandler(handler.clear_logs, pattern="^clear_logs$"),
                CallbackQueryHandler(handler.backup_database, pattern="^backup_db$"),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_TICKETS: [
                CallbackQueryHandler(
                    handler.show_open_tickets, pattern="^admin_tickets_open$"
                ),
                CallbackQueryHandler(
                    handler.show_all_tickets, pattern="^admin_tickets$"
                ),
                CallbackQueryHandler(
                    handler.show_tickets_menu, pattern="^admin_tickets_menu$"
                ),
                CallbackQueryHandler(
                    handler.show_category_filter, pattern="^admin_tickets_filter$"
                ),
                CallbackQueryHandler(
                    handler.filter_tickets_by_category, pattern="^admin_tickets_filter_"
                ),
                CallbackQueryHandler(
                    handler.view_admin_ticket, pattern=r"^admin_ticket_[0-9a-f\-]+$"
                ),
                CallbackQueryHandler(
                    handler.start_ticket_reply, pattern=r"^admin_ticket_resp_\d+$"
                ),
                CallbackQueryHandler(
                    handler.close_admin_ticket, pattern=r"^admin_ticket_close_\d+$"
                ),
                CallbackQueryHandler(
                    handler.reopen_admin_ticket, pattern=r"^admin_ticket_reopen_\d+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            REPLYING_TO_TICKET: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handler.send_ticket_reply
                ),
                CallbackQueryHandler(
                    handler.show_tickets_menu, pattern="^admin_tickets_menu$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", handler.end_admin),
            CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
        ],
        per_message=False,
        per_chat=True,
        per_user=True,
        allow_reentry=True,
    )
