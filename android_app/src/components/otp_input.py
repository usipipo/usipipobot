"""
OTP Input component for entering 6-digit verification codes.
"""
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.textfield import MDTextField
from loguru import logger

from src.config import OTP_LENGTH


class OtpInput(BoxLayout):
    """
    Custom widget for OTP input with multiple single-digit fields.
    
    Events:
        on_otp_complete: Fired when all digits are entered
    """
    
    otp = StringProperty("")
    length = NumericProperty(OTP_LENGTH)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = "10dp"
        self.padding = "10dp"
        self.text_fields = []
        self._build_inputs()
    
    def _build_inputs(self):
        """Build individual OTP input fields."""
        for i in range(self.length):
            tf = MDTextField(
                mode="rectangle",
                max_text_length=1,
                halign="center",
                font_size="24sp",
                size_hint_x=None,
                width="50dp",
                input_filter="int",
                multiline=False,
            )
            tf.bind(text=lambda instance, value, idx=i: self._on_text_change(instance, value, idx))
            tf.bind(on_text_validate=lambda instance, idx=i: self._focus_next(idx))
            self.text_fields.append(tf)
            self.add_widget(tf)
        
        # Focus first field
        if self.text_fields:
            self.text_fields[0].focus = True
    
    def _on_text_change(self, instance, value, index):
        """Handle text change in OTP field."""
        if len(value) > 1:
            # Limit to 1 character
            instance.text = value[-1]
            value = instance.text
        
        # Update OTP property
        self._update_otp()
        
        # Auto-focus next field if value entered
        if value and index < self.length - 1:
            self.text_fields[index + 1].focus = True
        elif value and index == self.length - 1:
            # All digits entered
            logger.debug(f"OTP complete: {self.otp}")
            self.dispatch("on_otp_complete", self.otp)
    
    def _focus_next(self, index):
        """Focus next field on Enter key."""
        if index < self.length - 1:
            self.text_fields[index + 1].focus = True
    
    def _update_otp(self):
        """Update the OTP string from all fields."""
        self.otp = "".join([tf.text for tf in self.text_fields])
    
    def clear(self):
        """Clear all OTP fields."""
        for tf in self.text_fields:
            tf.text = ""
        self.otp = ""
        if self.text_fields:
            self.text_fields[0].focus = True
    
    def on_otp_complete(self, otp):
        """
        Event fired when OTP is complete.
        Override this method or bind to the event.
        """
        logger.info(f"OTP entered: {otp}")
    
    def focus_first(self):
        """Focus the first OTP field."""
        if self.text_fields:
            self.text_fields[0].focus = True
