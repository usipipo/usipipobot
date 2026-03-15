"""
Key detail screen for uSipipo VPN Android APK.
Shows detailed information about a specific VPN key.
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
from src.components.qr_display import QrDisplay
from src.services.auth_service import AuthService
from src.services.keys_service import KeysService, VpnKeyData


class KeyDetailScreen(MDScreen):
    """
    Screen for displaying detailed VPN key information.

    Features:
    - Key status and type indicator
    - Data usage with progress bar
    - QR code for connection
    - Connection string (copy to clipboard)
    - Share functionality
    - Technical information
    - Connection instructions
    - Rename and delete options
    """

    # Key properties
    key_name = StringProperty("Cargando...")
    key_type = StringProperty("outline")
    key_type_display = StringProperty("Outline VPN")
    server = StringProperty("Outline Server")
    is_active = BooleanProperty(True)
    status_color = ListProperty([0, 1, 0.255, 1])  # terminal_green

    # Usage properties
    used_bytes = NumericProperty(0)
    data_limit_bytes = NumericProperty(0)
    used_display = StringProperty("0 GB")
    limit_display = StringProperty("5 GB")
    remaining_display = StringProperty("5 GB")
    usage_percentage = NumericProperty(0.0)
    progress_color = ListProperty([0, 0.941, 1, 1])  # neon_cyan

    # Dates
    created_at = StringProperty("")
    expires_at = StringProperty("")
    billing_reset_at = StringProperty("")
    last_seen_at = StringProperty("")

    # Connection
    key_data = StringProperty("")
    qr_data = StringProperty("")
    external_id = StringProperty("")

    # Status
    is_loading = BooleanProperty(True)
    is_offline = BooleanProperty(False)
    has_error = BooleanProperty(False)
    error_message = StringProperty("")

    # Warning banners
    show_purchase_banner = BooleanProperty(False)
    show_limit_reached_overlay = BooleanProperty(False)

    # Key ID
    _key_id = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.keys_service: Optional[KeysService] = None
        self.dialog = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Key detail screen entered")
        self.load_key_detail()

    def on_leave(self):
        """Called when screen is left."""
        pass

    def load_key_detail(self):
        """Load key detail from API."""
        self.is_loading = True
        self.has_error = False

        # Get key_id from app
        from kivy.app import App

        app = App.get_running_app()
        self._key_id = getattr(app, "current_key_id", None)

        if not self._key_id:
            logger.error("No key_id provided")
            self.has_error = True
            self.error_message = "No se especificó la clave"
            self.is_loading = False
            return

        # Get current user
        telegram_id = self.auth_service.get_current_user()
        if not telegram_id:
            logger.warning("No authenticated user, redirecting to login")
            Clock.schedule_once(lambda dt: self._redirect_to_login(), 0.5)
            return

        self.keys_service = KeysService()

        # Load data asynchronously
        Clock.schedule_once(lambda dt: self._fetch_key_detail(), 0)

    def _redirect_to_login(self):
        """Redirect to login screen."""
        if self.manager:
            self.manager.current = "login"

    async def _fetch_key_detail_async(self):
        """Fetch key detail asynchronously."""
        try:
            key_data = await self.keys_service.get_key_detail(self._key_id)
            Clock.schedule_once(lambda dt: self._update_detail(key_data))
        except Exception as err:
            logger.error(f"Error fetching key detail: {err}")
            Clock.schedule_once(lambda dt, e=err: self._handle_load_error(e))

    def _fetch_key_detail(self):
        """Fetch key detail (async wrapper)."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._fetch_key_detail_async())

        with ThreadPoolExecutor() as executor:
            executor.submit(run_async)

    def _update_detail(self, key: VpnKeyData):
        """
        Update UI with key data.

        Args:
            key: VpnKeyData object
        """
        try:
            # Basic info
            self.key_name = key.name
            self.key_type = key.key_type
            self.key_type_display = "Outline VPN" if key.key_type == "outline" else "WireGuard"
            self.server = key.server
            self.is_active = key.is_active
            self.status_color = [0, 1, 0.255, 1] if key.is_active else [0.541, 0.541, 0.604, 1]

            # Usage
            self.used_bytes = key.used_bytes
            self.data_limit_bytes = key.data_limit_bytes
            self.used_display = self.keys_service.format_bytes(key.used_bytes)
            self.limit_display = self.keys_service.format_bytes(key.data_limit_bytes)
            self.remaining_display = self.keys_service.format_bytes(key.remaining_bytes)
            self.usage_percentage = key.usage_percentage
            self.progress_color = self._get_progress_color(key.usage_percentage)

            # Dates
            self.created_at = self._format_date(key.created_at)
            self.expires_at = self._format_date(key.expires_at) or "Sin vencimiento"
            self.billing_reset_at = self._format_date(key.billing_reset_at)
            self.last_seen_at = self._format_date(key.last_seen_at) or "Nunca"

            # Connection
            self.key_data = key.key_data
            self.qr_data = key.key_data
            self.external_id = key.external_id or ""

            # Configure QR display
            qr_display = self.ids.get("qr_display")
            if qr_display:
                qr_display.qr_data = key.key_data

            self.is_loading = False
            logger.debug(f"Key detail loaded: {key.name}")

        except Exception as e:
            logger.error(f"Error updating detail: {e}")
            self._handle_load_error(e)

    def _handle_load_error(self, error: Exception):
        """Handle load error."""
        self.is_loading = False
        self.has_error = True
        self.error_message = str(error)
        logger.error(f"Key detail load error: {error}")

        Snackbar(text="Error cargando información de la clave", duration=3).open()

    def _get_progress_color(self, percentage: float) -> List[float]:
        """Get progress bar color based on percentage."""
        # Update banner visibility based on percentage
        if percentage >= 100:
            self.show_limit_reached_overlay = True
            self.show_purchase_banner = False
            return [1, 0.267, 0.267, 1]  # error (red)
        elif percentage >= 85:
            self.show_limit_reached_overlay = False
            self.show_purchase_banner = True
            return [1, 0.267, 0.267, 1]  # error (red)
        elif percentage >= 60:
            self.show_limit_reached_overlay = False
            self.show_purchase_banner = True
            return [1, 0.584, 0, 1]  # amber
        else:
            self.show_limit_reached_overlay = False
            self.show_purchase_banner = False
            return [0, 0.941, 1, 1]  # neon_cyan

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date string for display."""
        if not date_str:
            return ""

        try:
            from datetime import datetime

            # Parse ISO format
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y")
        except Exception:
            return date_str

    def on_back_pressed(self):
        """Handle back button press."""
        logger.info("Back to keys list")
        if self.manager and self.manager.has_screen("keys_list"):
            self.manager.current = "keys_list"

    def on_buy_more_pressed(self):
        """Handle buy more GB button press from banner."""
        logger.info("Navigate to buy more GB")
        if self.manager and self.manager.has_screen("purchase"):
            self.manager.current = "purchase"

    def on_copy_code_pressed(self):
        """Handle copy connection string button press."""
        logger.info("Copying connection string to clipboard")

        if not self.key_data:
            Snackbar(text="No hay código para copiar", duration=2).open()
            return

        # Copy to clipboard
        from kivy.core.clipboard import Clipboard

        Clipboard.copy(self.key_data)

        Snackbar(text="✅ Código copiado al portapapeles", duration=3).open()

        # Haptic feedback
        self._haptic_feedback()

    def _haptic_feedback(self):
        """Provide haptic feedback (vibration)."""
        try:
            from jnius import autoclass

            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            vibrator = activity.getSystemService(activity.VIBRATOR_SERVICE)
            vibrator.vibrate(50)  # 50ms vibration
            logger.debug("Haptic feedback triggered (50ms)")
        except Exception as e:
            logger.debug(f"Haptic feedback not available: {e}")  # Desktop or error: skip haptic

    def on_share_pressed(self):
        """Handle share button press."""
        logger.info("Showing share options")
        self._show_share_sheet()

    def _show_share_sheet(self):
        """Show share options dialog."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Compartir Clave",
                text="¿Cómo deseas compartir?",
                buttons=[
                    MDFlatButton(
                        text="Como texto",
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=lambda x: self._share_as_text(),
                    ),
                    MDFlatButton(
                        text="QR como imagen",
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=lambda x: self._share_qr_image(),
                    ),
                    MDFlatButton(
                        text="Cancelar",
                        theme_text_color="Custom",
                        text_color=[0.878, 0.878, 0.878, 1],
                        on_release=self.dismiss_dialog,
                    ),
                ],
            )
        self.dialog.open()

    def _share_as_text(self):
        """Share connection string as text."""
        self.dismiss_dialog(None)

        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            activity = autoclass("org.kivy.android.PythonActivity").mActivity

            intent = Intent(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_SUBJECT, f"Clave VPN - {self.key_name}")
            intent.putExtra(
                Intent.EXTRA_TEXT,
                f"🔑 {self.key_name}\n\n{self.key_data}\n\nCompartido desde uSipipo VPN",
            )

            activity.startActivity(Intent.createChooser(intent, "Compartir"))
            logger.info("Share intent launched")
        except Exception as e:
            logger.error(f"Error sharing: {e}")
            Snackbar(text="Error al compartir", duration=2).open()

    def _share_qr_image(self):
        """Share QR code as image."""
        self.dismiss_dialog(None)

        # For now, share as text
        # Full implementation would generate QR image and share
        Snackbar(text="Compartiendo como texto...", duration=2).open()
        self._share_as_text()

    def on_menu_pressed(self):
        """Handle menu button press (⋮)."""
        logger.info("Showing key options menu")
        self._show_options_menu()

    def _show_options_menu(self):
        """Show options menu (rename, delete)."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Opciones",
                text=f"¿Qué deseas hacer con '{self.key_name}'?",
                buttons=[
                    MDFlatButton(
                        text="RENOMBRAR",
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=lambda x: self._show_rename_dialog(),
                    ),
                    MDFlatButton(
                        text="ELIMINAR",
                        theme_text_color="Custom",
                        text_color=[1, 0.267, 0.267, 1],
                        on_release=lambda x: self._confirm_delete(),
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

    def _show_rename_dialog(self):
        """Show rename dialog."""
        self.dismiss_dialog(None)

        from kivymd.uix.textfield import MDTextField

        if not self.dialog:
            text_field = MDTextField(
                text=self.key_name,
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
                        on_release=lambda x: self._rename_key(text_field.text),
                    ),
                ],
            )
        self.dialog.open()

    def _rename_key(self, new_name: str):
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
            return loop.run_until_complete(self._rename_key_async(new_name))

        with ThreadPoolExecutor() as executor:
            executor.submit(run_rename)

    async def _rename_key_async(self, new_name: str):
        """Rename key asynchronously."""
        try:
            await self.keys_service.rename_key(self._key_id, new_name)
            Clock.schedule_once(lambda dt: Snackbar(text="Nombre actualizado", duration=2).open())
            # Update UI
            self.key_name = new_name
        except Exception as err:
            logger.error(f"Error renaming key: {err}")
            error_msg = str(err)
            Clock.schedule_once(
                lambda dt, msg=error_msg: Snackbar(text=f"Error: {msg}", duration=3).open()
            )

    def _confirm_delete(self):
        """Confirm key deletion."""
        self.dismiss_dialog(None)

        if not self.dialog:
            self.dialog = MDDialog(
                title="⚠️ Eliminar Clave",
                text=f"¿Estás seguro que deseas eliminar '{self.key_name}'?\n\nEsta acción es irreversible. La clave dejará de funcionar inmediatamente.",
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
                        on_release=lambda x: self._delete_key(),
                    ),
                ],
            )
        self.dialog.open()

    def _delete_key(self):
        """Delete key."""
        self.dismiss_dialog(None)

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_delete():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._delete_key_async())

        with ThreadPoolExecutor() as executor:
            executor.submit(run_delete)

    async def _delete_key_async(self):
        """Delete key asynchronously."""
        try:
            await self.keys_service.delete_key(self._key_id)
            Clock.schedule_once(lambda dt: Snackbar(text="Clave eliminada", duration=2).open())
            # Navigate back to list
            Clock.schedule_once(lambda dt: self.on_back_pressed(), 0.5)
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
