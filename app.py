"""
Inky Frame - Photo Frame Controller for Inky Impression 7.3"
Web UI for uploading, cropping, and cycling photos on e-ink display.
"""

import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Paths
DATA_DIR = Path(os.environ.get('DATA_DIR', '/app/data'))
PHOTOS_DIR = DATA_DIR / 'photos'
ORIGINALS_DIR = DATA_DIR / 'originals'
CONFIG_FILE = DATA_DIR / 'config.json'

# Display settings for Inky Impression 7.3"
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# Ensure directories exist
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)

# Global state
display_thread = None
stop_event = threading.Event()


def load_config():
    """Load configuration from file."""
    default_config = {
        'cycle_enabled': False,
        'cycle_interval': 3600,  # seconds (1 hour default)
        'current_photo': None,
        'orientation': 'landscape',  # landscape or portrait
        'photo_order': [],
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
    return default_config


def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_display_dimensions(orientation):
    """Get display dimensions based on orientation."""
    if orientation == 'portrait':
        return DISPLAY_HEIGHT, DISPLAY_WIDTH
    return DISPLAY_WIDTH, DISPLAY_HEIGHT


def get_photos():
    """Get list of all photos."""
    photos = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']:
        photos.extend(PHOTOS_DIR.glob(ext))
        photos.extend(PHOTOS_DIR.glob(ext.upper()))
    return sorted(photos, key=lambda x: x.stat().st_mtime, reverse=True)


def display_photo(photo_path):
    """Display a photo on the Inky Impression."""
    try:
        from inky.auto import auto
        
        inky_display = auto()
        
        img = Image.open(photo_path)
        img_width, img_height = img.size
        
        # Detect if image is portrait (taller than wide)
        is_portrait = img_height > img_width
        
        if is_portrait:
            # Rotate portrait image 90° CCW so it displays correctly
            # when the display is physically rotated to portrait orientation
            img = img.rotate(90, expand=True)
        
        # Now resize to fit display's native dimensions
        img = img.resize((inky_display.width, inky_display.height), Image.Resampling.LANCZOS)
        
        if hasattr(inky_display, 'set_image'):
            inky_display.set_image(img)
            inky_display.show()
            return True
    except ImportError:
        print("Inky library not available - running in dev mode")
        return False
    except Exception as e:
        print(f"Error displaying photo: {e}")
        return False
    return True


def cycle_photos():
    """Background thread to cycle through photos."""
    config = load_config()
    photo_index = 0
    
    while not stop_event.is_set():
        config = load_config()
        
        if not config.get('cycle_enabled'):
            time.sleep(1)
            continue
        
        photos = get_photos()
        if not photos:
            time.sleep(1)
            continue
        
        order = config.get('photo_order', [])
        if order:
            ordered_photos = []
            for name in order:
                for p in photos:
                    if p.name == name:
                        ordered_photos.append(p)
                        break
            for p in photos:
                if p not in ordered_photos:
                    ordered_photos.append(p)
            photos = ordered_photos
        
        if photo_index >= len(photos):
            photo_index = 0
        
        current_photo = photos[photo_index]
        config['current_photo'] = current_photo.name
        save_config(config)
        
        display_photo(current_photo)
        
        photo_index += 1
        
        interval = config.get('cycle_interval', 3600)
        stop_event.wait(timeout=interval)


def start_cycle_thread():
    """Start the photo cycling thread."""
    global display_thread
    if display_thread is None or not display_thread.is_alive():
        stop_event.clear()
        display_thread = threading.Thread(target=cycle_photos, daemon=True)
        display_thread.start()


start_cycle_thread()


@app.route('/')
def index():
    """Main page."""
    config = load_config()
    photos = get_photos()
    return render_template('index.html', 
                         config=config, 
                         photos=[p.name for p in photos],
                         display_width=DISPLAY_WIDTH,
                         display_height=DISPLAY_HEIGHT)


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update configuration."""
    if request.method == 'GET':
        return jsonify(load_config())
    
    config = load_config()
    data = request.json
    
    if 'cycle_enabled' in data:
        config['cycle_enabled'] = bool(data['cycle_enabled'])
    if 'cycle_interval' in data:
        config['cycle_interval'] = max(60, int(data['cycle_interval']))
    if 'orientation' in data:
        config['orientation'] = data['orientation']
    if 'photo_order' in data:
        config['photo_order'] = data['photo_order']
    
    save_config(config)
    return jsonify(config)


@app.route('/api/photos', methods=['GET'])
def api_photos():
    """List all photos."""
    photos = get_photos()
    return jsonify([{
        'name': p.name,
        'size': p.stat().st_size,
        'modified': datetime.fromtimestamp(p.stat().st_mtime).isoformat()
    } for p in photos])


@app.route('/api/photos/upload', methods=['POST'])
def api_upload():
    """Upload a new photo."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{name}_{timestamp}{ext}"
    
    # Save original to originals directory
    original_filepath = ORIGINALS_DIR / filename
    file.save(original_filepath)
    
    # Also save a copy to photos directory for immediate display
    display_filepath = PHOTOS_DIR / filename
    with open(original_filepath, 'rb') as src:
        with open(display_filepath, 'wb') as dst:
            dst.write(src.read())
    
    return jsonify({'name': filename, 'success': True})


@app.route('/api/photos/upload-cropped', methods=['POST'])
def api_upload_cropped():
    """Upload a cropped photo from the crop tool."""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    
    image_data = data['image']
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    image_bytes = base64.b64decode(image_data)
    img = Image.open(io.BytesIO(image_bytes))
    
    # Use original filename or create new one if cropping a fresh upload
    filename = data.get('filename', 'cropped')
    
    # If this is from an existing photo (re-cropping), use the same filename
    # If this is a new upload being cropped, generate timestamped name
    if data.get('is_recrop', False):
        # Re-cropping existing photo - use exact filename to overwrite
        final_filename = filename
    else:
        # New upload being cropped - generate timestamped name
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_filename = f"{secure_filename(name)}_{timestamp}.png"
    
    filepath = PHOTOS_DIR / final_filename
    img.save(filepath, 'PNG')
    
    return jsonify({'name': final_filename, 'success': True})


@app.route('/api/photos/<filename>', methods=['DELETE'])
def api_delete_photo(filename):
    """Delete a photo."""
    secure_name = secure_filename(filename)
    display_filepath = PHOTOS_DIR / secure_name
    original_filepath = ORIGINALS_DIR / secure_name
    
    deleted_any = False
    
    # Delete display version
    if display_filepath.exists():
        display_filepath.unlink()
        deleted_any = True
    
    # Delete original version  
    if original_filepath.exists():
        original_filepath.unlink()
        deleted_any = True
    
    if deleted_any:
        return jsonify({'success': True})
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/display/<filename>', methods=['POST'])
def api_display_photo(filename):
    """Display a specific photo immediately."""
    filepath = PHOTOS_DIR / secure_filename(filename)
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    
    config = load_config()
    config['current_photo'] = filename
    save_config(config)
    
    success = display_photo(filepath)
    return jsonify({'success': success, 'displayed': filename})


@app.route('/photos/<filename>')
def serve_photo(filename):
    """Serve a photo file."""
    return send_from_directory(PHOTOS_DIR, filename)


@app.route('/api/photos/original/<filename>')
def serve_original_photo(filename):
    """Serve an original photo file for editing."""
    return send_from_directory(ORIGINALS_DIR, filename)


@app.route('/api/preview/<filename>')
def api_preview(filename):
    """Get a preview thumbnail of a photo."""
    filepath = PHOTOS_DIR / secure_filename(filename)
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    
    img = Image.open(filepath)
    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    b64 = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({'thumbnail': f'data:image/png;base64,{b64}'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)