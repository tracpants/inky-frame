"""Shared fixtures: run the app against a temporary data directory."""

import importlib
import io
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def app_module(tmp_path, monkeypatch):
    """Import app.py fresh with DATA_DIR pointing at a temp directory."""
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    sys.modules.pop('app', None)
    module = importlib.import_module('app')
    module.app.config['TESTING'] = True
    yield module
    module.stop_event.set()
    sys.modules.pop('app', None)


@pytest.fixture
def client(app_module):
    return app_module.app.test_client()


def make_png(width=800, height=480, color=(30, 120, 200)):
    """Return PNG bytes of a solid image."""
    buf = io.BytesIO()
    Image.new('RGB', (width, height), color).save(buf, 'PNG')
    return buf.getvalue()


@pytest.fixture
def png_bytes():
    return make_png()


@pytest.fixture
def uploaded_photo(client, png_bytes):
    """Upload one photo and return its stored filename."""
    resp = client.post(
        '/api/photos/upload',
        data={'file': (io.BytesIO(png_bytes), 'holiday.png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()['name']
