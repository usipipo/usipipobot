"""
Quick action button component for uSipipo VPN Android APK.
Square button with icon and text for quick actions.
"""
from kivy.properties import StringProperty, ListProperty
from kivymd.uix.card import MDCard
from kivymd.uix.ripplebehavior import CommonRippleBehavior


class QuickActionButton(CommonRippleBehavior, MDCard):
    """
    Reusable quick action button component.
    
    Features:
    - Icon + text label
    - Customizable colors
    - Ripple effect on touch
    - Cyberpunk styling
    - Compact square design
    """

    # Button properties
    button_text = StringProperty("Acción")
    button_icon = StringProperty("star")
    icon_color = ListProperty([0, 0.941, 1, 1])  # neon_cyan

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.102, 0.102, 0.141, 1]  # bg_card

    def set_action(self, action_type: str):
        """
        Set action type and automatically configure icon and color.
        
        Args:
            action_type: One of 'new_key', 'buy_gb', 'support', 'refresh', 'settings'
        """
        action_config = {
            'new_key': {
                'text': 'Nueva Clave',
                'icon': 'key-plus',
                'color': [0, 0.941, 1, 1]  # neon_cyan
            },
            'buy_gb': {
                'text': 'Comprar GB',
                'icon': 'database-plus',
                'color': [0, 1, 0.255, 1]  # terminal_green
            },
            'support': {
                'text': 'Soporte',
                'icon': 'headset',
                'color': [1, 0, 0.667, 1]  # neon_magenta
            },
            'refresh': {
                'text': 'Actualizar',
                'icon': 'refresh',
                'color': [0, 0.941, 1, 1]  # neon_cyan
            },
            'settings': {
                'text': 'Ajustes',
                'icon': 'cog',
                'color': [0.878, 0.878, 0.878, 1]  # text_primary
            }
        }

        config = action_config.get(action_type, action_config['new_key'])
        self.button_text = config['text']
        self.button_icon = config['icon']
        self.icon_color = config['color']
