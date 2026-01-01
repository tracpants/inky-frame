"""
Simplified date widget for displaying current date on the Inky Frame.
Shows date in fixed "Wed 24 Dec" format with adaptive sizing and preset positioning.
"""

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, Tuple
from .base import BaseWidget


class DateWidget(BaseWidget):
    """Widget that displays the current date in simplified format."""
    
    widget_type = "date"
    
    # Fixed date format for consistency
    DATE_FORMAT = '%a %d %b'  # "Wed 24 Dec"
    
    # Preset position options
    POSITIONS = {
        'top_left': {'x': 5, 'y': 5},
        'top_right': {'x': 95, 'y': 5, 'align': 'right'},
        'bottom_left': {'x': 5, 'y': 90},
        'bottom_right': {'x': 95, 'y': 90, 'align': 'right'},
        'center_top': {'x': 50, 'y': 5, 'align': 'center'},
        'center_bottom': {'x': 50, 'y': 90, 'align': 'center'}
    }
    
    # Style presets
    STYLES = {
        'classic': {
            'text_color': [255, 255, 255],
            'bg_color': [0, 0, 0, 180],
            'background': True
        },
        'clean': {
            'text_color': [0, 0, 0],
            'bg_color': [255, 255, 255, 200],
            'background': True
        },
        'minimal': {
            'text_color': [255, 255, 255],
            'bg_color': [0, 0, 0, 0],
            'background': False
        }
    }
    
    def render(self, display_width: int, display_height: int) -> Optional[Image.Image]:
        """
        Render the simplified date widget.
        
        Args:
            display_width: Width of the display in pixels
            display_height: Height of the display in pixels
            
        Returns:
            PIL Image with the date overlay, or None if disabled
        """
        if not self.enabled:
            return None
        
        # Get current date in fixed format
        now = datetime.now()
        date_text = now.strftime(self.DATE_FORMAT)
        
        # Calculate adaptive font size based on display dimensions and orientation
        font_size = self._calculate_adaptive_font_size(display_width, display_height)
        
        # Get style configuration
        style_name = self.style.get('style', 'classic')
        style_config = self.STYLES.get(style_name, self.STYLES['classic'])
        
        text_color = tuple(style_config['text_color'])
        bg_color = tuple(style_config['bg_color'])
        bg_enabled = style_config['background']
        
        # Load font
        font = self.load_font(font_size)
        
        # Measure text size
        bbox = font.getbbox(date_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate padding based on font size
        padding = max(8, int(font_size * 0.3))
        
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
            # Rounded rectangle for better appearance
            draw.rounded_rectangle([0, 0, widget_width, widget_height], 
                                 radius=max(4, int(font_size * 0.15)), 
                                 fill=bg_color)
        
        # Draw text
        text_x = padding
        text_y = padding
        draw.text((text_x, text_y), date_text, fill=text_color, font=font)
        
        # Store widget dimensions for positioning calculations
        self._last_widget_width = widget_width
        self._last_widget_height = widget_height
        
        return widget_img
    
    def _calculate_adaptive_font_size(self, display_width: int, display_height: int) -> int:
        """
        Calculate optimal font size based on display dimensions and orientation.
        
        Args:
            display_width: Width of the display
            display_height: Height of the display
            
        Returns:
            Optimal font size in pixels
        """
        # Determine if we're in landscape or portrait mode
        is_landscape = display_width > display_height
        
        if is_landscape:
            # Landscape mode: base on width (typical 800x480)
            base_size = min(32, max(20, int(display_width / 25)))
        else:
            # Portrait mode: base on height (typical 480x800) 
            base_size = min(28, max(18, int(display_height / 30)))
        
        return base_size
    
    def get_position_pixels(self, display_width: int, display_height: int) -> Tuple[int, int]:
        """
        Convert preset position to pixel coordinates with alignment support.
        
        Args:
            display_width: Width of the display in pixels
            display_height: Height of the display in pixels
            
        Returns:
            Tuple of (x, y) pixel coordinates
        """
        position_name = self.position.get('preset', 'bottom_right')
        position_config = self.POSITIONS.get(position_name, self.POSITIONS['bottom_right'])
        
        # Get base position
        x_percent = position_config['x']
        y_percent = position_config['y']
        
        x_pixel = int((x_percent / 100.0) * display_width)
        y_pixel = int((y_percent / 100.0) * display_height)
        
        # Adjust for alignment if widget is already rendered
        alignment = position_config.get('align', 'left')
        if hasattr(self, '_last_widget_width'):
            if alignment == 'right':
                x_pixel -= self._last_widget_width
            elif alignment == 'center':
                x_pixel -= self._last_widget_width // 2
        
        return x_pixel, y_pixel
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get simplified default configuration for the date widget.
        
        Returns:
            Dictionary with simplified configuration
        """
        return {
            'enabled': False,
            'position': {
                'preset': 'bottom_right'  # Use preset instead of x/y coordinates
            },
            'style': {
                'style': 'classic'  # Use style preset instead of individual colors
            }
        }
    
    def get_position_presets(self) -> Dict[str, str]:
        """
        Get available position preset options.
        
        Returns:
            Dictionary mapping preset keys to display names
        """
        return {
            'top_left': 'Top Left',
            'top_right': 'Top Right',
            'bottom_left': 'Bottom Left', 
            'bottom_right': 'Bottom Right',
            'center_top': 'Center Top',
            'center_bottom': 'Center Bottom'
        }
    
    def get_style_presets(self) -> Dict[str, str]:
        """
        Get available style preset options.
        
        Returns:
            Dictionary mapping style keys to display names
        """
        return {
            'classic': 'Classic (White on Black)',
            'clean': 'Clean (Black on White)',
            'minimal': 'Minimal (No Background)'
        }