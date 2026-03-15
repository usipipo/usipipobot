"""
Create VPN Key screen for uSipipo VPN Android APK.
Guides user through 3-step wizard to create a new VPN key.
"""

from typing import Any, Dict, Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from loguru import logger
from src.services.auth_service import AuthService
from src.services.keys_service import KeysService


class CreateKeyScreen(MDScreen):
    """
    Screen for creating a new VPN key with 3-step wizard.

    Step 1: Select protocol (Outline or WireGuard)
    Step 2: Name the key (with suggestions)
    Step 3: Confirmation and creation

    Features:
    - Protocol selection with descriptions
    - Inline validation for existing key types
    - Name suggestions with chips
    - Character counter
    - Confirmation summary
    - Success screen navigation
    """

    # Step properties
    current_step = NumericProperty(1)
    total_steps = NumericProperty(3)

    # Step 1: Protocol selection
    selected_protocol = StringProperty("")
    can_create_outline = BooleanProperty(True)
    can_create_wireguard = BooleanProperty(True)
    outline_blocked_reason = StringProperty("")
    wireguard_blocked_reason = StringProperty("")

    # Step 2: Key naming
    key_name = StringProperty("")
    name_suggestions = ListProperty(
        ["Mi iPhone", "Mi PC", "Mi tablet", "Trabajo", "Casa", "Viajes"]
    )
    char_count = NumericProperty(0)
    max_chars = NumericProperty(30)
    has_name_error = BooleanProperty(False)
    name_error_message = StringProperty("")

    # Step 3: Confirmation
    confirmation_server = StringProperty("")

    # Status
    is_loading = BooleanProperty(False)
    is_offline = BooleanProperty(False)
    has_error = BooleanProperty(False)
    error_message = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.keys_service: Optional[KeysService] = None
        self.dialog = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Create key screen entered")
        self._reset_form()
        self._check_creation_capability()

    def on_leave(self):
        """Called when screen is left."""
        pass

    def _reset_form(self):
        """Reset form to initial state."""
        self.current_step = 1
        self.selected_protocol = ""
        self.key_name = ""
        self.char_count = 0
        self.has_name_error = False
        self.name_error_message = ""
        self.is_loading = False
        self.has_error = False
        logger.debug("Create key form reset")

    def _check_creation_capability(self):
        """Check if user can create keys and which types."""
        self.keys_service = KeysService()

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_check():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._check_capability_async())

        with ThreadPoolExecutor() as executor:
            executor.submit(run_check)

    async def _check_capability_async(self):
        """Check capability asynchronously."""
        try:
            result = await self.keys_service.can_create_key()
            Clock.schedule_once(lambda dt: self._update_capability(result))
        except Exception as e:
            logger.error(f"Error checking capability: {e}")
            Clock.schedule_once(
                lambda dt: Snackbar(text="Error verificando límites", duration=3).open()
            )

    def _update_capability(self, result: Dict[str, Any]):
        """Update UI with capability data."""
        self.can_create_outline = result.get("can_create_outline", True)
        self.can_create_wireguard = result.get("can_create_wireguard", True)

        if not self.can_create_outline:
            self.outline_blocked_reason = "Ya tienes una clave Outline activa"
        if not self.can_create_wireguard:
            self.wireguard_blocked_reason = "Ya tienes una clave WireGuard activa"

        # If both blocked, show error and go back
        if not self.can_create_outline and not self.can_create_wireguard:
            self._show_limit_reached_dialog()

        logger.debug(
            f"Creation capability: outline={self.can_create_outline}, "
            f"wireguard={self.can_create_wireguard}"
        )

    def _show_limit_reached_dialog(self):
        """Show dialog when user reached key limit."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="⚠️ Límite Alcanzado",
                text="Tienes 2/2 claves activas.\n\nElimina una clave existente para crear una nueva.",
                buttons=[
                    MDFlatButton(
                        text="IR A CLAVES",
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=lambda x: self._navigate_to_keys_list(),
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

    def _navigate_to_keys_list(self):
        """Navigate to keys list screen."""
        self.dismiss_dialog(None)
        if self.manager and self.manager.has_screen("keys_list"):
            self.manager.current = "keys_list"

    def on_protocol_selected(self, protocol: str):
        """Handle protocol selection."""
        if protocol == "outline" and not self.can_create_outline:
            return
        if protocol == "wireguard" and not self.can_create_wireguard:
            return

        self.selected_protocol = protocol
        logger.debug(f"Protocol selected: {protocol}")

        # Auto-advance to step 2 after short delay
        Clock.schedule_once(lambda dt: self.go_to_step(2), 0.3)

    def go_to_step(self, step: int):
        """Navigate to specific step."""
        if step < 1 or step > self.total_steps:
            return

        # Validation when moving forward
        if step > self.current_step:
            if self.current_step == 1 and not self.selected_protocol:
                Snackbar(text="Selecciona un protocolo", duration=2).open()
                return
            elif self.current_step == 2:
                if not self._validate_key_name():
                    return

        self.current_step = step

        # Update confirmation data on step 3
        if step == 3:
            self.confirmation_server = (
                "Outline Server" if self.selected_protocol == "outline" else "WireGuard Server"
            )

        logger.debug(f"Navigated to step {step}")

    def on_back_pressed(self):
        """Handle back button."""
        if self.current_step > 1:
            self.go_to_step(self.current_step - 1)
        else:
            self._navigate_to_keys_list()

    def on_next_pressed(self):
        """Handle next button."""
        self.go_to_step(self.current_step + 1)

    def on_create_key_pressed(self):
        """Handle create key button on step 3."""
        if not self._validate_key_name():
            return

        self._create_key()

    def _validate_key_name(self) -> bool:
        """Validate key name."""
        name = self.key_name.strip()

        if not name:
            self.has_name_error = True
            self.name_error_message = "El nombre no puede estar vacío"
            Snackbar(text=self.name_error_message, duration=2).open()
            return False

        if len(name) < 2:
            self.has_name_error = True
            self.name_error_message = "El nombre debe tener al menos 2 caracteres"
            Snackbar(text=self.name_error_message, duration=2).open()
            return False

        if len(name) > 30:
            self.has_name_error = True
            self.name_error_message = "El nombre no puede exceder 30 caracteres"
            Snackbar(text=self.name_error_message, duration=2).open()
            return False

        self.has_name_error = False
        self.name_error_message = ""
        return True

    def on_name_text(self, text: str):
        """Handle name text change."""
        self.key_name = text
        self.char_count = len(text)
        self.has_name_error = False

    def on_suggestion_pressed(self, suggestion: str):
        """Handle suggestion chip press."""
        self.key_name = suggestion
        self.char_count = len(suggestion)
        self.has_name_error = False
        logger.debug(f"Suggestion selected: {suggestion}")

    def _create_key(self):
        """Create the VPN key."""
        self.is_loading = True

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_create():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._create_key_async())

        with ThreadPoolExecutor() as executor:
            executor.submit(run_create)

    async def _create_key_async(self):
        """Create key asynchronously."""
        try:
            result = await self.keys_service.create_key(
                key_type=self.selected_protocol, name=self.key_name.strip()
            )
            Clock.schedule_once(lambda dt, r=result: self._on_key_created(r))
        except Exception as e:
            logger.error(f"Error creating key: {e}")
            error_msg = str(e)
            Clock.schedule_once(lambda dt, msg=error_msg: self._on_create_error(msg))

    def _on_key_created(self, result: Dict[str, Any]):
        """Handle successful key creation."""
        self.is_loading = False

        # Store key data for success screen
        from kivy.app import App

        app = App.get_running_app()
        app.current_key_data = result

        logger.info(f"Key created successfully: {result.get('id')}")

        # Navigate to success screen
        if self.manager and self.manager.has_screen("create_key_success"):
            self.manager.current = "create_key_success"

    def _on_create_error(self, error_msg: str):
        """Handle key creation error."""
        self.is_loading = False
        self.has_error = True
        self.error_message = error_msg

        # Check for specific errors
        if "Ya tienes una clave" in error_msg:
            error_msg = "Ya tienes una clave de este tipo. Elimínala para crear otra."
        elif "Sin datos disponibles" in error_msg:
            error_msg = "No tienes datos disponibles. Compra más GB."

        Snackbar(text=error_msg, duration=4).open()
        logger.error(f"Key creation error: {error_msg}")

    def dismiss_dialog(self, instance):
        """Dismiss dialog."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
