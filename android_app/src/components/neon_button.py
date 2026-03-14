"""
Neon Button component with cyberpunk styling.
"""
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.behaviors import RectangularRippleBehavior

from src.config import COLORS


class NeonButtonBehavior(RectangularRippleBehavior):
    """Behavior for neon glow effect on buttons."""
    
    neon_color = ListProperty(COLORS["neon_cyan"])


class NeonButton(NeonButtonBehavior, MDRaisedButton):
    """
    Custom button with neon glow effect for cyberpunk theme.
    
    Usage:
        NeonButton(
            text="CLICK ME",
            neon_color=[0, 0.941, 1, 1],  # Cyan
            on_release=self.callback
        )
    """
    
    text = StringProperty("")
    neon_color = ListProperty(COLORS["neon_cyan"])
    disabled = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default styling
        self.md_bg_color = self.neon_color
        self.theme_text_color = "Custom"
        self.text_color = COLORS["bg_void"]
        self.font_size = dp(16)
        self.height = dp(48)
        self.size_hint_x = 1
        self.rounded_button = True
    
    def on_neon_color(self, instance, value):
        """Update button color when neon_color changes."""
        self.md_bg_color = value
        # Ripple color should match
        self.ripple_color = value
