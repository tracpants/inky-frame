"""
Date widget for displaying current date on the Inky Frame.
Shows date in customizable format without time to minimize e-ink refreshes.
"""

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, Tuple
from .base import BaseWidget


class DateWidget(BaseWidget):
    """Widget that displays the current date."""
    
    widget_type = "date"
    
    def render(self, display_width: int, display_height: int) -> Optional[Image.Image]:
        """
        Render the date widget.
        
        Args:
            display_width: Width of the display in pixels
            display_height: Height of the display in pixels
            
        Returns:
            PIL Image with the date overlay, or None if disabled
        """
        if not self.enabled:
            return None
        
        # Get current date
        now = datetime.now()
        
        # Format date based on style configuration
        date_format = self.style.get('format', '%A, %B %d, %Y')  # Default: "Monday, December 23, 2024"
        date_text = now.strftime(date_format)
        
        # Get styling options
        font_size = self.style.get('font_size', 24)
        text_color = tuple(self.style.get('text_color', [255, 255, 255]))  # White
        bg_color = tuple(self.style.get('bg_color', [0, 0, 0, 180]))  # Semi-transparent black
        bg_enabled = self.style.get('background', True)
        padding = self.style.get('padding', 12)
        
        # Load font
        font = self.load_font(font_size)
        
        # Measure text size
        bbox = font.getbbox(date_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate widget dimensions
        if bg_enabled:
            widget_width = text_width + (padding * 2)
            widget_height = text_height + (padding * 2)
        else:
            widget_width = text_width
            widget_height = text_height
            padding = 0
        
        # Create widget image with transparency
        widget_img = Image.new('RGBA', (widget_width, widget_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(widget_img)
        
        # Draw background if enabled
        if bg_enabled:
            draw.rectangle([0, 0, widget_width, widget_height], fill=bg_color)
        
        # Draw text
        text_x = padding
        text_y = padding
        draw.text((text_x, text_y), date_text, fill=text_color, font=font)
        
        return widget_img
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for the date widget.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            'enabled': True,
            'position': {
                'x': 5,   # 5% from left
                'y': 5    # 5% from top
            },
            'style': {
                'format': '%A, %B %d, %Y',  # "Monday, December 23, 2024"
                'font_size': 24,
                'text_color': [255, 255, 255],  # White
                'bg_color': [0, 0, 0, 180],     # Semi-transparent black
                'background': True,
                'padding': 12
            }
        }
    
    def get_format_options(self) -> Dict[str, str]:
        """
        Get available date format options.
        
        Returns:
            Dictionary mapping format names to format strings
        """
        return {
            'full': '%A, %B %d, %Y',           # Monday, December 23, 2024
            'short': '%b %d, %Y',              # Dec 23, 2024
            'numeric': '%m/%d/%Y',             # 12/23/2024
            'iso': '%Y-%m-%d',                 # 2024-12-23
            'day_only': '%A',                  # Monday
            'date_only': '%B %d',              # December 23
            'month_year': '%B %Y'              # December 2024
        }
    
    def get_color_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Get color preset options.
        
        Returns:
            Dictionary mapping preset names to color configurations
        """
        return {
            'classic': {
                'text_color': [255, 255, 255],
                'bg_color': [0, 0, 0, 180],
                'background': True
            },
            'white_on_black': {
                'text_color': [255, 255, 255],
                'bg_color': [0, 0, 0, 255],
                'background': True
            },
            'black_on_white': {
                'text_color': [0, 0, 0],
                'bg_color': [255, 255, 255, 200],
                'background': True
            },
            'transparent': {
                'text_color': [255, 255, 255],
                'bg_color': [0, 0, 0, 0],
                'background': False
            },
            'red_accent': {
                'text_color': [255, 255, 255],
                'bg_color': [200, 50, 50, 180],
                'background': True
            }
        }