"""
Keys list screen for uSipipo VPN Android APK.
Shows all VPN keys with their status and usage.
"""

from typing import Any, Dict, List, Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from loguru import logger
from src.components.vpn_key_card import VpnKeyCard
from src.services.auth_service import AuthService
from src.services.keys_service import KeysService, VpnKeyData


class KeysListScreen(MDScreen):
    """
    Screen for listing all VPN keys.

    Features:
    - List of all VPN keys (active and inactive)
    - Visual cards with key info and usage
    - Color-coded by key type (Outline/WireGuard)
    - Progress bars for data usage
    - Status badges (Active/Inactive/Expired)
    - Pull-to-refresh
    - Create new key button
    - Tap to view key detail
    - Auto-refresh every 60 seconds
    """

    # User properties
    username = StringProperty("Usuario")

    # Keys properties
    keys_list = ListProperty([])  # List of dicts for UI
    total_count = NumericProperty(0)
    active_count = NumericProperty(0)
    max_keys = NumericProperty(2)

    # Status properties
    is_loading = BooleanProperty(True)
    is_offline = BooleanProperty(False)
    has_error = BooleanProperty(False)
    error_message = StringProperty("")

    # Auto-refresh
    _auto_refresh_event = None
    _refresh_interval = 60  # seconds

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.keys_service: Optional[KeysService] = None
        self.dialog = None
        self.refresh_layout = None
        self._telegram_id = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Keys list screen entered")
        self.load_keys()
        self._start_auto_refresh()

    def on_leave(self):
        """Called when screen is left."""
        self._stop_auto_refresh()

    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        self._stop_auto_refresh()
        self._auto_refresh_event = Clock.schedule_interval(
            lambda dt: self._auto_refresh_callback(), self._refresh_interval
        )
        logger.debug(f"Auto-refresh started (interval: {self._refresh_interval}s)")

    def _stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self._auto_refresh_event:
            self._auto_refresh_event.cancel()
            self._auto_refresh_event = None
            logger.debug("Auto-refresh stopped")

    def _auto_refresh_callback(self):
        """Callback for auto-refresh."""
        # Only refresh if screen is current and not already loading
        if (
            not self.is_offline
            and self.manager
            and self.manager.current == self.name
            and not self.is_loading
        ):
            logger.debug("Auto-refreshing keys list")
            self.load_keys(force_refresh=False)

    def setup_pull_to_refresh(self):
        """Setup pull-to-refresh layout."""
        if self.ids.get("refresh_layout"):
            self.refresh_layout = self.ids.refresh_layout
            logger.debug("Pull-to-refresh layout configured")

    def load_keys(self, force_refresh: bool = False):
        """
        Load VPN keys from API.

        Args:
            force_refresh: If True, bypass cache
        """
        self.is_loading = True
        self.has_error = False

        # Get current user
        telegram_id = self.auth_service.get_current_user()
        if not telegram_id:
            logger.warning("No authenticated user, redirecting to login")
            Clock.schedule_once(lambda dt: self._redirect_to_login(), 0.5)
            return

        self._telegram_id = telegram_id
        self.keys_service = KeysService()

        # Load data asynchronously
        Clock.schedule_once(lambda dt: self._fetch_keys(force_refresh), 0)

    def _redirect_to_login(self):
        """Redirect to login screen."""
        if self.manager:
            self.manager.current = "login"

    async def _fetch_keys_async(self, force_refresh: bool):
        """Fetch keys data asynchronously."""
        try:
            response = await self.keys_service.list_keys()

            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_keys_list(response))

        except Exception as err:
            logger.error(f"Error fetching keys: {err}")
            Clock.schedule_once(lambda dt, e=err: self._handle_load_error(e))

    def _fetch_keys(self, force_refresh: bool = False):
        """Fetch keys data (async wrapper)."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._fetch_keys_async(force_refresh))

        with ThreadPoolExecutor() as executor:
            executor.submit(run_async)

    def _update_keys_list(self, data: Dict[str, Any]):
        """
        Update UI with keys data.

        Args:
            data: Keys data from API
        """
        try:
            keys: List[VpnKeyData] = data.get("keys", [])
            self.total_count = data.get("total_count", 0)
            self.active_count = data.get("active_count", 0)
            self.max_keys = data.get("max_keys", 2)

            # Get cards container
            cards_container = self.ids.get("cards_container")
            if cards_container:
                cards_container.clear_widgets()

            # Create VpnKeyCard widgets for each key
            for key in keys:
                card = VpnKeyCard()
                card.key_name = key.name
                card.key_type = key.key_type
                card.is_active = key.is_active
                card.key_usage = f"{self.keys_service.format_bytes(key.used_bytes)} / {self.keys_service.format_bytes(key.data_limit_bytes)}"

                # Bind tap event to navigate to detail
                card.bind(on_release=lambda instance, k=key: self.on_key_card_pressed(k.id))

                if cards_container:
                    cards_container.add_widget(card)

            self.is_loading = False
            logger.debug(f"Keys list updated: {len(keys)} keys rendered as cards")

        except Exception as e:
            logger.error(f"Error updating keys list: {e}")
            self._handle_load_error(e)

    def _handle_load_error(self, error: Exception):
        """Handle load error."""
        self.is_loading = False
        self.has_error = True
        self.error_message = str(error)
        logger.error(f"Keys load error: {error}")

        Snackbar(text="Error cargando claves. Verifica tu conexión.", duration=3).open()

    def on_refresh(self):
        """Handle pull-to-refresh action."""
        logger.info("Keys list refresh requested")
        self.load_keys(force_refresh=True)

        if self.refresh_layout:
            self.refresh_layout.done()

    def on_create_key_pressed(self):
        """Handle create new key button press."""
        logger.info("Navigate to create key screen")

        # First check if user can create keys
        self._check_and_navigate_to_create()

    async def _check_can_create_async(self):
        """Check if user can create keys."""
        try:
            can_create_data = await self.keys_service.can_create_key()
            Clock.schedule_once(lambda dt: self._navigate_if_can_create(can_create_data))
        except Exception as e:
            logger.error(f"Error checking creation capability: {e}")
            Clock.schedule_once(
                lambda dt: Snackbar(text="Error verificando límites", duration=3).open()
            )

    def _check_and_navigate_to_create(self):
        """Check limits and navigate to create screen."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_check():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._check_can_create_async())

        with ThreadPoolExecutor() as executor:
            executor.submit(run_check)

    def _navigate_if_can_create(self, can_create_data: Dict[str, Any]):
        """Navigate to create screen if user can create keys."""
        can_create = can_create_data.get("can_create", False)
        reason = can_create_data.get("reason")

        if not can_create:
            Snackbar(text=reason or "No puedes crear más claves", duration=3).open()
            return

        if self.manager and self.manager.has_screen("create_key"):
            self.manager.current = "create_key"

    def on_key_card_pressed(self, key_id: str):
        """Handle key card tap (navigate to detail)."""
        logger.info(f"Viewing key detail: {key_id}")

        # Store key_id for detail screen
        from kivy.app import App

        app = App.get_running_app()
        app.current_key_id = key_id

        if self.manager and self.manager.has_screen("key_detail"):
            self.manager.current = "key_detail"

    def on_back_pressed(self):
        """Handle back button press."""
        logger.info("Back to dashboard")
        if self.manager and self.manager.has_screen("dashboard"):
            self.manager.current = "dashboard"

    def show_key_options(self, key_id: str, key_name: str):
        """
        Show options for a key (rename, delete).

        Args:
            key_id: UUID of the key
            key_name: Current name of the key
        """
        if not self.dialog:
            self.dialog = MDDialog(
                title="Opciones de Clave",
                text=f"¿Qué deseas hacer con '{key_name}'?",
                buttons=[
                    MDFlatButton(
                        text="RENOMBRAR",
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=lambda x: self._show_rename_dialog(key_id, key_name),
                    ),
                    MDFlatButton(
                        text="ELIMINAR",
                        theme_text_color="Custom",
                        text_color=[1, 0.267, 0.267, 1],
                        on_release=lambda x: self._confirm_delete_key(key_id, key_name),
                    ),
                    MDFlatButton(
                        text="CANCELAR",
                        theme_text_color="Custom",
                        text_color=[0.878, 0.878, 0.878, 1],
                        on_release=self.dismiss_dialog,
                    ),
                ],
            )
        self.dialog.open()

    def _show_rename_dialog(self, key_id: str, current_name: str):
        """Show rename dialog."""
        self.dismiss_dialog(None)

        from kivymd.uix.textfield import MDTextField

        if not self.dialog:
            text_field = MDTextField(
                text=current_name,
                hint_text="Nombre de la clave",
                helper_text="Máximo 30 caracteres",
                helper_text_mode="on_error",
                max_length=30,
                size_hint_x=None,
                width=dp(300),
                pos_hint={"center_x": 0.5},
            )

            self.dialog = MDDialog(
                title="Renombrar Clave",
                type="custom",
                content_cls=text_field,
                buttons=[
                    MDFlatButton(
                        text="CANCELAR",
                        theme_text_color="Custom",
                        text_color=[0.878, 0.878, 0.878, 1],
                        on_release=self.dismiss_dialog,
                    ),
                    MDFlatButton(
                        text="GUARDAR",
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=lambda x: self._rename_key(key_id, text_field.text),
                    ),
                ],
            )
        self.dialog.open()

    def _rename_key(self, key_id: str, new_name: str):
        """Rename key."""
        self.dismiss_dialog(None)

        if not new_name or len(new_name.strip()) == 0:
            Snackbar(text="El nombre no puede estar vacío", duration=2).open()
            return

        new_name = new_name.strip()[:30]

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_rename():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._rename_key_async(key_id, new_name))

        with ThreadPoolExecutor() as executor:
            executor.submit(run_rename)

    async def _rename_key_async(self, key_id: str, new_name: str):
        """Rename key asynchronously."""
        try:
            await self.keys_service.rename_key(key_id, new_name)
            Clock.schedule_once(lambda dt: Snackbar(text="Nombre actualizado", duration=2).open())
            # Refresh list
            Clock.schedule_once(lambda dt: self.load_keys(force_refresh=True), 0.5)
        except Exception as err:
            logger.error(f"Error renaming key: {err}")
            error_msg = str(err)
            Clock.schedule_once(
                lambda dt, msg=error_msg: Snackbar(text=f"Error: {msg}", duration=3).open()
            )

    def _confirm_delete_key(self, key_id: str, key_name: str):
        """Confirm key deletion."""
        self.dismiss_dialog(None)

        if not self.dialog:
            self.dialog = MDDialog(
                title="⚠️ Eliminar Clave",
                text=f"¿Estás seguro que deseas eliminar '{key_name}'?\n\nEsta acción es irreversible. La clave dejará de funcionar inmediatamente.",
                buttons=[
                    MDFlatButton(
                        text="CANCELAR",
                        theme_text_color="Custom",
                        text_color=[0.878, 0.878, 0.878, 1],
                        on_release=self.dismiss_dialog,
                    ),
                    MDFlatButton(
                        text="ELIMINAR",
                        theme_text_color="Custom",
                        text_color=[1, 0.267, 0.267, 1],
                        on_release=lambda x: self._delete_key(key_id),
                    ),
                ],
            )
        self.dialog.open()

    def _delete_key(self, key_id: str):
        """Delete key."""
        self.dismiss_dialog(None)

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_delete():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._delete_key_async(key_id))

        with ThreadPoolExecutor() as executor:
            executor.submit(run_delete)

    async def _delete_key_async(self, key_id: str):
        """Delete key asynchronously."""
        try:
            await self.keys_service.delete_key(key_id)
            Clock.schedule_once(lambda dt: Snackbar(text="Clave eliminada", duration=2).open())
            # Refresh list
            Clock.schedule_once(lambda dt: self.load_keys(force_refresh=True), 0.5)
        except Exception as e:
            logger.error(f"Error deleting key: {e}")
            error_msg = str(e)
            # Check for credits-related errors (in Spanish or English)
            if "créditos" in error_msg.lower() or "credit" in error_msg.lower():
                error_msg = "Necesitas créditos de referido para eliminar claves. Invita amigos."
            Clock.schedule_once(lambda dt: Snackbar(text=error_msg, duration=4).open())

    def dismiss_dialog(self, instance):
        """Dismiss dialog."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
