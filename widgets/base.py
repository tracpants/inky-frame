"""
Base widget class for the Inky Frame widget system.
All widgets should inherit from BaseWidget.
"""

from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Tuple, Optional
import os

# TrueType fonts to try, in order. INKY_FONT overrides them all.
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
]


class BaseWidget(ABC):
    """Base class for all display widgets."""
    
    # Widget type identifier - must be overridden by subclasses
    widget_type = None
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize widget with configuration.
        
        Args:
            config: Widget configuration dictionary containing:
                - enabled: bool - whether widget is active
                - position: dict with x, y coordinates (0-100 as percentage)
                - orientation: str - 'landscape' or 'portrait'
                - style: dict with styling options (font_size, color, etc.)
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.position = config.get('position', {'x': 10, 'y': 10})  # Default top-left
        self.orientation = config.get('orientation', 'landscape')
        self.style = config.get('style', {})
    
    @abstractmethod
    def render(self, display_width: int, display_height: int) -> Optional[Image.Image]:
        """
        Render the widget content.
        
        Args:
            display_width: Width of the display in pixels
            display_height: Height of the display in pixels
            
        Returns:
            PIL Image with the widget content, or None if widget should not be displayed
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for this widget type.
        
        Returns:
            Dictionary with default configuration values
        """
        pass
    
    def get_position_pixels(self, display_width: int, display_height: int) -> Tuple[int, int]:
        """
        Convert percentage position to pixel coordinates.
        
        Args:
            display_width: Width of the display in pixels
            display_height: Height of the display in pixels
            
        Returns:
            Tuple of (x, y) pixel coordinates
        """
        x_percent = self.position.get('x', 10)
        y_percent = self.position.get('y', 10)
        
        x_pixel = int((x_percent / 100.0) * display_width)
        y_pixel = int((y_percent / 100.0) * display_height)
        
        return x_pixel, y_pixel
    
    def load_font(self, size: int = 20) -> ImageFont.ImageFont:
        """
        Load a font for text rendering at the requested pixel size.
        
        Tries INKY_FONT, then common system TrueType fonts, and finally
        Pillow's built-in font scaled to the requested size, so the widget
        is readable on the panel regardless of which fonts are installed.
        
        Args:
            size: Font size in pixels
            
        Returns:
            PIL ImageFont object
        """
        candidates = [os.environ.get('INKY_FONT')] + FONT_CANDIDATES
        for path in candidates:
            if not path:
                continue
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
        try:
            return ImageFont.load_default(size)  # Pillow >= 10.1 scales it
        except TypeError:
            return ImageFont.load_default()
    
    def create_text_background(self, text: str, font: ImageFont.ImageFont, 
                             padding: int = 10, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 128)) -> Image.Image:
        """
        Create a background for text with padding.
        
        Args:
            text: Text to measure
            font: Font to use for measurement
            padding: Padding around text in pixels
            bg_color: Background color as RGBA tuple
            
        Returns:
            PIL Image with background
        """
        # Measure text size
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create background image
        bg_width = text_width + (padding * 2)
        bg_height = text_height + (padding * 2)
        
        background = Image.new('RGBA', (bg_width, bg_height), bg_color)
        return background
    
    @classmethod
    def normalize_config(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalise a configuration submitted via the API.
        
        Subclasses should override this to check their own options.
        Raises ValueError with a user-readable message on invalid input.
        """
        position = data.get('position', {})
        style = data.get('style', {})
        if not isinstance(position, dict) or not isinstance(style, dict):
            raise ValueError('position and style must be objects')
        return {
            'enabled': bool(data.get('enabled', False)),
            'position': position,
            'style': style,
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update widget configuration.
        
        Args:
            new_config: New configuration values to merge
        """
        self.config.update(new_config)
        self.enabled = self.config.get('enabled', True)
        self.position = self.config.get('position', {'x': 10, 'y': 10})
        self.orientation = self.config.get('orientation', 'landscape')
        self.style = self.config.get('style', {})