# Inky Frame

A web-based photo frame controller for the Pimoroni Inky Impression 7.3" e-ink display on Raspberry Pi.

## Features

- **Web UI** - Upload and manage photos from any device on your network
- **Crop Tool** - Visual cropping with correct 800×480 aspect ratio
- **Auto-Cycling** - Automatically rotate through photos at configurable intervals
- **Orientation Support** - Landscape (800×480) or Portrait (480×800) modes
- **Docker Packaged** - Easy deployment and development

## Hardware Requirements

- Raspberry Pi 3B+ or newer (any 40-pin header model)
- Pimoroni Inky Impression 7.3" display
- SD card with Raspberry Pi OS (Bookworm or later recommended)

## Quick Start

### On Raspberry Pi

1. **Enable SPI and I2C:**
   ```bash
   sudo raspi-config nonint do_spi 0
   sudo raspi-config nonint do_i2c 0
   ```

2. **Add SPI overlay** (edit `/boot/firmware/config.txt`):
   ```
   dtoverlay=spi0-0cs
   ```

3. **Reboot:**
   ```bash
   sudo reboot
   ```

4. **Clone and run:**
   ```bash
   git clone <repo-url> inky-frame
   cd inky-frame
   docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d
   ```

5. **Access the UI:**
   Open `http://<pi-ip>:5000` in your browser

### For Development (without hardware)

```bash
docker compose up
```

The web UI will work without the display - you'll see "dev mode" messages when trying to update the display.

## Configuration

### Display Settings

| Setting | Description |
|---------|-------------|
| Auto-cycle | Enable/disable automatic photo rotation |
| Interval | Time between photo changes (min: 1 minute) |
| Orientation | Landscape (800×480) or Portrait (480×800) |

### Data Persistence

Photos and settings are stored in a Docker volume (`inky-data`). To backup:

```bash
docker run --rm -v inky-data:/data -v $(pwd):/backup alpine tar czf /backup/inky-backup.tar.gz /data
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET/POST | Get or update settings |
| `/api/photos` | GET | List all photos |
| `/api/photos/upload` | POST | Upload a new photo |
| `/api/photos/upload-cropped` | POST | Upload cropped image |
| `/api/photos/<n>` | DELETE | Delete a photo |
| `/api/display/<n>` | POST | Display a specific photo |
| `/photos/<n>` | GET | Serve photo file |

## Display Notes

- **Refresh time:** ~20-25 seconds per update
- **Colors:** 7 colors with automatic dithering
- **Temperature:** Best results between 15-35°C

## Troubleshooting

### "No EEPROM detected"
Ensure SPI and I2C are enabled and the display is properly connected.

### Display not updating
Check container logs: `docker logs inky-frame`

### Permission errors
The Pi container needs privileged access for GPIO. Ensure you're using the `docker-compose.pi.yml` override.

## Project Structure

```
inky-frame/
├── app.py                  # Flask application
├── templates/
│   └── index.html          # Web UI
├── Dockerfile              # Development build
├── Dockerfile.pi           # Raspberry Pi build
├── docker-compose.yml      # Base compose config
├── docker-compose.pi.yml   # Pi hardware override
├── requirements.txt        # Python dependencies
└── requirements-pi.txt     # Pi-specific dependencies
```

## License

MIT
