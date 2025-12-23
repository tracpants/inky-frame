# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Inky Frame is a web-based photo frame controller for the Pimoroni Inky Impression 7.3" e-ink display on Raspberry Pi. It provides a Flask web UI for uploading photos, visual cropping with correct aspect ratio, auto-cycling through photos, and immediate display control.

## Architecture

The application consists of:

- **app.py**: Main Flask application with REST API endpoints and background photo cycling
- **templates/index.html**: Single-page web UI with JavaScript for photo management and cropping
- **Docker setup**: Multi-stage deployment (dev vs Pi hardware)
- **Data persistence**: Docker volume at `/app/data` containing photos and config.json

### Key Components

- **Photo Management**: Upload, crop, delete, and serve photos from `/app/data/photos`
- **Configuration**: JSON-based settings in `/app/data/config.json` for cycling, orientation, and photo order
- **Display Control**: Background threading for auto-cycling with configurable intervals
- **Hardware Integration**: Conditional import of `inky.auto` library for e-ink display control

## Development Commands

### Development Environment
```bash
docker compose up
```
Runs without hardware dependencies - displays "dev mode" messages when attempting display updates.

### Raspberry Pi Deployment
```bash
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d
```
Requires hardware access with privileged mode for GPIO/SPI/I2C.

### Build for Pi Hardware
```bash
docker build --platform linux/arm64 -t inky-frame .
```

## API Architecture

REST endpoints follow `/api/` prefix:
- `/api/config` - GET/POST configuration management
- `/api/photos` - GET photo listing, DELETE for removal
- `/api/photos/upload` - POST file upload
- `/api/photos/upload-cropped` - POST base64 cropped images
- `/api/display/<filename>` - POST immediate display control
- `/photos/<filename>` - Static file serving

## Hardware Considerations

- Display refresh takes 20-25 seconds
- Requires SPI/I2C enabled on Pi (`raspi-config`)
- Portrait images auto-rotate 90° CCW for correct display when rotated
- GPIO access requires privileged Docker mode
- Dependencies split between `requirements.txt` (dev) and `requirements-pi.txt` (hardware)

## Configuration

Settings stored in JSON with defaults for cycle timing (3600s), orientation (landscape), and photo ordering. Background thread handles auto-cycling with configurable intervals (minimum 60 seconds).