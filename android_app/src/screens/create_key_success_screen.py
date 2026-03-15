"""
Create Key Success screen for uSipipo VPN Android APK.
Shows success message with QR code and connection instructions after key creation.
"""

from typing import Any, Dict, Optional

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from loguru import logger
from src.services.auth_service import AuthService


class CreateKeySuccessScreen(MDScreen):
    """
    Screen shown after successful VPN key creation.

    Features:
    - Success animation/icon
    - Key name and protocol display
    - QR code for connection
    - Connection string (truncated)
    - Copy to clipboard functionality
    - Share functionality
    - Connection instructions
    - Navigation to keys list or home
    - Exit confirmation if user hasn't copied
    """

    # Key properties
    key_name = StringProperty("Mi iPhone")
    key_type = StringProperty("outline")
    key_type_display = StringProperty("Outline VPN")
    server = StringProperty("Outline Server")

    # Connection
    key_data = StringProperty("")
    qr_data = StringProperty("")
    truncated_code = StringProperty("")

    # Status
    is_loading = BooleanProperty(True)
    is_offline = BooleanProperty(False)
    has_error = BooleanProperty(False)
    error_message = StringProperty("")

    # Copy state
    has_copied = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.dialog = None
        self._key_data_raw = ""

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Create key success screen entered")
        # Bind to keyboard to intercept back button
        Window.bind(on_keyboard=self._on_keyboard_down)
        self._load_key_data()

    def on_leave(self):
        """Called when screen is left."""
        # Unbind from keyboard
        Window.unbind(on_keyboard=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, *args):
        """
        Intercept hardware back button (Android).

        Args:
            window: Kivy window
            key: Key code (27 = ESC/back button)
        """
        if key == 27:  # ESC / Android back button
            self._confirm_exit()
            return True  # Consume the event
        return False  # Let other keys pass through

    def _load_key_data(self):
        """Load key data from app global state."""
        self.is_loading = True

        # Get key data from app
        from kivy.app import App

        app = App.get_running_app()
        key_data = getattr(app, "current_key_data", None)

        if not key_data:
            logger.error("No key data found")
            self.has_error = True
            self.error_message = "No se encontró la información de la clave"
            self.is_loading = False
            return

        # Extract data
        self.key_name = key_data.get("name", "Sin nombre")
        self.key_type = key_data.get("key_type", "outline")
        self.key_type_display = "Outline VPN" if self.key_type == "outline" else "WireGuard"
        self.server = key_data.get("server", "Server")
        self.key_data = key_data.get("key_data", "")
        self.qr_data = key_data.get("qr_data", "")
        self._key_data_raw = self.key_data

        # Truncate code for display
        if len(self.key_data) > 50:
            self.truncated_code = self.key_data[:50] + "..."
        else:
            self.truncated_code = self.key_data

        self.is_loading = False
        logger.info(f"Success screen loaded for key: {self.key_name}")

    def on_back_pressed(self):
        """Handle back button press."""
        logger.info("Back button pressed")
        self._confirm_exit()

    def _confirm_exit(self):
        """Confirm exit if user hasn't copied the code."""
        if not self.has_copied:
            if not self.dialog:
                self.dialog = MDDialog(
                    title="⚠️ ¿Salir sin copiar?",
                    text="Podrás ver tu clave en cualquier momento desde Mis Claves.\n\n¿Estás seguro que deseas salir?",
                    buttons=[
                        MDFlatButton(
                            text="SALIR",
                            theme_text_color="Custom",
                            text_color=[1, 0.267, 0.267, 1],
                            on_release=lambda x: self._navigate_to_keys_list(),
                        ),
                        MDFlatButton(
                            text="QUEDARME",
                            theme_text_color="Custom",
                            text_color=[0, 0.941, 1, 1],
                            on_release=self.dismiss_dialog,
                        ),
                    ],
                )
            self.dialog.open()
        else:
            self._navigate_to_keys_list()

    def _navigate_to_keys_list(self):
        """Navigate to keys list screen."""
        self.dismiss_dialog(None)
        if self.manager and self.manager.has_screen("keys_list"):
            self.manager.current = "keys_list"

    def on_go_home_pressed(self):
        """Handle go home button press."""
        logger.info("Navigate to dashboard")
        if not self.has_copied:
            self._confirm_exit()
        else:
            if self.manager and self.manager.has_screen("dashboard"):
                self.manager.current = "dashboard"

    def on_copy_code_pressed(self):
        """Handle copy connection string button press."""
        logger.info("Copying connection string to clipboard")

        if not self.key_data:
            Snackbar(text="No hay código para copiar", duration=2).open()
            return

        # Copy to clipboard
        from kivy.core.clipboard import Clipboard

        Clipboard.copy(self.key_data)

        self.has_copied = True
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
            logger.debug(f"Haptic feedback not available: {e}")

    def on_share_pressed(self):
        """Handle share button press."""
        logger.info("Sharing connection string")
        self._share_as_text()

    def _share_as_text(self):
        """Share connection string as text."""
        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            activity = autoclass("org.kivy.android.PythonActivity").mActivity

            intent = Intent(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_SUBJECT, f"Clave VPN - {self.key_name}")
            intent.putExtra(
                Intent.EXTRA_TEXT,
                f"🔑 {self.key_name} - {self.key_type_display}\n\n{self.key_data}\n\nCompartido desde uSipipo VPN",
            )

            activity.startActivity(Intent.createChooser(intent, "Compartir"))
            logger.info("Share intent launched")
        except Exception as e:
            logger.error(f"Error sharing: {e}")
            Snackbar(text="Error al compartir", duration=2).open()

    def dismiss_dialog(self, instance):
        """Dismiss dialog."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
