"""
Status badge component for uSipipo VPN Android APK.
Small badge showing status with icon and color.
"""

from kivy.properties import ListProperty, StringProperty
from kivymd.uix.card import MDCard


class StatusBadge(MDCard):
    """
    Reusable status badge component.

    Features:
    - Icon + text badge
    - Color-coded by status type
    - Compact design for inline use
    - Cyberpunk styling
    """

    # Status properties
    status_text = StringProperty("Activo")
    status_icon = StringProperty("check-circle")
    status_color = ListProperty([0, 1, 0.255, 1])  # terminal_green

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_status(self, status_type: str):
        """
        Set status type and automatically configure icon and color.

        Args:
            status_type: One of 'active', 'inactive', 'suspended', 'pending', 'error'
        """
        status_config = {
            "active": {
                "text": "Activo",
                "icon": "check-circle",
                "color": [0, 1, 0.255, 1],  # terminal_green
            },
            "inactive": {
                "text": "Inactivo",
                "icon": "circle-outline",
                "color": [0.541, 0.541, 0.604, 1],  # text_secondary
            },
            "suspended": {
                "text": "Suspendido",
                "icon": "lock-outline",
                "color": [1, 0.267, 0.267, 1],  # red
            },
            "pending": {
                "text": "Pendiente",
                "icon": "clock-outline",
                "color": [1, 0.584, 0, 1],  # amber
            },
            "error": {
                "text": "Error",
                "icon": "alert-circle",
                "color": [1, 0.267, 0.267, 1],  # red
            },
            "online": {"text": "En línea", "icon": "wifi", "color": [0, 0.941, 1, 1]},  # neon_cyan
            "offline": {
                "text": "Sin conexión",
                "icon": "wifi-off",
                "color": [0.541, 0.541, 0.604, 1],  # text_secondary
            },
        }

        config = status_config.get(status_type, status_config["inactive"])
        self.status_text = config["text"]
        self.status_icon = config["icon"]
        self.status_color = config["color"]
