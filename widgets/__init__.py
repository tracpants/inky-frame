"""
Widget system for Inky Frame display overlays.
Provides modular widget functionality for overlaying information on photos.
"""

from .base import BaseWidget
from .date_widget import DateWidget

# Widget registry - automatically populated by importing widget modules
WIDGET_REGISTRY = {}

def register_widget(widget_class):
    """Register a widget class in the global registry."""
    WIDGET_REGISTRY[widget_class.widget_type] = widget_class

def get_widget(widget_type):
    """Get a widget class by type."""
    return WIDGET_REGISTRY.get(widget_type)

def get_available_widgets():
    """Get list of available widget types."""
    return list(WIDGET_REGISTRY.keys())

# Register built-in widgets
register_widget(DateWidget)